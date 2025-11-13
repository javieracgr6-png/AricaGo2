import math
import requests
import pandas as pd
import streamlit as st

# ============================
# CONFIGURACIÓN GENERAL
# ============================
st.set_page_config(
    page_title="AricaGo - Asistente Turístico",
    page_icon="🌎",
    layout="wide",
)

# ============================
# CARGA DE DATOS
# ============================
@st.cache_data
def cargar_lugares():
    df = pd.read_csv("data/lugares.csv")
    return df

lugares_df = cargar_lugares()

# 3 primeros como destacados (puedes cambiarlo después)
destacados_df = lugares_df.head(3).copy()

# categorías únicas
categorias = sorted(lugares_df["categoria"].unique().tolist())

# ============================
# FUNCIONES AUXILIARES
# ============================
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_weather_arica():
    lat, lon = -18.48, -70.31
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current_weather=true"
    )
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        current = data.get("current_weather", {})
        temp = current.get("temperature")
        wind = current.get("windspeed")
        code = current.get("weathercode")

        desc = "Despejado"
        if code in [1, 2, 3]:
            desc = "Parcialmente nublado"
        if code in [45, 48]:
            desc = "Niebla"
        if code in [51, 53, 55, 61, 63, 65]:
            desc = "Lluvia"
        if code in [71, 73, 75, 77]:
            desc = "Nieve"
        if code in [95, 96, 99]:
            desc = "Tormenta"

        return {
            "ciudad": "Arica",
            "temp": temp,
            "viento": wind,
            "descripcion": desc,
        }
    except Exception:
        return {
            "ciudad": "Arica",
            "temp": 24,
            "viento": 8,
            "descripcion": "Soleado (demo offline)",
        }

def convertir_divisa(monto, desde, hacia):
    try:
        url = f"https://api.frankfurter.app/latest?amount={monto}&from={desde}&to={hacia}"
        response = requests.get(url)

        if response.status_code != 200:
            return None, "No se pudo conectar al servicio de divisas."

        data = response.json()

        if "rates" not in data or hacia not in data["rates"]:
            return None, "No se encontró la tasa de cambio solicitada."

        resultado = data["rates"][hacia]
        return resultado, None

    except Exception as e:
        return None, f"Error: {str(e)}"


# ============================
# UI PRINCIPAL
# ============================
st.title("🌎 AricaGo – Asistente Turístico Inteligente")
st.caption("Descubre la Región de Arica y Parinacota con recomendaciones cercanas a ti.")

# Barra rápida
with st.container():
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.text_input("🔍 ¿Qué quieres explorar hoy?", placeholder="Ej: playas tranquilas, miradores, museos...")
    with col_r:
        st.write("")
        st.write("")
        st.button("🎲 Sugerir un destino al azar")

# 1) Destinos destacados
st.subheader("🏅 Destinos destacados")
cols = st.columns(3)
for col, (_, destino) in zip(cols, destacados_df.iterrows()):
    with col:
        st.image(destino["imagen"], use_container_width=True)
        st.markdown(f"**{destino['nombre']}**")
        st.caption(destino["descripcion"])

st.markdown("---")

# 2) Búsqueda por categorías
st.subheader("🧭 Explora por categoría")
opcion_categoria = st.radio(
    "Selecciona una categoría",
    options=["Todas"] + categorias,
    horizontal=True,
)

if opcion_categoria == "Todas":
    filtrados_df = lugares_df.copy()
else:
    filtrados_df = lugares_df[lugares_df["categoria"] == opcion_categoria].copy()

st.write(f"Mostrando {len(filtrados_df)} lugar(es) para: **{opcion_categoria}**")

# 3) Lugares cerca de ti
st.subheader("📍 Lugares cerca de ti")
with st.expander("Configurar ubicación (simulación GPS)", expanded=True):
    st.write("Para la demo, ingresamos latitud y longitud manualmente.")
    col1, col2 = st.columns(2)
    with col1:
        lat_user = st.number_input("Latitud", value=-18.478, format="%.6f")
    with col2:
        lon_user = st.number_input("Longitud", value=-70.312, format="%.6f")

# calcular distancias
filtrados_df["dist_km"] = filtrados_df.apply(
    lambda row: haversine_km(lat_user, lon_user, row["lat"], row["lon"]), axis=1
)
filtrados_df = filtrados_df.sort_values("dist_km")

cols_cards = st.columns(3)
for i, (_, lugar) in enumerate(filtrados_df.iterrows()):
    col = cols_cards[i % 3]
    with col:
        st.image(lugar["imagen"], use_container_width=True)
        st.markdown(f"**{lugar['nombre']}**")
        st.caption(lugar["descripcion"])
        st.write(f"📍 {lugar['dist_km']:.1f} km · 🏷️ {lugar['categoria']}")

st.markdown("---")

# 4) Clima Arica
st.subheader("☀️ Clima actual en Arica")
weather = get_weather_arica()
col_w1, col_w2 = st.columns([2, 1])
with col_w1:
    st.markdown(f"**{weather['ciudad']}**")
    st.write(f"**{weather['temp']} °C** · {weather['descripcion']}")
    st.caption(f"Viento: {weather['viento']} km/h (fuente: Open-Meteo)")
with col_w2:
    st.metric("Temperatura", f"{weather['temp']} °C")
    st.metric("Viento", f"{weather['viento']} km/h")

st.markdown("---")

# 5) Conversor de divisas
st.subheader("💱 Conversor de divisas rápido")
col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
with col_c1:
    monto = st.number_input("Monto", min_value=0.0, value=10000.0, step=100.0)
with col_c2:
    desde = st.selectbox("Desde", ["CLP", "USD", "EUR"], index=0)
with col_c3:
    hacia = st.selectbox("Hacia", ["USD", "CLP", "EUR"], index=1)

if st.button("Convertir"):
    resultado = convertir_divisa(monto, desde, hacia)
    if resultado is not None:
        st.success(f"{monto:,.2f} {desde} ≈ {resultado:,.2f} {hacia}")
    else:
        st.error("No se pudo obtener la tasa de cambio. Intenta nuevamente más tarde.")

st.caption("Fuente: exchangerate.host (servicio gratuito de tasas de cambio).")
