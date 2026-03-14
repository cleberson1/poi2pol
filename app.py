import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import tempfile
import os
import zipfile

# Configuração da página
st.set_page_config(page_title="POI2POL - Conversor CSV", layout="wide")

# Título do Aplicativo
st.title("🗺️ POI2POL — Conversor CSV ➔ Shapefile")

# 1. Seção de Instruções
with st.expander("📋 INSTRUÇÕES - Como preparar seu CSV", expanded=True):
    st.markdown("""
    ### Requisitos do Arquivo CSV:
    1. **Colunas Obrigatórias:** `ponto`, `zona`, `x`, `y`, `locacao`.
    2. **Agrupamento:** O sistema criará um polígono para cada valor diferente na coluna **locacao**.
    3. **Software de Planilha:** Use o software de sua preferência (Excel, Sheets, etc.), mas salve obrigatoriamente como **CSV (Separado por vírgulas ou ponto e vírgula)**.
    4. **Formatação Numérica:** Use **ponto (.)** como separador decimal.
    """)
    
    example_data = {
        'ponto': ['P1', 'P2', 'P3', 'PA', 'PB'],
        'zona': ['23S', '23S', '23S', '23S', '23S'],
        'x': [566865.53, 566882.96, 566971.02, 562732.49, 562706.82],
        'y': [9745153.65, 9745268.58, 9745343.86, 9740334.26, 9740920.31],
        'locacao': ['Sítio Exemplo A', 'Sítio Exemplo A', 'Sítio Exemplo A', 'Área Exemplo B', 'Área Exemplo B']
    }
    st.table(pd.DataFrame(example_data))
    st.info("💡 O sistema identifica automaticamente o separador (vírgula ou ponto e vírgula).")

st.divider()

# 2. Configuração e Upload
col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader("Selecione seu arquivo CSV", type=["csv"])

with col2:
    datum_choice = st.selectbox(
        "Escolha o Datum (Sistema de Referência):",
        ["WGS 84", "SIRGAS 2000"]
    )
    target_crs = "EPSG:32723" if datum_choice == "WGS 84" else "EPSG:31983"

# 3. Processamento
if uploaded_file is not None:
    try:
        content = uploaded_file.getvalue().decode('utf-8')
        separator = ';' if content.count(';') > content.count(',') else ','
        uploaded_file.seek(0)
        
        df = pd.read_csv(uploaded_file, sep=separator)
        
        required_cols = {'ponto', 'zona', 'x', 'y', 'locacao'}
        if not required_cols.issubset(df.columns):
            st.error(f"Erro: O CSV deve conter: {', '.join(required_cols)}")
        else:
            st.success(f"Arquivo lido com sucesso (Separador: '{separator}')")
            
            polygons, locacao_names, valid_status = [], [], []
            
            for locacao, group in df.groupby('locacao'):
                if len(group) < 3:
                    st.warning(f"⚠️ '{locacao}' ignorado: menos de 3 pontos.")
                    continue
                
                points = list(zip(group['x'], group['y']))
                poly = Polygon(points)
                is_valid = poly.is_valid
                
                polygons.append(poly)
                locacao_names.append(locacao)
                valid_status.append("Válida" if is_valid else "Inválida (Auto-interseção)")

            if polygons:
                gdf = gpd.GeoDataFrame({
                    'locacao': locacao_names, 
                    'status_geo': valid_status,
                    'geometry': polygons
                }, crs=target_crs)
                
                st.subheader("Análise das Geometrias")
                st.dataframe(gdf[['locacao', 'status_geo']], use_container_width=True)

                if "Inválida (Auto-interseção)" in valid_status:
                    st.warning("🚨 Geometrias inválidas detectadas. Verifique a ordem dos pontos.")

                with tempfile.TemporaryDirectory() as tmp_dir:
                    base_name = "poi2pol_output"
                    shp_path = os.path.join(tmp_dir, f"{base_name}.shp")
                    gdf.to_file(shp_path)
                    
                    zip_path = os.path.join(tmp_dir, "export.zip")
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for ext in ['.shp', '.shx', '.dbf', '.prj']:
                            f_path = os.path.join(tmp_dir, f"{base_name}{ext}")
                            if os.path.exists(f_path):
                                zipf.write(f_path, arcname=f"{base_name}{ext}")

                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="📥 Baixar Shapefile (ZIP)",
                            data=f,
                            file_name="poi2pol_shapes.zip",
                            mime="application/zip"
                        )
            else:
                st.error("Dados insuficientes para gerar polígonos.")
    except Exception as e:
        st.error(f"Erro: {e}")

# 4. Rodapé Personalizado
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Desenvolvido por <b>Cleberson Carlos</b> para a galera que sofre no IPHAN"
    "</div>", 
    unsafe_allow_html=True
)
