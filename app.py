import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import plotly.express as px
import json

NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
GROQ_KEY    = st.secrets["GROQ_KEY"]

st.set_page_config(
    page_title="El Reducto — Risk Monitor",
    page_icon="◆",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────── CSS ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

*, html, body, [class*="css"], .stApp {
    box-sizing: border-box;
    font-family: 'Inter', system-ui, sans-serif !important;
}

/* ── BASE ── */
.stApp {
    background: #f0ede8;
}

.block-container {
    padding: 2rem 1.2rem 5rem !important;
    max-width: 540px !important;
    margin: 0 auto !important;
}

/* ── HIDE CHROME ── */
#MainMenu, footer, header, .stDeployButton,
[data-testid="stToolbar"], [data-testid="stDecoration"] {
    display: none !important;
}

/* ── METRIC CARDS ── */
[data-testid="metric-container"] {
    background: #faf9f6;
    border: 1px solid #e5e0d8;
    border-radius: 14px;
    padding: 1.1rem 1rem 1rem;
}
[data-testid="stMetricLabel"] p {
    font-size: .6rem !important;
    font-weight: 600 !important;
    letter-spacing: .15em !important;
    text-transform: uppercase !important;
    color: #a89f94 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    letter-spacing: -.035em !important;
    color: #1c1c1c !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: #faf9f6;
    color: #555;
    border: 1px solid #ddd8d0;
    border-radius: 100px;
    font-size: .68rem;
    font-weight: 600;
    letter-spacing: .1em;
    text-transform: uppercase;
    padding: .45rem 1rem;
    width: 100%;
    transition: all .15s;
}
.stButton > button:hover, .stButton > button:focus {
    background: #1c1c1c;
    color: #f0ede8;
    border-color: #1c1c1c;
}

/* ── SPINNER ── */
[data-testid="stSpinner"] { color: #a89f94 !important; font-size: .8rem; }

/* ── PLOTLY CHART ── */
[data-testid="stPlotlyChart"] {
    border: 1px solid #e5e0d8;
    border-radius: 14px;
    overflow: hidden;
}

/* ── ALERTS ── */
[data-testid="stAlert"] {
    background: #faf9f6 !important;
    border: 1px solid #ddd8d0 !important;
    border-radius: 12px !important;
    color: #555 !important;
    font-size: .82rem !important;
}

/* ── DIVIDER ── */
hr { border: none; border-top: 1px solid #e5e0d8; margin: 1.8rem 0; }
</style>
""", unsafe_allow_html=True)

# ── SPLASH SCREEN ───────────────────────────────────────────────────────────
if 'splash_shown' not in st.session_state:
    st.markdown("""
    <style>
    .splash-container {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: #f0ede8; z-index: 999999;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        animation: fadeOutSplash 1.2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        animation-delay: 2.5s;
        pointer-events: none;
    }
    @keyframes fadeOutSplash {
        0% { opacity: 1; visibility: visible; }
        100% { opacity: 0; visibility: hidden; }
    }
    .splash-logo {
        font-family: 'Playfair Display', serif;
        font-size: 2.6rem; font-weight: 700; color: #1c1c1c;
        letter-spacing: -0.02em; margin-bottom: 1rem;
        animation: pulseLogo 2s infinite alternate ease-in-out;
    }
    .splash-text {
        font-family: 'Inter', sans-serif; font-size: 0.62rem; font-weight: 600;
        letter-spacing: 0.35em; text-transform: uppercase; color: #a89f94;
    }
    @keyframes pulseLogo {
        0% { opacity: 0.5; transform: scale(0.98); }
        100% { opacity: 1; transform: scale(1); }
    }
    </style>
    <div class="splash-container">
        <div class="splash-logo">El Reducto</div>
        <div class="splash-text">Sincronizando Inteligencia</div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.splash_shown = True


# ─────────────────────────────── HELPERS ────────────────────────────────────
def groq_request(prompt, max_tokens=1000):
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}",
                     "Content-Type": "application/json"},
            json={"model": "llama-3.1-8b-instant",
                  "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": max_tokens},
            timeout=30
        )
        return r.json()['choices'][0]['message']['content']
    except:
        return None


