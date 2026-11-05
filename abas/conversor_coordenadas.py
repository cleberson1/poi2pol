import pyproj
import streamlit as st

from .utils_crs import crs_geografico, crs_utm, fuso_utm


def _inverter():
    st.session_state["utm_inverso"] = not st.session_state.get("utm_inverso", False)


def _graus_para_utm(datum):
    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat = st.number_input("Latitude (graus decimais):", value=-23.5505, format="%.6f", key="lat_input")
        st.caption("Exemplo: -23.5505 (Sul) ou 23.5505 (Norte)")
    with col_lon:
        lon = st.number_input("Longitude (graus decimais):", value=-46.6333, format="%.6f", key="lon_input")
        st.caption("Exemplo: -46.6333 (Oeste) ou 46.6333 (Leste)")

    if not st.button("🔄 Converter para UTM", key="convert_utm"):
        return

    try:
        if not -80 <= lat <= 84:
            raise ValueError("a latitude deve estar entre -80 e 84 para UTM")
        if not -180 <= lon <= 180:
            raise ValueError("a longitude deve estar entre -180 e 180")

        zona = fuso_utm(lon)
        hemisferio = "S" if lat < 0 else "N"
        destino = crs_utm(zona, hemisferio, datum)
        transformer = pyproj.Transformer.from_crs(crs_geografico(datum), destino, always_xy=True)
        x, y = transformer.transform(lon, lat)

        st.success("✅ Conversão realizada com sucesso!")
        c1, c2, c3 = st.columns(3)
        c1.metric("📍 Fuso UTM", f"{zona}{hemisferio}")
        c2.metric("📌 Coordenada X (Easting)", f"{x:.2f} m")
        c3.metric("📌 Coordenada Y (Northing)", f"{y:.2f} m")
        st.info(f"🔍 Sistema de referência utilizado: {destino if destino.startswith('EPSG') else f'UTM {zona}{hemisferio} ({datum})'}")
        st.code(f"X: {x:.2f}\nY: {y:.2f}\nFuso: {zona}{hemisferio}", language="text")
    except Exception as e:
        st.error(f"Erro na conversão: {e}. Verifique se os valores são válidos.")


def _utm_para_graus(datum):
    c1, c2 = st.columns(2)
    with c1:
        x = st.number_input("X ou E (Leste):", value=566865.53, format="%.2f", key="x_utm_input")
    with c2:
        y = st.number_input("Y ou N (Norte):", value=9745153.65, format="%.2f", key="y_utm_input")

    c3, c4 = st.columns(2)
    with c3:
        zona = st.number_input("Fuso UTM (1 a 60):", min_value=1, max_value=60, value=23, step=1, key="zona_utm_input")
    with c4:
        hemisferio = st.radio("Hemisfério:", ["S", "N"], horizontal=True, key="hemi_utm_input")

    if not st.button("🔄 Converter para Graus Decimais", key="convert_graus"):
        return

    try:
        origem = crs_utm(int(zona), hemisferio, datum)
        transformer = pyproj.Transformer.from_crs(origem, crs_geografico(datum), always_xy=True)
        lon, lat = transformer.transform(x, y)

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("resultado fora dos limites; confira X, Y, fuso e hemisfério")

        st.success("✅ Conversão realizada com sucesso!")
        r1, r2 = st.columns(2)
        r1.metric("📌 Latitude", f"{lat:.6f}°")
        r2.metric("📌 Longitude", f"{lon:.6f}°")
        st.code(f"Latitude: {lat:.6f}\nLongitude: {lon:.6f}", language="text")
    except Exception as e:
        st.error(f"Erro na conversão: {e}. Verifique se os valores são válidos.")


def render():
    st.header("Conversor de Coordenadas")
    inverso = st.session_state.get("utm_inverso", False)

    col_titulo, col_botao = st.columns([4, 1])
    with col_titulo:
        st.subheader("UTM → Graus Decimais" if inverso else "Graus Decimais → UTM")
    with col_botao:
        st.button("🔁 Inverter", on_click=_inverter, use_container_width=True, key="btn_inverter")

    datum = st.selectbox("Datum:", ["WGS 84", "SIRGAS 2000"], key="datum_utm")

    if inverso:
        _utm_para_graus(datum)
    else:
        _graus_para_utm(datum)
