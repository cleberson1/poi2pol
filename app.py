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

# 1. Instruções Atualizadas
with st.expander("📋 INSTRUÇÕES - Como preparar seu CSV", expanded=True):
    st.markdown("""
    ### Requisitos do Arquivo CSV:
    1. **Colunas Obrigatórias:** `ponto`, `zona`, `x`, `y`, `locacao`.
    2. **Agrupamento:** O sistema criará um polígono para cada valor diferente na coluna **locacao**.
    3. **Software de Planilha:** Você pode usar Excel, LibreOffice ou Google Sheets, mas deve clicar em **"Salvar como"** e escolher o formato **CSV (Separado por vírgulas ou ponto e vírgula)**.
    4. **Formatação Numérica:** Use **ponto (.)** como separador decimal (Ex: 566865.53).
    
    **Exemplo de organização:**
    """)
    example_df = pd.DataFrame({
        'ponto': ['P1', 'P2', 'P3', 'PA', 'PB'],
        'zona': ['23S', '23S', '23S', '23S', '23S'],
        'x': [566865.53, 566882.96, 566971.02, 562732.49, 562706.82],
        'y': [9745153.65, 9745268.58, 9745343.86, 9740334.26, 9740920.31],
        'locacao': ['Sítio 1', 'Sítio 1', 'Sítio 1', 'Área B', 'Área B']
    })
    st.table(example_df)
    st.info("💡 O sistema aceita automaticamente arquivos separados por vírgula (,) ou ponto e vírgula (;).")

# 2. Configurações de Geoprocessamento
st.sidebar.header("Configurações de Projeção")
crs_choice = st.sidebar.selectbox(
    "Escolha o Sistema de Coordenadas (Datum):",
    ["WGS 84 / UTM zone 23S (EPSG:32723)", "SIRGAS 2000 / UTM zone 23S (EPSG:31983)"]
)
target_crs = "EPSG:32723" if "WGS 84" in crs_choice else "EPSG:31983"

# 3. Área de Upload
uploaded_file = st.file_uploader("Selecione seu arquivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Tenta detectar o separador (vírgula ou ponto e vírgula)
        content = uploaded_file.getvalue().decode('utf-8')
        separator = ';' if content.count(';') > content.count(',') else ','
        uploaded_file.seek(0) # Reseta o ponteiro do arquivo
        
        df = pd.read_csv(uploaded_file, sep=separator)
        
        # Validação de colunas
        required_cols = {'ponto', 'zona', 'x', 'y', 'locacao'}
        if not required_cols.issubset(df.columns):
            st.error(f"Erro: O CSV deve conter exatamente as colunas: {', '.join(required_cols)}")
        else:
            st.success(f"Arquivo lido com sucesso (Separador detectado: '{separator}')")
            
            # Processamento
            polygons = []
            locacao_names = []
            valid_status = []
            
            grouped = df.groupby('locacao')
            
            for locacao, group in grouped:
                if len(group) < 3:
                    st.warning(f"⚠️ '{locacao}' ignorado: Necessário pelo menos 3 pontos.")
                    continue
                
                # Criar polígono
                points = list(zip(group['x'], group['y']))
                poly = Polygon(points)
                
                # Validação de Geometria
                is_valid = poly.is_valid
                
                polygons.append(poly)
                locacao_names.append(locacao)
                valid_status.append("Válida" if is_valid else "Inválida (Auto-interseção)")

            if polygons:
                # Criar GeoDataFrame
                gdf = gpd.GeoDataFrame({
                    'locacao': locacao_names, 
                    'status_geo': valid_status,
                    'geometry': polygons
                }, crs=target_crs)
                
                st.subheader("Resumo do Processamento")
                st.dataframe(gdf[['locacao', 'status_geo']])

                # Verificação de erros críticos
                if "Inválida (Auto-interseção)" in valid_status:
                    st.error("🚨 Detectamos geometrias inválidas. O Shapefile será gerado, mas pode apresentar erros em softwares GIS.")

                # 4. Exportação
                with tempfile.TemporaryDirectory() as tmp_dir:
                    base_name = "export_poi2pol"
                    shp_path = os.path.join(tmp_dir, f"{base_name}.shp")
                    gdf.to_file(shp_path)
                    
                    zip_path = os.path.join(tmp_dir, "shapefile.zip")
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for ext in ['.shp', '.shx', '.dbf', '.prj']:
                            f_path = os.path.join(tmp_dir, f"{base_name}{ext}")
                            if os.path.exists(f_path):
                                zipf.write(f_path, arcname=f"{base_name}{ext}")

                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="📥 Baixar Shapefile (ZIP)",
                            data=f,
                            file_name=f"poi2pol_{locacao_names[0]}.zip" if len(locacao_names)==1 else "poi2pol_multiplo.zip",
                            mime="application/zip"
                        )
            else:
                st.error("Nenhum polígono pôde ser formado.")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
