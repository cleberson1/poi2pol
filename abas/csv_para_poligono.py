import os
import tempfile
import zipfile

import geopandas as gpd
import pandas as pd
import streamlit as st
from shapely.geometry import Polygon


def render():
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
            'locacao': ['Sítio A', 'Sítio A', 'Sítio A', 'Área B', 'Área B'],
        }
        st.table(pd.DataFrame(example_data))

    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_csv = st.file_uploader("Selecione seu arquivo CSV", type=["csv"], key="csv_upload")
    with col2:
        datum_choice = st.selectbox("Datum:", ["WGS 84", "SIRGAS 2000"], key="datum1")
        target_crs = "EPSG:32723" if datum_choice == "WGS 84" else "EPSG:31983"

    if not uploaded_csv:
        return

    try:
        content = uploaded_csv.getvalue().decode('utf-8')
        separator = ';' if content.count(';') > content.count(',') else ','
        uploaded_csv.seek(0)
        df = pd.read_csv(uploaded_csv, sep=separator)

        required_cols = {'ponto', 'zona', 'x', 'y', 'locacao'}
        if not required_cols.issubset(df.columns):
            st.error(f"Faltam colunas: {required_cols - set(df.columns)}")
            return

        polygons, locacao_names, valid_status = [], [], []
        for locacao, group in df.groupby('locacao'):
            if len(group) < 3:
                st.warning(f"⚠️ '{locacao}' ignorado: menos de 3 pontos.")
                continue
            poly = Polygon(list(zip(group['x'], group['y'])))
            polygons.append(poly)
            locacao_names.append(locacao)
            valid_status.append("Válida" if poly.is_valid else "Inválida (Auto-interseção)")

        if not polygons:
            return

        gdf = gpd.GeoDataFrame(
            {'locacao': locacao_names, 'status_geo': valid_status, 'geometry': polygons},
            crs=target_crs,
        )
        st.dataframe(gdf[['locacao', 'status_geo']], use_container_width=True)

        with tempfile.TemporaryDirectory() as tmp_dir:
            shp_name = "poi2pol_output"
            gdf.to_file(os.path.join(tmp_dir, f"{shp_name}.shp"))
            zip_path = os.path.join(tmp_dir, "export.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for ext in ['.shp', '.shx', '.dbf', '.prj']:
                    zipf.write(os.path.join(tmp_dir, f"{shp_name}{ext}"), arcname=f"{shp_name}{ext}")
            with open(zip_path, "rb") as f:
                zip_bytes = f.read()

        st.download_button("📥 Baixar Shapefile (ZIP)", zip_bytes, "poi2pol_shapes.zip", "application/zip")
    except Exception as e:
        st.error(f"Erro no processamento: {e}")