@st.cache_data(ttl=86400)
def obtener_noticias():
    headers = {"User-Agent": "Mozilla/5.0"}
    fecha_limite = datetime.now() - timedelta(days=180)
    queries = [
        "mineria+Cajamarca+conflicto+2025",
        "mineria+Cajamarca+comunidades+2025",
        "protesta+minera+Cajamarca+2025",
        "agua+mineria+Cajamarca+2025",
        "Yanacocha+Cajamarca+2025",
        "IAMGOLD+Peru",
    ]
    todos = []
    for q in queries:
        try:
            url = f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=PE&ceid=PE:es-419"
            soup = BeautifulSoup(
                requests.get(url, headers=headers, timeout=10).text, 'xml')
            for item in soup.find_all('item'):
                titulo   = item.find('title').get_text(strip=True)   if item.find('title')   else ""
                pub_date = item.find('pubDate').get_text(strip=True)  if item.find('pubDate') else ""
                fuente   = item.find('source').get_text(strip=True)   if item.find('source')  else "Google News"
                link     = item.find('link').get_text(strip=True)     if item.find('link')    else ""
                try:
                    dt = parsedate_to_datetime(pub_date).replace(tzinfo=None)
                    if dt < fecha_limite: continue
                    fecha_str = dt.strftime('%d %b %Y')
                    fecha_iso = dt.strftime('%Y-%m-%d')
                except:
                    continue
                if titulo:
                    todos.append({"titulo": titulo, "fuente": fuente,
                                  "fecha": fecha_str, "fecha_iso": fecha_iso, "url": link})
        except:
            continue
    df = pd.DataFrame(todos).drop_duplicates(subset='titulo').reset_index(drop=True)
    return df.sort_values('fecha_iso', ascending=False).reset_index(drop=True)


@st.cache_data(ttl=86400)
def clasificar_noticias(titulos_json):
    titulos, todas = json.loads(titulos_json), []
    for i in range(0, len(titulos), 10):
        lote  = titulos[i:i+10]
        lista = "\n".join([f"{j+1}. {t}" for j, t in enumerate(lote)])
        prompt = f"""Clasifica estas noticias para una empresa minera en Cajamarca Perú.
Responde SOLO con un array JSON. Sin texto extra. Sin markdown.
Valores posibles: "ALTO", "MEDIO", "BAJO"
ALTO: protesta, paro, bloqueo, conflicto, violencia, oposición a minería
MEDIO: minería ilegal, contaminación, tensión, demanda judicial
BAJO: producción, inversión, noticias neutras o positivas
Noticias:\n{lista}\nArray JSON:"""
        res = groq_request(prompt, max_tokens=200)
        try:
            res = res.strip().replace("```json","").replace("```","").strip()
            lc  = json.loads(res[res.find('['):res.rfind(']')+1])
            todas.extend(lc)
        except:
            todas.extend(["BAJO"] * len(lote))
    return todas


# ─────────────────────────────── DATA ───────────────────────────────────────
with st.spinner("Obteniendo noticias..."):
    df = obtener_noticias()

with st.spinner("Clasificando con IA..."):
    clases = clasificar_noticias(json.dumps(df['titulo'].tolist()))
    df['riesgo'] = clases if len(clases) == len(df) else ["BAJO"] * len(df)
    def norm(v):
        v = str(v).upper()
        return 'ALTO' if 'ALTO' in v else ('MEDIO' if 'MEDIO' in v else 'BAJO')
    df['riesgo'] = df['riesgo'].apply(norm)

n_alto = len(df[df['riesgo']=='ALTO'])
nivel_global = 'ALTO' if n_alto > 5 else ('MEDIO' if n_alto > 1 else 'BAJO')

