"""
SiMLA - Generador de datos simulados
Basado en rangos reales documentados del Lago de Amatitlán y el río Villalobos.
Fuentes de referencia: AMSA, literatura científica sobre eutrofización tropical.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


# ─── Umbrales de referencia científica ───────────────────────────────────────
THRESHOLDS = {
    "fosforo_total":      {"bajo": 0.05, "medio": 0.10, "alto": 0.20},   # mg/L
    "nitrogeno_total":    {"bajo": 1.0,  "medio": 2.0,  "alto": 4.0},    # mg/L
    "oxigeno_disuelto":   {"alto": 6.0,  "medio": 4.0,  "bajo": 2.0},    # mg/L (invertido)
    "temperatura":        {"bajo": 22.0, "medio": 26.0, "alto": 30.0},   # °C
    "clorofila_a":        {"bajo": 10.0, "medio": 50.0, "alto": 100.0},  # µg/L
    "coliformes":         {"bajo": 200,  "medio": 1000, "alto": 5000},   # NMP/100mL
    "caudal_villalobos":  {"bajo": 5.0,  "medio": 15.0, "alto": 30.0},  # m³/s
    "precipitacion":      {"bajo": 10.0, "medio": 50.0, "alto": 120.0}, # mm/mes
}

# ─── Generador principal ──────────────────────────────────────────────────────
def generar_serie_temporal(
    años: int = 3,
    frecuencia: str = "W",  # semanal por defecto
    semilla: int = 42
) -> pd.DataFrame:
    """
    Genera una serie temporal de parámetros ambientales simulados
    con estacionalidad realista (época seca/lluviosa de Guatemala).
    """
    np.random.seed(semilla)

    fecha_inicio = datetime(2022, 1, 1)
    if frecuencia == "W":
        n = años * 52
    elif frecuencia == "M":
        n = años * 12
    else:
        n = años * 365

    fechas = pd.date_range(start=fecha_inicio, periods=n, freq=frecuencia)
    t = np.linspace(0, años * 2 * np.pi, n)

    # Estacionalidad: época lluviosa mayo–octubre (pico en agosto)
    lluvia_season = np.sin(t - np.pi / 6) * 0.5 + 0.5  # 0 a 1

    # ── Precipitación (mm) ──────────────────────────────────────────────────
    precip = 15 + 105 * lluvia_season + np.random.normal(0, 12, n)
    precip = np.clip(precip, 0, None)

    # ── Caudal río Villalobos (m³/s) ────────────────────────────────────────
    caudal = 4 + 28 * lluvia_season + np.random.normal(0, 2.5, n)
    caudal = np.clip(caudal, 2, None)

    # ── Fósforo total (mg/L) — aumenta con lluvia y caudal ──────────────────
    fosforo = 0.08 + 0.15 * lluvia_season + np.random.normal(0, 0.02, n)
    fosforo += np.linspace(0, 0.04, n)  # tendencia de degradación anual
    fosforo = np.clip(fosforo, 0.03, 0.45)

    # ── Nitrógeno total (mg/L) ───────────────────────────────────────────────
    nitrogeno = 1.5 + 2.5 * lluvia_season + np.random.normal(0, 0.3, n)
    nitrogeno = np.clip(nitrogeno, 0.5, 6.0)

    # ── Oxígeno disuelto (mg/L) — inversamente relacionado con nutrientes ────
    od = 7.5 - 4.0 * lluvia_season - 0.3 * (fosforo / 0.2) + np.random.normal(0, 0.5, n)
    od = np.clip(od, 0.5, 9.5)

    # ── Temperatura (°C) ────────────────────────────────────────────────────
    temp = 24 + 4 * np.sin(t - np.pi / 4) + np.random.normal(0, 0.8, n)
    temp = np.clip(temp, 20, 32)

    # ── Clorofila-a (µg/L) — proxy de biomasa algal ─────────────────────────
    clorofila = 15 + 90 * lluvia_season * (fosforo / 0.2) + np.random.normal(0, 8, n)
    clorofila = np.clip(clorofila, 5, 200)

    # ── Coliformes fecales (NMP/100mL) ──────────────────────────────────────
    coliformes = 300 + 4700 * lluvia_season + np.random.normal(0, 400, n)
    coliformes = np.clip(coliformes, 50, None).astype(int)

    df = pd.DataFrame({
        "fecha":             fechas,
        "precipitacion":     np.round(precip, 1),
        "caudal_villalobos": np.round(caudal, 2),
        "fosforo_total":     np.round(fosforo, 4),
        "nitrogeno_total":   np.round(nitrogeno, 3),
        "oxigeno_disuelto":  np.round(od, 2),
        "temperatura":       np.round(temp, 1),
        "clorofila_a":       np.round(clorofila, 1),
        "coliformes":        coliformes,
    })

    df["mes"] = df["fecha"].dt.month
    df["año"]  = df["fecha"].dt.year
    df["epoca"] = df["mes"].apply(
        lambda m: "Lluviosa (May–Oct)" if 5 <= m <= 10 else "Seca (Nov–Abr)"
    )

    return df


def calcular_indice_riesgo(row: pd.Series) -> dict:
    """
    Calcula un índice de riesgo de eutrofización (0–100) por fila
    basado en umbrales de fósforo, clorofila-a y oxígeno disuelto.
    Retorna el score y el nivel (Bajo / Medio / Alto / Crítico).
    """
    th = THRESHOLDS

    # Puntaje fósforo (0–40 pts)
    p = row["fosforo_total"]
    if p < th["fosforo_total"]["bajo"]:
        p_score = p / th["fosforo_total"]["bajo"] * 10
    elif p < th["fosforo_total"]["medio"]:
        p_score = 10 + (p - th["fosforo_total"]["bajo"]) / (th["fosforo_total"]["medio"] - th["fosforo_total"]["bajo"]) * 15
    elif p < th["fosforo_total"]["alto"]:
        p_score = 25 + (p - th["fosforo_total"]["medio"]) / (th["fosforo_total"]["alto"] - th["fosforo_total"]["medio"]) * 10
    else:
        p_score = 40
    p_score = min(p_score, 40)

    # Puntaje clorofila (0–35 pts)
    c = row["clorofila_a"]
    c_score = min((c / th["clorofila_a"]["alto"]) * 35, 35)

    # Puntaje OD invertido (0–25 pts) — menos OD = más riesgo
    od = row["oxigeno_disuelto"]
    od_score = max(0, (1 - od / th["oxigeno_disuelto"]["alto"]) * 25)

    total = p_score + c_score + od_score

    if total < 25:
        nivel = "Bajo"
        color = "#2ecc71"
    elif total < 50:
        nivel = "Medio"
        color = "#f39c12"
    elif total < 75:
        nivel = "Alto"
        color = "#e67e22"
    else:
        nivel = "Crítico"
        color = "#e74c3c"

    return {"score": round(total, 1), "nivel": nivel, "color": color}


def enriquecer_con_riesgo(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas de índice de riesgo al DataFrame."""
    riesgos = df.apply(calcular_indice_riesgo, axis=1)
    df["riesgo_score"] = [r["score"] for r in riesgos]
    df["riesgo_nivel"] = [r["nivel"] for r in riesgos]
    df["riesgo_color"] = [r["color"] for r in riesgos]
    return df
