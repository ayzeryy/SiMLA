"""
SiMLA — Sistema de Monitoreo y Simulación Ambiental
     Lago de Amatitlán, Guatemala
──────────────────────────────────────────────────────
Módulo 1: Carga y Visualización de Datos Ambientales
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data.generator import generar_serie_temporal, enriquecer_con_riesgo, THRESHOLDS

# ─── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="SiMLA | Lago de Amatitlán",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Estilos CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }

    .main { background-color: #0d1117; }

    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #0f1f2e 50%, #0d1117 100%);
    }

    .metric-card {
        background: linear-gradient(145deg, #161b22, #1c2733);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: border-color 0.3s;
    }

    .metric-card:hover { border-color: #58a6ff; }

    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 600;
        line-height: 1;
    }

    .metric-label {
        font-size: 0.75rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 6px;
    }

    .metric-unit {
        font-size: 0.85rem;
        color: #58a6ff;
        font-family: 'JetBrains Mono', monospace;
    }

    .risk-badge {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.05em;
    }

    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #c9d1d9;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        border-bottom: 1px solid #21262d;
        padding-bottom: 8px;
        margin-bottom: 16px;
    }

    .header-bar {
        background: linear-gradient(90deg, #0d1117, #0f1f2e);
        border-bottom: 1px solid #21262d;
        padding: 16px 0;
        margin-bottom: 24px;
    }

    .stSelectbox > div, .stMultiSelect > div {
        background-color: #161b22 !important;
        border-color: #30363d !important;
    }

    div[data-testid="stSidebarContent"] {
        background: #161b22;
        border-right: 1px solid #21262d;
    }

    .stSlider > div { padding: 0; }
    .stMetric { background: transparent; }
</style>
""", unsafe_allow_html=True)

