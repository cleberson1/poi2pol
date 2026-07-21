import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import tempfile
import os
import zipfile
import shutil

# Configuração da página
st.set_page_config(page_title="POI2POL & Vertex Extractor", layout="wide")

# Título do Aplicativo (Alterado conforme solicitado)
st.title("🗺️ POI2POL — Conversor e Extrator Geoespacial")

# Criação das Abas
tab1, tab2, tab3 = st.tabs(["📍 CSV para Polígono", "📐 Extrair Vértices de Shapefile", "🌐 Conversor Graus Decimais → UTM"])

# --- ABA 1: POI2POL (Funcionalidade Original) ---
with tab1:
    st.header("Conversor de Pontos para Polígono")
    with st.expander("📋 INSTRUÇÕES - Como preparar seu CSV", expanded=False):
        st.markdown("""
        ### Requisitos do Arquivo CSV:
        1. **Colunas Obrigatórias:** `ponto`, `zona`, `x`, `y`, `locacao`.
        2. **Agrupamento:** O sistema criará um polígono para cada valor na coluna **locacao**.
        3. **Formatação:** Use **ponto (.)** como separador decimal.
        """)
        example_data = {
            'ponto': ['P1', 'P2', 'P3', 'PA', 'PB'],
            'zona': ['23S', '23S', '23S', '23S', '23S'],
            'x': [566865.53, 566882.96, 566971.02, 562732.49, 562706.82],
            'y': [9745153.65, 9745268.58, 9745343.86, 9740334.26, 9740920.31],
            'locacao': ['Sítio A', 'Sítio A', 'Sítio A', 'Área B', 'Área B']
        }
        st.table(pd.DataFrame(example_data))

    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_csv = st.file_uploader("Selecione seu arquivo CSV", type=["csv"], key="csv_upload")
    with col2:
        datum_choice = st.selectbox("Datum:", ["WGS 84", "SIRGAS 2000"], key="datum1")
        target_crs = "EPSG:32723" if datum_choice == "WGS 84" else "EPSG:31983"

    if uploaded_csv:
        try:
            content = uploaded_csv.getvalue().decode('utf-8')
            separator = ';' if content.count(';') > content.count(',') else ','
            uploaded_csv.seek(0)
            df = pd.read_csv(uploaded_csv, sep=separator)
            
            required_cols = {'ponto', 'zona', 'x', 'y', 'locacao'}
            if not required_cols.issubset(df.columns):
                st.error(f"Faltam colunas: {required_cols - set(df.columns)}")
            else:
                polygons, locacao_names, valid_status = [], [], []
                for locacao, group in df.groupby('locacao'):
                    if len(group) < 3:
                        st.warning(f"⚠️ '{locacao}' ignorado: menos de 3 pontos.")
                        continue
                    poly = Polygon(list(zip(group['x'], group['y'])))
                    polygons.append(poly)
                    locacao_names.append(locacao)
                    valid_status.append("Válida" if poly.is_valid else "Inválida (Auto-interseção)")

                if polygons:
                    gdf = gpd.GeoDataFrame({'locacao': locacao_names, 'status_geo': valid_status, 'geometry': polygons}, crs=target_crs)
                    st.dataframe(gdf[['locacao', 'status_geo']], use_container_width=True)

                    with tempfile.TemporaryDirectory() as tmp_dir:
                        shp_name = "poi2pol_output"
                        shp_path = os.path.join(tmp_dir, f"{shp_name}.shp")
                        gdf.to_file(shp_path)
                        zip_path = os.path.join(tmp_dir, "export.zip")
                        with zipfile.ZipFile(zip_path, 'w') as zipf:
                            for ext in ['.shp', '.shx', '.dbf', '.prj']:
                                zipf.write(os.path.join(tmp_dir, f"{shp_name}{ext}"), arcname=f"{shp_name}{ext}")
                        
                        with open(zip_path, "rb") as f:
                            st.download_button("📥 Baixar Shapefile (ZIP)", f, "poi2pol_shapes.zip", "application/zip")
        except Exception as e:
            st.error(f"Erro no processamento: {e}")

