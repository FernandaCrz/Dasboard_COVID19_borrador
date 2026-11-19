import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium





# Configuración inicial de la página
st.set_page_config(
    page_title="COVID-19",
    layout="wide",
    initial_sidebar_state="collapsed",
)

@st.cache_data
def load_data():
    return pd.read_csv("casos_COVID_por_Entidad_2020_5.csv")
df = load_data()

@st.cache_data
def load_data_activos():
    return pd.read_csv("casos_covid_activos_2020_5.csv")
df2 = load_data_activos()


#ENCABEZADO
st.markdown(
    "<span style='background-color: #2563eb; color: white; padding: 4px 10px;"
    " border-radius: 9999px; font-size: 11px; font-weight:"
    " bold;'>ANÁLISIS EPIDEMIOLÓGICO NACIONAL</span>",
    unsafe_allow_html=True,
)

st.title("COVID-19")


#DESCRIPCION
st.markdown("####    ¿Que es?")
st.write(
        "Enfermedad respiratoria aguda causada por el virus SARS-CoV-2."
    )
st.markdown("#####  Síntomas:")
st.write(
        "Fiebre, tos, dolor de garganta, congestión o secreción nasal, "
        "dolor de cabeza, dolor muscular o corporal, fatiga o cansancio."
    )
st.markdown("#####  Método de Propagación:")
st.write(
        "Se propaga principalmente de persona a persona a través de gotitas "
        "que se expulsan cuando una persona infectada tose, estornuda, "
        "habla o respira. También puede contraerse al tocar superficies "
        "u objetos contaminados y luego llevarse las manos a la cara, la nariz o la boca."
    )



#PESTAÑAS
st.markdown("### Vista General - Análisis Global")
ano_general = st.radio(
        "Selecciona el periodo temporal:",
        [
            "Suma de Casos",
            "2020",
            "2021",
            "2022",
            "2023",
            "2024",
            "2025"
        ],  
        index=0,
        horizontal=True,
        key="radio_general",
    )




#LINEA TEMPORAL
st.markdown("#### Evolución Temporal de Casos")

df_activos = df2.copy()
df_activos["FECHA_SINTOMAS"] = pd.to_datetime(df_activos["FECHA_SINTOMAS"], errors="coerce")
df_activos["CASOS_ACTIVOS_ESTIMADOS_14D"] = pd.to_numeric(df_activos["CASOS_ACTIVOS_ESTIMADOS_14D"], errors="coerce")
df_activos = df_activos.dropna(subset=["FECHA_SINTOMAS", "CASOS_ACTIVOS_ESTIMADOS_14D"])

if ano_general != "Suma de Casos":
    df_activos = df_activos[
        df_activos["FECHA_SINTOMAS"].dt.year == int(ano_general)
    ]

# Agrupar por fecha en caso de que existan varios registros por día (por ejemplo, por entidad)
df_linea = (df_activos.groupby("FECHA_SINTOMAS", as_index=False)["CASOS_ACTIVOS_ESTIMADOS_14D"].sum().sort_values("FECHA_SINTOMAS"))

if df_linea.empty:
    st.warning("No hay datos de casos activos estimados disponibles para '{ano_general}'.")
else:
    titulo_grafico = (
        "Casos Activos Estimados - Histórico Completo"
        if ano_general == "Suma de Casos"
        else f"Casos Activos Estimados -  {ano_general}"
    )

    fig_linea = px.line(
        df_linea,
        x="FECHA_SINTOMAS",
        y="CASOS_ACTIVOS_ESTIMADOS_14D",
        title=titulo_grafico,
        labels={
            "FECHA_SINTOMAS": "Fecha de Inicio de Síntomas",
            "CASOS_ACTIVOS_ESTIMADOS_14D": "Casos Activos Estimados",
        },
    )
    fig_linea.update_layout(hovermode="x unified")
    st.plotly_chart(fig_linea, use_container_width=True)




#MAPA
st.markdown("#### Distribución Geográfica de Casos por Entidad")

df_mapa = df.copy()
df_mapa["LATITUD"] = pd.to_numeric(df_mapa["LATITUD"], errors="coerce")
df_mapa["LONGITUD"] = pd.to_numeric(df_mapa["LONGITUD"], errors="coerce")
df_mapa["CASOS"] = pd.to_numeric(df_mapa["CASOS"], errors="coerce")

