import io
import os
import tempfile
import zipfile

import geopandas as gpd
import pandas as pd
import streamlit as st

from .utils_crs import crs_geografico, crs_utm, fuso_utm

SAIDAS = [
    "WGS 84 (graus decimais)",
    "SIRGAS 2000 (graus decimais)",
    "WGS 84 UTM (fuso automático)",
    "SIRGAS 2000 UTM (fuso automático)",
]

TIPOS = {"Point": "pontos", "LineString": "linhas", "Polygon": "poligonos"}


def _achar_kml(pasta):
    candidatos = []
    for raiz, _, arquivos in os.walk(pasta):
        for nome in arquivos:
            if nome.lower().endswith(".kml"):
                candidatos.append(os.path.join(raiz, nome))
    candidatos.sort(key=lambda p: (os.path.basename(p).lower() != "doc.kml", p))
    return candidatos[0] if candidatos else None


def _listar_camadas(caminho):
    try:
        import pyogrio
        return [c[0] for c in pyogrio.list_layers(caminho)]
    except Exception:
        try:
            import fiona
            return fiona.listlayers(caminho)
        except Exception:
            return [None]


def _ler_kml(caminho):
    quadros = []
    for camada in _listar_camadas(caminho):
        try:
            g = gpd.read_file(caminho, layer=camada) if camada else gpd.read_file(caminho)
        except Exception:
            continue
        if g.empty:
            continue
        g["camada"] = camada
        quadros.append(g)
    if not quadros:
        return None
    gdf = gpd.GeoDataFrame(pd.concat(quadros, ignore_index=True), geometry="geometry")
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    return gdf[~(gdf.geometry.isna() | gdf.geometry.is_empty)].copy()


def _preparar(gdf):
    # GeometryCollection não existe em Shapefile: separa em partes simples
    gc = gdf.geom_type == "GeometryCollection"
    if gc.any():
        gdf = pd.concat([gdf[~gc], gdf[gc].explode(index_parts=False)], ignore_index=True)
        gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs=gdf.crs)
    # Shapefile não aceita datetime e colunas vazias só atrapalham
    for col in gdf.columns:
        if col == "geometry":
            continue
        if pd.api.types.is_datetime64_any_dtype(gdf[col]):
            gdf[col] = gdf[col].astype(str)
    vazias = [c for c in gdf.columns if c != "geometry" and gdf[c].isna().all()]
    return gdf.drop(columns=vazias)


def _reprojetar(gdf, saida):
    datum = "SIRGAS 2000" if saida.startswith("SIRGAS") else "WGS 84"
    if "UTM" not in saida:
        return gdf.to_crs(crs_geografico(datum)), None

    geo = gdf.to_crs(crs_geografico(datum))
    minx, miny, maxx, maxy = geo.total_bounds
    zona = fuso_utm((minx + maxx) / 2)
    hemisferio = "S" if (miny + maxy) / 2 < 0 else "N"
    aviso = None
    if fuso_utm(minx) != fuso_utm(maxx):
        aviso = (f"Os dados cruzam mais de um fuso UTM ({fuso_utm(minx)} a {fuso_utm(maxx)}). "
                 f"Foi usado o fuso central {zona}{hemisferio}; distorções nas bordas são esperadas.")
    return gdf.to_crs(crs_utm(zona, hemisferio, datum)), aviso


def _gerar_zip(gdf, base):
    grupos = {}
    for tipo, sufixo in TIPOS.items():
        mascara = gdf.geom_type.isin([tipo, f"Multi{tipo}"])
        if mascara.any():
            grupos[sufixo] = gdf[mascara]

    buffer = io.BytesIO()
    with tempfile.TemporaryDirectory() as tmp_dir, zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for sufixo, parte in grupos.items():
            nome = f"{base}_{sufixo}"
            parte.to_file(os.path.join(tmp_dir, f"{nome}.shp"), encoding="utf-8")
            for arq in os.listdir(tmp_dir):
                if arq.startswith(nome + "."):
                    zf.write(os.path.join(tmp_dir, arq), arcname=arq)
    return buffer.getvalue(), {k: len(v) for k, v in grupos.items()}


def render():
    st.header("Conversor de KML/KMZ para Shapefile")
    st.info(
        "Envie um arquivo **.kml** ou **.kmz**. Como o Shapefile aceita só um tipo de geometria por arquivo, "
        "o resultado vem em um ZIP com um Shapefile para cada tipo encontrado (pontos, linhas e/ou polígonos)."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        arquivo = st.file_uploader("Selecione o arquivo KML ou KMZ", type=["kml", "kmz"], key="kml_upload")
    with col2:
        saida = st.selectbox("Sistema de coordenadas de saída:", SAIDAS, key="kml_saida")

    if not arquivo:
        return

    try:
        base = os.path.splitext(arquivo.name)[0]
        with tempfile.TemporaryDirectory() as tmp_dir:
            if arquivo.name.lower().endswith(".kmz"):
                with zipfile.ZipFile(io.BytesIO(arquivo.getvalue())) as z:
                    z.extractall(tmp_dir)
                caminho = _achar_kml(tmp_dir)
                if not caminho:
                    st.error("Nenhum arquivo .kml encontrado dentro do KMZ.")
                    return
            else:
                caminho = os.path.join(tmp_dir, "entrada.kml")
                with open(caminho, "wb") as f:
                    f.write(arquivo.getvalue())
            gdf = _ler_kml(caminho)

        if gdf is None or gdf.empty:
            st.error("Nenhuma geometria encontrada no arquivo.")
            return

        gdf = _preparar(gdf)
        gdf, aviso = _reprojetar(gdf, saida)
        if aviso:
            st.warning(aviso)

        zip_bytes, contagem = _gerar_zip(gdf, base)
        if not contagem:
            st.error("Nenhuma geometria compatível (ponto, linha ou polígono) foi encontrada.")
            return

        st.success("✅ Conversão concluída: " + ", ".join(f"{n} {tipo}" for tipo, n in contagem.items()))
        st.caption(f"CRS de saída: {gdf.crs.name if gdf.crs else 'indefinido'}. "
                   "Nomes de campos são limitados a 10 caracteres pelo formato Shapefile.")
        st.dataframe(gdf.drop(columns="geometry"), use_container_width=True)

        st.download_button("📥 Baixar Shapefile(s) (ZIP)", zip_bytes, f"{base}_shp.zip", "application/zip")
    except Exception as e:
        st.error(f"Erro na conversão: {e}")