RISK_COLOR  = {'ALTO':'#991b1b', 'MEDIO':'#92400e', 'BAJO':'#166534'}
RISK_BG     = {'ALTO':'#fef2f2', 'MEDIO':'#fffbeb', 'BAJO':'#f0fdf4'}
RISK_BORDER = {'ALTO':'#fca5a5', 'MEDIO':'#fcd34d', 'BAJO':'#86efac'}
STATUS_DOT  = {'ALTO':'#dc2626', 'MEDIO':'#d97706', 'BAJO':'#16a34a'}


# ─────────────────────────────── LAYOUT ─────────────────────────────────────

# ── HEADER ───────────────────────────────────────────────────────────────────
dot = STATUS_DOT[nivel_global]
st.markdown(f"""
<div style="margin-bottom:2rem; padding-bottom:1.5rem; border-bottom:1px solid #e5e0d8;">
  <div style="font-size:.58rem; font-weight:700; letter-spacing:.2em;
              text-transform:uppercase; color:#b5aca1; margin-bottom:.75rem;">
    IAMGOLD Perú &nbsp;·&nbsp; El Reducto
  </div>
  <div style="font-family:'Playfair Display', Georgia, serif;
              font-size:1.9rem; font-weight:700; color:#1c1c1c;
              letter-spacing:-.02em; line-height:1.15; margin-bottom:.85rem;">
    Monitor de<br>Conflictividad
  </div>
  <div style="display:inline-flex; align-items:center; gap:.5rem;
              background:#faf9f6; border:1px solid #e0dbd3;
              border-radius:100px; padding:.4rem .9rem;">
    <div style="width:6px; height:6px; border-radius:50%; background:{dot};
                box-shadow:0 0 6px {dot}88;"></div>
    <span style="font-size:.62rem; font-weight:700; letter-spacing:.13em;
                 text-transform:uppercase; color:#1c1c1c;">
      Riesgo {nivel_global}
    </span>
  </div>
  <div style="font-size:.68rem; color:#b5aca1; margin-top:.6rem;">
    {len(df)} noticias &nbsp;·&nbsp; Últimos 6 meses &nbsp;·&nbsp; Cajamarca
  </div>
</div>
""", unsafe_allow_html=True)


# ── MÉTRICAS ─────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)
c1.metric("Total noticias", len(df))
c2.metric("Alto riesgo", n_alto)

c3, c4 = st.columns(2)
c3.metric("Riesgo medio", len(df[df['riesgo']=='MEDIO']))
c4.metric("Bajo riesgo",  len(df[df['riesgo']=='BAJO']))

st.markdown("<hr>", unsafe_allow_html=True)


# ── GRÁFICO ───────────────────────────────────────────────────────────────────
PLOT = dict(
    paper_bgcolor='#faf9f6', plot_bgcolor='#faf9f6',
    font=dict(family='Inter', color='#a89f94', size=11),
    title_font=dict(family='Inter', color='#a89f94', size=10, weight='normal'),
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=dict(gridcolor='#ede9e4', linecolor='#e5e0d8',
               tickfont=dict(color='#b5aca1', size=10)),
    yaxis=dict(gridcolor='#ede9e4', linecolor='#e5e0d8',
               tickfont=dict(color='#b5aca1', size=10)),
)

# tendencia mensual
df['mes'] = pd.to_datetime(df['fecha_iso']).dt.to_period('M').astype(str)
tend = df.groupby(['mes','riesgo']).size().reset_index(name='n')

fig = px.line(tend, x='mes', y='n', color='riesgo',
              color_discrete_map=RISK_COLOR, markers=True,
              title='TENDENCIA MENSUAL')
fig.update_traces(line=dict(width=2.5))
fig.update_layout(**PLOT, showlegend=True,
    legend=dict(bgcolor='#faf9f6', bordercolor='#e5e0d8',
                font=dict(color='#a89f94', size=10), x=0, y=1.15,
                orientation='h'))
st.plotly_chart(fig, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)


# ── FILTROS ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-size:.58rem; font-weight:700; letter-spacing:.2em;
            text-transform:uppercase; color:#b5aca1; margin-bottom:.8rem;">
  NOTICIAS