# --- ABA 2: EXTRAIR VÉRTICES (Conversão.py) ---
with tab2:
    st.header("Extrator de Vértices de Shapefile")
    st.info("Envie um arquivo **.zip** contendo todos os arquivos do Shapefile (.shp, .shx, .dbf, .prj).")
    
    uploaded_zip = st.file_uploader("Selecione o ZIP do Shapefile", type=["zip"], key="zip_upload")
    
    if uploaded_zip:
        try:
            with tempfile.TemporaryDirectory() as tmp_extract_dir:
                # Salvar e extrair o ZIP
                zip_path = os.path.join(tmp_extract_dir, "upload.zip")
                with open(zip_path, "wb") as f:
                    f.write(uploaded_zip.getbuffer())
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmp_extract_dir)
                
                # Localizar o arquivo .shp
                shp_files = [f for f in os.listdir(tmp_extract_dir) if f.endswith('.shp')]
                
                if not shp_files:
                    st.error("Nenhum arquivo .shp encontrado dentro do ZIP.")
                else:
                    shp_path = os.path.join(tmp_extract_dir, shp_files[0])
                    gdf_in = gpd.read_file(shp_path)
                    
                    # Lógica do conversao.py
                    gdf_exploded = gdf_in.explode(index_parts=False)
                    vertices = []

                    for index, row in gdf_exploded.iterrows():
                        if row.geometry.geom_type == 'Polygon':
                            coords = list(row.geometry.exterior.coords)
                        else:
                            coords = list(row.geometry.coords)

                        for c in coords:
                            x, y, *extras = c
                            z = extras[0] if extras else None
                            
                            vertex_data = {
                                'original_id': index,
                                'x': x,
                                'y': y,
                                'z': z
                            }
                            # Adiciona outros atributos (exceto a geometria)
                            for k, v in row.items():
                                if k != 'geometry':
                                    vertex_data[k] = v
                            vertices.append(vertex_data)

                    df_vertices = pd.DataFrame(vertices)
                    
                    st.subheader("Vértices Extraídos")
                    st.dataframe(df_vertices, use_container_width=True)
                    
                    # Download do CSV
                    csv_data = df_vertices.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Baixar Tabela de Vértices (CSV)",
                        data=csv_data,
                        file_name="vertices_extraidos.csv",
                        mime="text/csv"
                    )
        except Exception as e:
            st.error(f"Erro ao extrair vértices: {e}")
            
# --- ABA 3: CONVERSOR GRAUS DECIMAIS → UTM ---
with tab3:
    st.header("Conversor de Coordenadas Geográficas para UTM")
    st.info("Insira as coordenadas em graus decimais para converter para o sistema UTM.")
    
    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat = st.number_input("Latitude (graus decimais):", value=-23.5505, format="%.6f", key="lat_input")
        st.caption("Exemplo: -23.5505 (Sul) ou 23.5505 (Norte)")
    with col_lon:
        lon = st.number_input("Longitude (graus decimais):", value=-46.6333, format="%.6f", key="lon_input")
        st.caption("Exemplo: -46.6333 (Oeste) ou 46.6333 (Leste)")
    
    datum_choice_utm = st.selectbox("Datum:", ["WGS 84", "SIRGAS 2000"], key="datum_utm")
    
    if st.button("🔄 Converter para UTM", key="convert_utm"):
        try:
            import pyproj
            
            # Definir o CRS de origem (WGS 84)
            crs_geog = "EPSG:4326"  # WGS 84
            
            # Determinar o fuso UTM baseado na longitude
            utm_zone = int((lon + 180) / 6) + 1
            hemisphere = "S" if lat < 0 else "N"
            
            # Definir o CRS de destino baseado no datum escolhido
            if datum_choice_utm == "WGS 84":
                crs_utm = f"EPSG:327{utm_zone:02d}" if hemisphere == "S" else f"EPSG:326{utm_zone:02d}"
            else:  # SIRGAS 2000
                crs_utm = f"EPSG:3198{utm_zone:02d}" if hemisphere == "S" else f"EPSG:3197{utm_zone:02d}"
            
            # Criar transformador
            transformer = pyproj.Transformer.from_crs(crs_geog, crs_utm, always_xy=True)
            
            # Converter
            x_utm, y_utm = transformer.transform(lon, lat)
            
            # Exibir resultados
            st.success(f"✅ Conversão realizada com sucesso!")
            
            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                st.metric("📍 Fuso UTM", f"{utm_zone}{hemisphere}")
            with col_res2:
                st.metric("📌 Coordenada X (Easting)", f"{x_utm:.2f} m")
            with col_res3:
                st.metric("📌 Coordenada Y (Northing)", f"{y_utm:.2f} m")
            
            st.info(f"🔍 Sistema de referência utilizado: {crs_utm}")
            
            # Opção de copiar coordenadas
            st.code(f"X: {x_utm:.2f}\nY: {y_utm:.2f}\nFuso: {utm_zone}{hemisphere}", language="text")
            
        except Exception as e:
            st.error(f"Erro na conversão: {e}. Verifique se os valores são válidos.")


# Rodapé
st.markdown("<br><hr><div style='text-align: center; color: gray;'>Desenvolvido por <b>Cleberson Carlos</b> para a galera que sofre no IPHAN</div>", unsafe_allow_html=True)
