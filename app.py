import streamlit as st

from abas import (
    csv_para_poligono,
    extrair_vertices,
    conversor_coordenadas,
    kml_para_shp,
    calculadora_datas,
)

st.set_page_config(page_title="POI2POL & Vertex Extractor", layout="wide")

st.title("🗺️ POI2POL — Conversor e Extrator Geoespacial")

# Para adicionar/remover uma aba: crie/apague o arquivo em abas/ e edite esta lista.
ABAS = [
    ("📍 CSV para Polígono", csv_para_poligono),
    ("📐 Extrair Vértices de Shapefile", extrair_vertices),
    ("🌐 Conversor de Coordenadas", conversor_coordenadas),
    ("🧭 KML/KMZ → Shapefile", kml_para_shp),
    ("📅 Calculadora de Datas", calculadora_datas),
]

for tab, (_, modulo) in zip(st.tabs([nome for nome, _ in ABAS]), ABAS):
    with tab:
        modulo.render()

st.markdown(
    "<br><hr><div style='text-align: center; color: gray;'>Desenvolvido por "
    "<b>Cleberson Carlos</b> para a galera que sofre no IPHAN</div>",
    unsafe_allow_html=True,
)