col_anio = next(
    (
        col
        for col in ["ANIO", "AÑO", "YEAR", "FECHA", "FECHA_SINTOMAS"]
        if col in df_mapa.columns
    ),
    None,
)

if ano_general != "Suma de Casos" and col_anio is not None:
    if pd.api.types.is_numeric_dtype(df_mapa[col_anio]):
        df_mapa = df_mapa[df_mapa[col_anio] == int(ano_general)]
    else:
        fechas_parsed = pd.to_datetime(df_mapa[col_anio], errors="coerce")
        if fechas_parsed.notna().any():
            df_mapa = df_mapa[fechas_parsed.dt.year == int(ano_general)]
        else:
            df_mapa = df_mapa[
                df_mapa[col_anio].astype(str).str.strip() == str(ano_general)
            ]

df_mapa = df_mapa.dropna(subset=["LATITUD", "LONGITUD", "CASOS"])

# Agrupar por entidad y coordenadas para evitar marcadores superpuestos
df_mapa_agg = df_mapa.groupby(
    ["ENTIDAD_RES", "ENTIDAD_FEDERATIVA", "LATITUD", "LONGITUD"],
    as_index=False,
)["CASOS"].sum()

if df_mapa_agg.empty:
    st.warning(
        f"No hay datos geográficos disponibles para '{ano_general}'."
    )
else:
    titulo_mapa = (
        "Casos por Entidad Federativa - Histórico"
        if ano_general == "Suma de Casos"
        else f"Casos por Entidad Federativa - Año {ano_general}"
    )

fig_mapa = px.scatter_map(
        df_mapa_agg,
        lat="LATITUD",
        lon="LONGITUD",
        size="CASOS",
        color="CASOS",
        hover_name="ENTIDAD_FEDERATIVA",
        hover_data={
            "ENTIDAD_RES": True,
            "CASOS": ":,",
            "LATITUD": False,
            "LONGITUD": False,
        },
        size_max=45,
        zoom=4.3,
        center={"lat": 23.6345, "lon": -102.5528},
        map_style="carto-positron",
        color_continuous_scale="Plasma",
        title=titulo_mapa,
        labels={"CASOS": "Casos"},
    )
fig_mapa.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
st.plotly_chart(fig_mapa, use_container_width=True)





#BARRAS Y PASTEL
if not df_mapa_agg.empty:
    st.markdown("#### Entidades con Más Casos")

    df_ranking = (
        df_mapa_agg.groupby("ENTIDAD_FEDERATIVA", as_index=False)["CASOS"]
        .sum()
        .sort_values("CASOS", ascending=False)
        .reset_index(drop=True)
    )

    top5 = df_ranking.head(5).copy()
    otros_casos = df_ranking.iloc[5:]["CASOS"].sum()

    df_pastel = top5.copy()
    if otros_casos > 0:
        df_pastel = pd.concat(
            [
                df_pastel,
                pd.DataFrame(
                    [{"ENTIDAD_FEDERATIVA": "Otros", "CASOS": otros_casos}]
                ),
            ],
            ignore_index=True,
        )

    subtitulo_periodo = (
        "Histórico"
        if ano_general == "Suma de Casos"
        else f"Año {ano_general}"
    )

    col_barras, col_pastel = st.columns(2)

    with col_barras:
        fig_barras = px.bar(
            top5.sort_values("CASOS", ascending=True),
            x="CASOS",
            y="ENTIDAD_FEDERATIVA",
            orientation="h",
            text="CASOS",
            labels={
                "ENTIDAD_FEDERATIVA": "Entidad Federativa",
                "CASOS": "Casos",
            },
            color="CASOS",
            color_continuous_scale="Plasma",
        )
        fig_barras.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_barras.update_layout(
            coloraxis_showscale=False,
            margin={"r": 20, "t": 45, "l": 10, "b": 20},
        )
        st.plotly_chart(fig_barras, use_container_width=True)

    with col_pastel:
        fig_pastel = px.pie(
            df_pastel,
            names="ENTIDAD_FEDERATIVA",
            values="CASOS",
            hole=0.0,
        )
        fig_pastel.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Casos: %{value:,}<br>Porcentaje: %{percent}<extra></extra>",
        )
        fig_pastel.update_layout(margin={"r": 10, "t": 45, "l": 10, "b": 20})
        st.plotly_chart(fig_pastel, use_container_width=True)