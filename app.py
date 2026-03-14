import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import tempfile
import os
import zipfile
import shutil

# Configuração da página
st.set_page_config(page_title="poi2pol - Conversor CSV para Shapefile", layout="wide")

# Título do Aplicativo
st.title("📍 poi2pol — Conversor CSV ➔ Shapefile (Polígonos)")

# 1. Instruções (Expander aberto por padrão)
with st.expander("📋 INSTRUÇÕES - Como preparar seu CSV", expanded=True):
    st.markdown("""
    ### Requisitos do Arquivo CSV:
    1. **Colunas Obrigatórias:** `nome`, `x`, `y`.
    2. **Identificador:** Cada polígono é agrupado pelo valor da coluna **nome**.
    3. **Coordenadas:** Use o sistema **WGS 84 / UTM zone 23S (EPSG:32723)**.
    4. **Formatação:** Use **ponto (.)** como separador decimal. Não use vírgulas em números.
    5. **Ordem:** Os pontos devem estar na ordem sequencial (horário ou anti-horário).
    
    **Exemplo de formato:**
    """)
    example_df = pd.DataFrame({
        'nome': ['Sítio Peru', 'Sítio Peru', 'Sítio Peru', 'Sítio Pepital', 'Sítio Pepital'],
        'x': [566865.53, 566882.96, 566971.02, 562732.49, 562706.82],
        'y': [9745153.65, 9745268.58, 9745343.86, 9740334.26, 9740920.31]
    })
    st.table(example_df)
    st.info("💡 O sistema fecha automaticamente o polígono conectando o último ponto ao primeiro.")

# 2. Área de Upload
uploaded_file = st.file_uploader("Arraste ou selecione seu arquivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        
        # Validação básica de colunas
        required_cols = {'nome', 'x', 'y'}
        if not required_cols.issubset(df.columns):
            st.error(f"Erro: O CSV deve conter as colunas: {', '.join(required_cols)}")
        else:
            st.success("Arquivo carregado com sucesso!")
            st.subheader("Preview dos Dados")
            st.dataframe(df.head())

            # 3. Processamento
            polygons = []
            names = []
            
            # Agrupamento por nome
            grouped = df.groupby('nome')
            
            valid_processing = True
            for name, group in grouped:
                if len(group) < 3:
                    st.warning(f"Atenção: O polígono '{name}' possui menos de 3 pontos e será ignorado.")
                    continue
                
                # Criar lista de tuplas (x, y)
                points = list(zip(group['x'], group['y']))
                # Criar polígono (Shapely fecha automaticamente)
                poly = Polygon(points)
                
                polygons.append(poly)
                names.append(name)

            if len(polygons) > 0:
                # Criar GeoDataFrame
                gdf = gpd.GeoDataFrame({'nome': names, 'geometry': polygons}, crs="EPSG:32723")
                
                st.info(f"📊 Processamento concluído: {len(polygons)} polígono(s) gerado(s).")

                # 4. Preparação do Download (ZIP)
                with tempfile.TemporaryDirectory() as tmp_dir:
                    base_filename = "poligonos_gerados"
                    shp_path = os.path.join(tmp_dir, f"{base_filename}.shp")
                    
                    # Salvar shapefile (geopandas gera shp, shx, dbf, prj)
                    gdf.to_file(shp_path)
                    
                    # Criar ZIP
                    zip_path = os.path.join(tmp_dir, "shapefile_export.zip")
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for ext in ['.shp', '.shx', '.dbf', '.prj']:
                            file_to_zip = os.path.join(tmp_dir, f"{base_filename}{ext}")
                            if os.path.exists(file_to_zip):
                                zipf.write(file_to_zip, arcname=f"{base_filename}{ext}")

                    # Botão de Download
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="📥 Download ZIP com Shapefile",
                            data=f,
                            file_name="poi2pol_export.zip",
                            mime="application/zip"
                        )
            else:
                st.error("Nenhum polígono válido pôde ser criado. Verifique a quantidade de pontos por área.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