# ─── Carga de datos ───────────────────────────────────────────────────────────
@st.cache_data
def cargar_datos(fuente: str, archivo=None) -> pd.DataFrame:
    if fuente == "Datos simulados (demo)" or archivo is None:
        df = generar_serie_temporal(años=3, frecuencia="W")
    else:
        df = pd.read_csv(archivo, parse_dates=["fecha"])
    return enriquecer_con_riesgo(df)


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌊 SiMLA")
    st.markdown("**Sistema de Monitoreo y Simulación Ambiental**")
    st.markdown("*Lago de Amatitlán, Guatemala*")
    st.divider()

    fuente = st.selectbox(
        "Fuente de datos",
        ["Datos simulados (demo)", "Cargar CSV propio"],
        help="Selecciona 'Datos simulados' para usar datos generados con rangos reales del lago."
    )

    archivo = None
    if fuente == "Cargar CSV propio":
        archivo = st.file_uploader(
            "Sube tu CSV",
            type=["csv"],
            help="El CSV debe tener columna 'fecha' y los parámetros con los mismos nombres del sistema."
        )

    st.divider()
    st.markdown("**Módulos disponibles**")
    modulo = st.radio(
        "",
        ["📊 Visualización de datos", "⚠️ Índice de riesgo", "📈 Análisis comparativo"],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("Universidad del Valle de Guatemala\nCurso: Retos Ambientales · 2026")


# ─── Carga principal ──────────────────────────────────────────────────────────
if fuente == "Cargar CSV propio" and archivo is None:
    st.info("⬆️ Sube un archivo CSV en la barra lateral para continuar, o cambia a 'Datos simulados'.")
    st.stop()

df = cargar_datos(fuente, archivo)

# ─── Filtros de fecha y época ─────────────────────────────────────────────────
col_f1, col_f2, col_f3 = st.columns([2, 2, 1])

with col_f1:
    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()
    rango = st.date_input(
        "Rango de fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

with col_f2:
    epocas = st.multiselect(
        "Época climática",
        options=df["epoca"].unique().tolist(),
        default=df["epoca"].unique().tolist()
    )

with col_f3:
    años_sel = st.multiselect(
        "Año",
        options=sorted(df["año"].unique().tolist()),
        default=sorted(df["año"].unique().tolist())
    )

# Aplicar filtros
if len(rango) == 2:
    mask = (
        (df["fecha"].dt.date >= rango[0]) &
        (df["fecha"].dt.date <= rango[1]) &
        (df["epoca"].isin(epocas)) &
        (df["año"].isin(años_sel))
    )
    df_filtrado = df[mask].copy()
else:
    df_filtrado = df.copy()

if df_filtrado.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# MÓDULO 1: VISUALIZACIÓN DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════
if modulo == "📊 Visualización de datos":

    st.markdown("## 📊 Visualización de Parámetros Ambientales")
    st.caption(f"Lago de Amatitlán · {len(df_filtrado)} registros en el período seleccionado")

    # ── KPIs principales ──────────────────────────────────────────────────────
    st.markdown('<p class="section-title">Resumen del período</p>', unsafe_allow_html=True)

    params_kpi = {
        "fosforo_total":    ("Fósforo Total",    "mg/L",     "#e74c3c"),
        "nitrogeno_total":  ("Nitrógeno Total",  "mg/L",     "#e67e22"),
        "oxigeno_disuelto": ("Oxígeno Disuelto", "mg/L",     "#3498db"),
        "temperatura":      ("Temperatura",       "°C",       "#9b59b6"),
        "clorofila_a":      ("Clorofila-a",       "µg/L",     "#2ecc71"),
        "riesgo_score":     ("Índice de Riesgo", "/ 100",    "#f1c40f"),
    }

    cols = st.columns(len(params_kpi))
    for col, (param, (label, unit, color)) in zip(cols, params_kpi.items()):
        val_mean = df_filtrado[param].mean()
        val_max  = df_filtrado[param].max()
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:{color};">{val_mean:.2f}</div>
                <div class="metric-unit">{unit}</div>
                <div class="metric-label">{label}<br>promedio</div>
                <div style="font-size:0.7rem;color:#6e7681;margin-top:4px;">máx: {val_max:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Selector de parámetro para gráfica principal ──────────────────────────
    st.markdown('<p class="section-title">Serie temporal</p>', unsafe_allow_html=True)

    param_opciones = {
        "Fósforo Total (mg/L)":      "fosforo_total",
        "Nitrógeno Total (mg/L)":    "nitrogeno_total",
        "Oxígeno Disuelto (mg/L)":   "oxigeno_disuelto",
        "Temperatura (°C)":           "temperatura",
        "Clorofila-a (µg/L)":        "clorofila_a",
        "Coliformes (NMP/100mL)":    "coliformes",
        "Caudal Villalobos (m³/s)":  "caudal_villalobos",
        "Precipitación (mm)":        "precipitacion",
    }

    col_p1, col_p2 = st.columns([3, 1])
    with col_p1:
        param_sel = st.selectbox("Parámetro a visualizar", list(param_opciones.keys()))
    with col_p2:
        mostrar_umbral = st.checkbox("Mostrar umbrales", value=True)

    param_col = param_opciones[param_sel]

    # Gráfica de serie temporal
    fig = go.Figure()

    # Área bajo la curva
    fig.add_trace(go.Scatter(
        x=df_filtrado["fecha"],
        y=df_filtrado[param_col],
        mode="lines",
        name=param_sel.split("(")[0].strip(),
        line=dict(color="#58a6ff", width=1.5),
        fill="tozeroy",
        fillcolor="rgba(88,166,255,0.08)",
        hovertemplate="%{x|%d %b %Y}<br><b>%{y:.3f}</b><extra></extra>"
    ))

    # Media móvil 4 semanas
    df_filtrado["rolling_mean"] = df_filtrado[param_col].rolling(window=4, center=True).mean()
    fig.add_trace(go.Scatter(
        x=df_filtrado["fecha"],
        y=df_filtrado["rolling_mean"],
        mode="lines",
        name="Media móvil (4 sem.)",
        line=dict(color="#f1c40f", width=2, dash="dot"),
        hovertemplate="%{x|%d %b %Y}<br>Media: <b>%{y:.3f}</b><extra></extra>"
    ))

    # Umbrales
    if mostrar_umbral and param_col in THRESHOLDS:
        th = THRESHOLDS[param_col]
        colores_umbral = {"bajo": "#2ecc71", "medio": "#f39c12", "alto": "#e74c3c"}
        for nivel, valor in th.items():
            fig.add_hline(
                y=valor,
                line_dash="dash",
                line_color=colores_umbral[nivel],
                line_width=1,
                annotation_text=f"  {nivel.capitalize()} ({valor})",
                annotation_font_color=colores_umbral[nivel],
                annotation_font_size=11,
            )

    fig.update_layout(
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Space Grotesk"),
        xaxis=dict(
            showgrid=True, gridcolor="#21262d", gridwidth=0.5,
            showline=True, linecolor="#30363d",
            tickformat="%b %Y"
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#21262d", gridwidth=0.5,
            showline=True, linecolor="#30363d",
        ),
        legend=dict(
            bgcolor="#161b22", bordercolor="#30363d", borderwidth=1,
            font=dict(size=11)
        ),
        hovermode="x unified",
        height=380,
        margin=dict(l=10, r=10, t=20, b=10),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Gráficas secundarias: distribución + comparativa épocas ──────────────
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.markdown('<p class="section-title">Distribución por época</p>', unsafe_allow_html=True)
        fig_box = px.box(
            df_filtrado, x="epoca", y=param_col,
            color="epoca",
            color_discrete_map={
                "Lluviosa (May–Oct)": "#3498db",
                "Seca (Nov–Abr)":    "#e67e22"
            },
            points="outliers",
            labels={param_col: param_sel, "epoca": "Época"}
        )
        fig_box.update_layout(
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Space Grotesk"),
            showlegend=False,
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(showgrid=False, linecolor="#30363d"),
            yaxis=dict(showgrid=True, gridcolor="#21262d"),
        )
        st.plotly_chart(fig_box, use_container_width=True)

    with col_d2:
        st.markdown('<p class="section-title">Promedio mensual</p>', unsafe_allow_html=True)
        df_mensual = df_filtrado.groupby("mes")[param_col].mean().reset_index()
        meses_nombres = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                         7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
        df_mensual["mes_nombre"] = df_mensual["mes"].map(meses_nombres)

        fig_bar = px.bar(
            df_mensual, x="mes_nombre", y=param_col,
            color=param_col,
            color_continuous_scale=["#1a4a6e", "#58a6ff", "#e74c3c"],
            labels={param_col: param_sel, "mes_nombre": "Mes"}
        )
        fig_bar.update_layout(
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Space Grotesk"),
            coloraxis_showscale=False,
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(showgrid=False, linecolor="#30363d", categoryorder="array",
                       categoryarray=list(meses_nombres.values())),
            yaxis=dict(showgrid=True, gridcolor="#21262d"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Tabla de datos ────────────────────────────────────────────────────────
    with st.expander("📋 Ver tabla de datos completa"):
        columnas_display = [
            "fecha", "epoca", "precipitacion", "caudal_villalobos",
            "fosforo_total", "nitrogeno_total", "oxigeno_disuelto",
            "temperatura", "clorofila_a", "coliformes",
            "riesgo_score", "riesgo_nivel"
        ]
        st.dataframe(
            df_filtrado[columnas_display].sort_values("fecha", ascending=False),
            use_container_width=True,
            height=300,
        )
        csv = df_filtrado[columnas_display].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar CSV",
            data=csv,
            file_name="simla_datos_lago_amatitlan.csv",
            mime="text/csv"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MÓDULO 2: ÍNDICE DE RIESGO
# ═══════════════════════════════════════════════════════════════════════════════
elif modulo == "⚠️ Índice de riesgo":

    st.markdown("## ⚠️ Índice de Riesgo de Eutrofización")
    st.caption("Calculado en base a fósforo total, clorofila-a y oxígeno disuelto · Escala 0–100")

    # ── Semáforo del período ──────────────────────────────────────────────────
    riesgo_actual = df_filtrado["riesgo_score"].iloc[-1]
    nivel_actual  = df_filtrado["riesgo_nivel"].iloc[-1]
    color_actual  = df_filtrado["riesgo_color"].iloc[-1]

    col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
    with col_r2:
        st.markdown(f"""
        <div class="metric-card" style="border-color:{color_actual}; padding:32px;">
            <div style="font-size:0.8rem;color:#8b949e;text-transform:uppercase;letter-spacing:0.1em;">
                Última lectura — Índice de Riesgo
            </div>
            <div class="metric-value" style="color:{color_actual}; font-size:4rem; margin:16px 0;">
                {riesgo_actual:.0f}
            </div>
            <div style="font-size:0.75rem;color:#8b949e;">de 100 puntos</div>
            <br>
            <span class="risk-badge" style="background:{color_actual}22; color:{color_actual}; border:1px solid {color_actual};">
                RIESGO {nivel_actual.upper()}
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Serie temporal del índice ─────────────────────────────────────────────
    st.markdown('<p class="section-title">Evolución del índice de riesgo</p>', unsafe_allow_html=True)

    fig_risk = go.Figure()

    # Zonas de color
    zonas = [
        (0,  25,  "rgba(46,204,113,0.08)",  "Bajo"),
        (25, 50,  "rgba(243,156,18,0.08)",  "Medio"),
        (50, 75,  "rgba(230,126,34,0.08)",  "Alto"),
        (75, 100, "rgba(231,76,60,0.08)",   "Crítico"),
    ]
    for y0, y1, color, label in zonas:
        fig_risk.add_hrect(y0=y0, y1=y1, fillcolor=color, line_width=0,
                           annotation_text=f"  {label}", annotation_position="left",
                           annotation_font_color="#8b949e", annotation_font_size=10)

    fig_risk.add_trace(go.Scatter(
        x=df_filtrado["fecha"],
        y=df_filtrado["riesgo_score"],
        mode="lines+markers",
        marker=dict(
            color=df_filtrado["riesgo_score"],
            colorscale=[[0,"#2ecc71"],[0.33,"#f39c12"],[0.66,"#e67e22"],[1,"#e74c3c"]],
            size=5,
            line=dict(width=0),
        ),
        line=dict(color="#58a6ff", width=1.5),
        fill="tozeroy",
        fillcolor="rgba(88,166,255,0.05)",
        name="Índice de riesgo",
        hovertemplate="%{x|%d %b %Y}<br>Riesgo: <b>%{y:.1f}/100</b><extra></extra>"
    ))

    fig_risk.update_layout(
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Space Grotesk"),
        xaxis=dict(showgrid=True, gridcolor="#21262d", tickformat="%b %Y"),
        yaxis=dict(showgrid=False, range=[0, 105]),
        height=350,
        margin=dict(l=10, r=80, t=10, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig_risk, use_container_width=True)

    # ── Distribución de niveles ───────────────────────────────────────────────
    col_pie1, col_pie2 = st.columns(2)
    with col_pie1:
        st.markdown('<p class="section-title">Distribución de niveles</p>', unsafe_allow_html=True)
        dist = df_filtrado["riesgo_nivel"].value_counts().reset_index()
        dist.columns = ["nivel", "conteo"]
        color_map = {"Bajo":"#2ecc71","Medio":"#f39c12","Alto":"#e67e22","Crítico":"#e74c3c"}
        fig_pie = px.pie(
            dist, values="conteo", names="nivel",
            color="nivel", color_discrete_map=color_map,
            hole=0.5,
        )
        fig_pie.update_layout(
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Space Grotesk"),
            height=280, margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_pie2:
        st.markdown('<p class="section-title">Estadísticas del índice</p>', unsafe_allow_html=True)
        stats = df_filtrado["riesgo_score"].describe()
        st.markdown(f"""
        <div class="metric-card" style="text-align:left; margin-top:0;">
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                <div>
                    <div class="metric-label">Promedio</div>
                    <div class="metric-value" style="color:#58a6ff;font-size:1.6rem;">{stats['mean']:.1f}</div>
                </div>
                <div>
                    <div class="metric-label">Máximo</div>
                    <div class="metric-value" style="color:#e74c3c;font-size:1.6rem;">{stats['max']:.1f}</div>
                </div>
                <div>
                    <div class="metric-label">Mínimo</div>
                    <div class="metric-value" style="color:#2ecc71;font-size:1.6rem;">{stats['min']:.1f}</div>
                </div>
                <div>
                    <div class="metric-label">Desv. estándar</div>
                    <div class="metric-value" style="color:#f1c40f;font-size:1.6rem;">{stats['std']:.1f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MÓDULO 3: ANÁLISIS COMPARATIVO
# ═══════════════════════════════════════════════════════════════════════════════
elif modulo == "📈 Análisis comparativo":

    st.markdown("## 📈 Análisis Comparativo entre Parámetros")

    param_map = {
        "Fósforo Total":     "fosforo_total",
        "Nitrógeno Total":   "nitrogeno_total",
        "Oxígeno Disuelto":  "oxigeno_disuelto",
        "Temperatura":        "temperatura",
        "Clorofila-a":       "clorofila_a",
        "Coliformes":        "coliformes",
        "Caudal Villalobos": "caudal_villalobos",
        "Precipitación":     "precipitacion",
        "Índice de Riesgo":  "riesgo_score",
    }

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        eje_x = st.selectbox("Eje X", list(param_map.keys()), index=0)
    with col_c2:
        eje_y = st.selectbox("Eje Y", list(param_map.keys()), index=4)

    # Scatter con color por época
    fig_scatter = px.scatter(
        df_filtrado,
        x=param_map[eje_x],
        y=param_map[eje_y],
        color="epoca",
        color_discrete_map={
            "Lluviosa (May–Oct)": "#3498db",
            "Seca (Nov–Abr)":    "#e67e22"
        },
        trendline="ols",
        trendline_scope="overall",
        labels={param_map[eje_x]: eje_x, param_map[eje_y]: eje_y},
        hover_data=["fecha", "riesgo_nivel"],
        opacity=0.7,
    )
    fig_scatter.update_layout(
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Space Grotesk"),
        xaxis=dict(showgrid=True, gridcolor="#21262d"),
        yaxis=dict(showgrid=True, gridcolor="#21262d"),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
        height=420,
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Correlación
    st.markdown('<p class="section-title">Matriz de correlación</p>', unsafe_allow_html=True)
    cols_corr = [v for v in param_map.values()]
    corr_matrix = df_filtrado[cols_corr].corr().round(2)

    fig_corr = px.imshow(
        corr_matrix,
        text_auto=True,
        color_continuous_scale=["#e74c3c","#0d1117","#3498db"],
        zmin=-1, zmax=1,
        labels=dict(color="Correlación"),
        x=list(param_map.keys()),
        y=list(param_map.keys()),
    )
    fig_corr.update_layout(
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Space Grotesk", size=10),
        height=500,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_corr, use_container_width=True)
