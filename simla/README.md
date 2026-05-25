# 🌊 SiMLA — Sistema de Monitoreo y Simulación Ambiental
### Lago de Amatitlán, Guatemala

Proyecto académico · Universidad del Valle de Guatemala  
Curso: Retos Ambientales · Fase 4

---

## Estructura del proyecto

```
simla/
├── app.py                  # Dashboard principal (Streamlit)
├── requirements.txt        # Dependencias
├── data/
│   ├── __init__.py
│   └── generator.py        # Generador de datos simulados + índice de riesgo
└── README.md
```

---

## Instalación y ejecución

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar el dashboard
```bash
streamlit run app.py
```

El dashboard abrirá automáticamente en `http://localhost:8501`

---

## Módulos disponibles

| Módulo | Descripción |
|--------|-------------|
| 📊 Visualización de datos | Serie temporal, distribución por época, promedio mensual |
| ⚠️ Índice de riesgo | Semáforo verde/amarillo/rojo basado en umbrales científicos |
| 📈 Análisis comparativo | Scatter plots, línea de tendencia, matriz de correlación |

---

## Parámetros monitoreados

| Parámetro | Unidad | Umbral alto (riesgo) |
|-----------|--------|----------------------|
| Fósforo total | mg/L | ≥ 0.10 mg/L |
| Nitrógeno total | mg/L | ≥ 2.0 mg/L |
| Oxígeno disuelto | mg/L | ≤ 4.0 mg/L |
| Temperatura | °C | ≥ 26 °C |
| Clorofila-a | µg/L | ≥ 50 µg/L |
| Coliformes fecales | NMP/100mL | ≥ 1000 |
| Caudal Villalobos | m³/s | ≥ 15 m³/s |

---

## Justificación del índice de riesgo

El índice se calcula con base en tres parámetros principales:
- **Fósforo total** (40 pts): principal limitante de la eutrofización
- **Clorofila-a** (35 pts): proxy directo de la biomasa de cianobacterias
- **Oxígeno disuelto** (25 pts, invertido): indicador de hipoxia

Umbrales basados en: OCDE (1982), Vollenweider & Kerekes (1982),  
y reportes técnicos de AMSA para el Lago de Amatitlán.

---

## Próximas fases (roadmap)

- [ ] Módulo de simulación de escenarios (Fase 4b)
- [ ] Mapa interactivo con Folium (zonas críticas)
- [ ] Modelo predictivo simple (regresión lineal)
- [ ] Exportación de reportes PDF
