# ⛏️ El Reducto — Inteligencia Minera en Tiempo Real

> Monitor de riesgo para el sector minero peruano, impulsado por IA.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://el-reducto.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ¿Qué es?

**El Reducto** es una aplicación web que recopila noticias del sector minero peruano en tiempo real, las clasifica automáticamente por nivel de riesgo (ALTO / MEDIO / BAJO) usando inteligencia artificial, y genera análisis de impacto específicos para empresas del sector.

Pensado para analistas, gestores de riesgo y equipos de relaciones comunitarias que necesitan estar informados sin perder horas filtrando ruido informativo.

---

## Funcionalidades

- **Feed de noticias en tiempo real** — Scraping de múltiples fuentes vía Google News RSS
- **Clasificación automática de riesgo** — LLM (LLaMA 3 vía Groq API) clasifica cada noticia en ALTO, MEDIO o BAJO riesgo
- **Análisis de impacto por empresa** — Genera un análisis específico del impacto de cada noticia sobre una empresa minera seleccionada
- **Resumen semanal IA** — Párrafo de contexto sobre el panorama de riesgo de la semana
- **Radar de anomalías** — Detecta semanas con actividad inusualmente alta mediante análisis estadístico
- **Keywords automáticos** — Extracción de términos clave con TF-IDF
- **Historial de 30 días** — Gráfico apilado de distribución de riesgo diario
- **Persistencia local** — Base de datos en JSON con deduplicación por hash MD5

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Frontend / App | Streamlit |
| Web Scraping | BeautifulSoup, Google News RSS |
| IA / NLP | Groq API (LLaMA 3), Prompt Engineering |
| Análisis de texto | scikit-learn (TF-IDF) |
| Visualización | Plotly |
| Datos | Pandas, JSON |
| Deploy | Streamlit Cloud |

---

## Arquitectura

```
Google News RSS
      │
      ▼
  fetch_rss()          ← BeautifulSoup parsea feeds por fuente
      │
      ▼
dedup_por_fuente()     ← Deduplicación por hash MD5 del título
      │
      ▼
  classify()           ← Groq API · LLaMA 3 · clasificación en lotes
      │
      ▼
  news_db_v5.json      ← Persistencia local con historial de 30 días
      │
      ▼
  Streamlit UI         ← HOY / NOTICIAS / RADAR / ACERCA
```

---

## Instalación local

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/el-reducto.git
cd el-reducto

# Instalar dependencias
pip install -r requirements.txt

# Configurar secrets
# Crear archivo .streamlit/secrets.toml con:
# GROQ_KEY = "tu_api_key_de_groq"

# Ejecutar
streamlit run app.py
```

### Dependencias principales

```
streamlit
requests
pandas
beautifulsoup4
plotly
scikit-learn
groq
```

---

## Configuración

La app requiere una API Key de [Groq](https://console.groq.com) configurada como secret de Streamlit:

```toml
# .streamlit/secrets.toml
GROQ_KEY = "gsk_..."
```

---

## Estructura del proyecto

```
el-reducto/
├── app.py              # Aplicación principal
├── news_db_v5.json     # Base de datos local (generada automáticamente)
├── requirements.txt    # Dependencias
└── .streamlit/
    └── secrets.toml    # API keys (no subir a GitHub)
```

---

## Casos de uso

1. Monitorear conflictos sociales, huelgas y bloqueos en zonas de operación minera
2. Clasificar automáticamente noticias por nivel de riesgo operacional
3. Analizar el impacto específico de una noticia sobre una empresa del sector
4. Detectar semanas de escalada territorial antes de que se agraven
5. Generar reportes de contexto para equipos de relaciones comunitarias

---

## Roadmap

- [ ] Soporte multi-empresa con perfiles personalizados
- [ ] Alertas por correo/WhatsApp ante eventos ALTO riesgo
- [ ] API REST para consumo externo
- [ ] Dashboard ejecutivo con exportación PDF
- [ ] Versión SaaS — **Veta AI**

---

## Autor

**Bryan Perez Aquino**  
Científico de Datos e IA · ISIL, Lima, Perú  
[LinkedIn](https://linkedin.com/in/tu-perfil) · [GitHub](https://github.com/tu-usuario)

---

*Todas las clasificaciones y análisis son generados por IA. No constituyen asesoría profesional.*
