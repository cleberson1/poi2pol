import os
import tempfile
import zipfile

import geopandas as gpd
import pandas as pd
import streamlit as st


def _achar_shp(pasta):
    for raiz, _, arquivos in os.walk(pasta):
        for nome in arquivos:
            if nome.lower().endswith(".shp"):
                return os.path.join(raiz, nome)
    return None


def render():
    st.header("Extrator de Vértices de Shapefile")
    st.info("Envie um arquivo **.zip** contendo todos os arquivos do Shapefile (.shp, .shx, .dbf, .prj).")

    uploaded_zip = st.file_uploader("Selecione o ZIP do Shapefile", type=["zip"], key="zip_upload")
    if not uploaded_zip:
        return

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = os.path.join(tmp_dir, "upload.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.getbuffer())
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)

            shp_path = _achar_shp(tmp_dir)
            if not shp_path:
                st.error("Nenhum arquivo .shp encontrado dentro do ZIP.")
                return

            gdf_in = gpd.read_file(shp_path)

        gdf_exploded = gdf_in.explode(index_parts=False)
        vertices = []
        for index, row in gdf_exploded.iterrows():
            if row.geometry is None or row.geometry.is_empty:
                continue
            if row.geometry.geom_type == 'Polygon':
                coords = list(row.geometry.exterior.coords)
            else:
                coords = list(row.geometry.coords)

            for c in coords:
                x, y, *extras = c
                z = extras[0] if extras else None
                vertex_data = {'original_id': index, 'x': x, 'y': y, 'z': z}
                for k, v in row.items():
                    if k != 'geometry':
                        vertex_data[k] = v
                vertices.append(vertex_data)

        df_vertices = pd.DataFrame(vertices)

        st.subheader("Vértices Extraídos")
        st.dataframe(df_vertices, use_container_width=True)

        st.download_button(
            label="📥 Baixar Tabela de Vértices (CSV)",
            data=df_vertices.to_csv(index=False).encode('utf-8'),
            file_name="vertices_extraidos.csv",
            mime="text/csv",
        )
    except Exception as e:
        st.error(f"Erro ao extrair vértices: {e}")