</div>
""", unsafe_allow_html=True)

if "filtro" not in st.session_state:
    st.session_state.filtro = "Todos"

b1, b2, b3, b4 = st.columns(4)
with b1:
    if st.button("Todos"):  st.session_state.filtro = "Todos"
with b2:
    if st.button("Alto"):   st.session_state.filtro = "ALTO"
with b3:
    if st.button("Medio"):  st.session_state.filtro = "MEDIO"
with b4:
    if st.button("Bajo"):   st.session_state.filtro = "BAJO"

filtro   = st.session_state.filtro
df_feed  = df[df['riesgo'] == filtro] if filtro != "Todos" else df
df_feed  = df_feed.head(60)

st.markdown("<div style='margin-top:.8rem'></div>", unsafe_allow_html=True)


# ── FEED DE TARJETAS ──────────────────────────────────────────────────────────
for idx, (_, row) in enumerate(df_feed.iterrows()):
    rc  = RISK_COLOR[row['riesgo']]
    rbg = RISK_BG[row['riesgo']]
    rbd = RISK_BORDER[row['riesgo']]

    url_html = (f"<a href='{row['url']}' target='_blank' "
                f"style='color:#b5aca1; font-size:.65rem; font-weight:500; "
                f"text-decoration:none; border-bottom:1px solid #ddd8d0;'>"
                f"Ver noticia →</a>") if row['url'] else ""

    st.markdown(f"""
    <div style="background:#faf9f6; border:1px solid #e5e0d8;
                border-radius:14px; padding:1rem 1.1rem;
                margin-bottom:.6rem;">
      <div style="display:flex; justify-content:space-between;
                  align-items:flex-start; gap:.8rem; margin-bottom:.6rem;">
        <div style="font-size:.88rem; font-weight:500; color:#1c1c1c;
                    line-height:1.45; letter-spacing:-.01em; flex:1;">
          {row['titulo']}
        </div>
        <span style="background:{rbg}; color:{rc}; border:1px solid {rbd};
                     font-size:.55rem; font-weight:700; letter-spacing:.13em;
                     text-transform:uppercase; padding:.25rem .6rem;
                     border-radius:100px; white-space:nowrap; flex-shrink:0;">
          {row['riesgo']}
        </span>
      </div>
      <div style="display:flex; align-items:center; gap:.75rem; flex-wrap:wrap;">
        <span style="font-size:.65rem; color:#b5aca1; font-weight:500;">{row['fuente']}</span>
        <span style="font-size:.65rem; color:#ddd8d0;">·</span>
        <span style="font-size:.65rem; color:#b5aca1;">{row['fecha']}</span>
        {"<span style='font-size:.65rem; color:#ddd8d0;'>·</span> " + url_html if url_html else ""}
      </div>
    </div>
    """, unsafe_allow_html=True)

    if row['riesgo'] == 'ALTO':
        if st.button("Analizar con IA →", key=f"ia_{idx}_{row['titulo'][:12]}"):
            with st.spinner("Analizando..."):
                resp = groq_request(
                    f"""Eres analista de riesgo social para IAMGOLD Perú (proyecto El Reducto, Cajamarca).
En 2-3 oraciones explica por qué esta noticia representa un riesgo. Sé directo y concreto.
Noticia: {row['titulo']} | Fuente: {row['fuente']} | Fecha: {row['fecha']}
Responde SOLO con la explicación."""
                )
                if resp:
                    st.warning(resp)


# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3.5rem; padding-top:1.5rem; border-top:1px solid #e5e0d8;
            text-align:center;">
  <div style="font-size:.58rem; font-weight:600; letter-spacing:.18em;
              text-transform:uppercase; color:#c9c0b7;">
    IAMGOLD Perú &nbsp;·&nbsp; El Reducto &nbsp;·&nbsp; Cajamarca
  </div>
  <div style="font-size:.58rem; color:#d4cfc8; margin-top:.3rem;">
    Powered by Groq LLaMA 3.1 · Google News RSS
  </div>
</div>
""", unsafe_allow_html=True)
