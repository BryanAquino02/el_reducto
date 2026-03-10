import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import time
import logging
from collections import Counter
import re

logging.basicConfig(level=logging.WARNING)

GROQ_KEY = st.secrets["GROQ_KEY"]
DB_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "news_db_v5.json")

st.set_page_config(
    page_title="El Reducto",
    page_icon="⛏️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────── CSS ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,700&family=DM+Sans:wght@300;400;500&display=swap');

*, html, body, [class*="css"], .stApp {
    box-sizing: border-box;
    font-family: 'DM Sans', sans-serif !important;
}

.stApp { background: #E9E5DC; }

.block-container {
    padding: 0 !important;
    max-width: 420px !important;
    margin: 0 auto !important;
}

#MainMenu, footer, header, .stDeployButton,
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }

/* ── TOPBAR ── */
.topbar {
    padding: 18px 20px 10px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 1px solid #D0CBBf;
    background: #E9E5DC;
    position: sticky;
    top: 0;
    z-index: 100;
}
.logo {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 16px;
    font-weight: 500;
    color: #0E0D0B;
    letter-spacing: -0.02em;
}
.topdate {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 10px;
    font-weight: 300;
    color: #9C9790;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ── SCREEN WRAPPER ── */
.screen { padding: 20px 20px 90px; }

/* ── SECTION LABEL ── */
.section-label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8.5px;
    font-weight: 300;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #9C9790;
    margin-bottom: 10px;
    margin-top: 4px;
}

/* ── FEATURED CARD ── */
.featured-card {
    background: #0E0D0B;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 24px;
}
.featured-org {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 9px;
    color: #6B6660;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 10px;
}
.featured-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 28px;
    font-weight: 700;
    line-height: 1.1;
    color: #F0EDE6;
    letter-spacing: -0.03em;
    margin-bottom: 12px;
}
.featured-title em {
    font-weight: 400;
    font-style: italic;
}
.featured-desc {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 12px;
    color: #7C7870;
    line-height: 1.65;
    margin-bottom: 16px;
}
.featured-meta {
    display: flex;
    gap: 20px;
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid #1E1E1B;
}
.meta-item-label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #5A5750;
    margin-bottom: 2px;
}
.meta-item-value {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 12px;
    font-weight: 500;
    color: #F0EDE6;
}

/* ── PILLS ── */
.pill {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 100px;
    display: inline-block;
}
.pill-alto  { border: 1.5px solid #C0392B; color: #C0392B; background: transparent; }
.pill-medio { border: 1.5px solid #9C9790; color: #9C9790; background: transparent; }
.pill-bajo  { border: 1.5px solid #27AE60; color: #27AE60; background: transparent; }
.pill-dark-alto  { border: 1.5px solid #E74C3C; color: #E74C3C; background: transparent; }
.pill-dark-medio { border: 1.5px solid #7C7870; color: #9C9790; background: transparent; }
.pill-dark-bajo  { border: 1.5px solid #2ECC71; color: #2ECC71; background: transparent; }

/* ── NEWS LIST ITEM ── */
.news-item {
    display: flex;
    gap: 12px;
    padding: 14px 0;
    border-bottom: 1px solid #D0CBBf;
    cursor: pointer;
    align-items: flex-start;
}
.news-item-fuente {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8.5px;
    color: #9C9790;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}
.news-item-title {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px;
    font-weight: 500;
    color: #0E0D0B;
    line-height: 1.35;
    margin-bottom: 6px;
}
.news-item-date {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 9px;
    color: #B0AB9E;
}

/* ── DETAIL VIEW ── */
.detail-back {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 10px;
    color: #9C9790;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
    cursor: pointer;
}
.detail-meta {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 9px;
    color: #9C9790;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 14px;
}
.detail-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 32px;
    font-weight: 700;
    line-height: 1.1;
    color: #0E0D0B;
    letter-spacing: -0.03em;
    margin-bottom: 20px;
}
.detail-title em {
    font-weight: 400;
    font-style: italic;
}
.detail-summary {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13.5px;
    color: #4A4540;
    line-height: 1.75;
    background: #F2EFE8;
    border-left: 3px solid #0E0D0B;
    padding: 14px 16px;
    border-radius: 0 10px 10px 0;
    margin-bottom: 20px;
}
.ai-analysis-box {
    background: #0E0D0B;
    border-radius: 14px;
    padding: 16px;
    margin-top: 12px;
}
.ai-analysis-label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8.5px;
    color: #6B6660;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 10px;
}
.ai-analysis-text {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 12.5px;
    color: #C8C3BA;
    line-height: 1.7;
}
.impact-positivo { color: #2ECC71 !important; }
.impact-negativo { color: #E74C3C !important; }
.impact-neutro   { color: #9C9790 !important; }

/* ── RADAR ── */
.radar-pulse {
    background: #0E0D0B;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 20px;
    text-align: center;
}
.radar-num {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 64px;
    font-weight: 700;
    color: #F0EDE6;
    line-height: 1;
    letter-spacing: -0.04em;
}
.radar-label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 9px;
    color: #6B6660;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-top: 6px;
}
.radar-diagnosis {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 18px;
    font-style: italic;
    color: #C8C3BA;
    margin-top: 8px;
}
.radar-stat {
    background: #F2EFE8;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 8px;
}
.radar-stat-label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8.5px;
    color: #9C9790;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 4px;
}
.radar-stat-value {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px;
    font-weight: 500;
    color: #0E0D0B;
}

/* ── SEARCH ── */
div[data-baseweb="input"] {
    background: #F2EFE8 !important;
    border: 1.5px solid #D0CBBf !important;
    border-radius: 100px !important;
}
div[data-baseweb="input"]:focus-within {
    border-color: #0E0D0B !important;
}
input[type="text"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    color: #0E0D0B !important;
    background: transparent !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: transparent !important;
    color: #6B6660 !important;
    border: 1px solid #D0CBBf !important;
    border-radius: 100px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 9px !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.4rem 0.8rem !important;
    box-shadow: none !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #0E0D0B !important;
    color: #F0EDE6 !important;
    border-color: #0E0D0B !important;
}

/* ── BOTTOM NAV ── */
.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 420px;
    background: #E9E5DC;
    border-top: 1px solid #D0CBBf;
    display: flex;
    padding: 10px 0 18px;
    z-index: 200;
}
.nav-item {
    flex: 1;
    text-align: center;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8.5px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #B0AB9E;
    cursor: pointer;
    padding-top: 4px;
    border-top: 2px solid transparent;
    margin-top: -1px;
}
.nav-item.active {
    color: #0E0D0B;
    border-top: 2px solid #0E0D0B;
}

hr { border: none; border-top: 1px solid #D0CBBf; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────── DB ──────────────────────────────────────────
def init_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w') as f:
            json.dump({'date': '', 'articles': [], 'history': []}, f)

def load_db():
    try:
        return json.load(open(DB_PATH, 'r'))
    except:
        return {'date': '', 'articles': [], 'history': []}

def save_db(data):
    with open(DB_PATH, 'w') as f:
        json.dump(data, f)

init_db()

# ─────────────────────────────── GROQ ────────────────────────────────────────
GEOLOGIST_PERSONA = """Eres la Dra. Carmen Quispe, ingeniera geóloga peruana con 18 años de experiencia 
en minería metálica, especializada en gestión de conflictos socioambientales en la sierra norte del Perú. 
Conoces profundamente el proyecto Conga de IAMGOLD en Cajamarca, la historia de conflictos con comunidades 
campesinas y rondas campesinas, la normativa peruana de concesiones mineras (MINEM), el rol del OEFA y 
la Defensoría del Pueblo, y la dinámica entre empresas extractivas y comunidades. 
Eres directa, técnica y sin rodeos. Usas terminología geológica y minera cuando es relevante."""

def groq_request(prompt, system=None, max_tokens=600):
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": messages,
                "max_tokens": max_tokens
            },
            timeout=20
        )
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        logging.warning(f"Groq error: {e}")
        return None


# ─────────────────────────────── FETCH & CLASSIFY ────────────────────────────
QUERIES = [
    "mineria+Cajamarca+conflicto",
    "mineria+Cajamarca+comunidades",
    "protesta+minera+Cajamarca",
    "IAMGOLD+Peru",
    "mineria+Peru",
    "conflictos+mineros+Peru",
    "inversion+minera+Peru",
    "protesta+minera+Peru"
]

def fetch_articles_from_rss(queries, fecha_limite):
    headers = {"User-Agent": "Mozilla/5.0"}
    todos = []
    for q in queries:
        try:
            url = f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=PE&ceid=PE:es-419"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'xml')
            for item in soup.find_all('item'):
                titulo  = item.find('title').get_text(strip=True) if item.find('title') else ""
                pub_raw = item.find('pubDate').get_text(strip=True) if item.find('pubDate') else ""
                fuente  = item.find('source').get_text(strip=True) if item.find('source') else "Google News"
                link    = item.find('link').get_text(strip=True) if item.find('link') else ""
                try:
                    dt = parsedate_to_datetime(pub_raw).replace(tzinfo=None)
                    if dt < fecha_limite:
                        continue
                    todos.append({
                        "titulo": titulo, "fuente": fuente,
                        "fecha": dt.strftime('%d.%m.%y'),
                        "fecha_iso": dt.strftime('%Y-%m-%d'),
                        "url": link
                    })
                except:
                    continue
        except Exception as e:
            logging.warning(f"Error fetching '{q}': {e}")
    return todos

def classify_articles(df):
    titulos = df['titulo'].tolist()
    todas_clases = []
    titulos_clasificar = titulos[:60]

    for i in range(0, len(titulos_clasificar), 20):
        lote = titulos_clasificar[i:i+20]
        lista = "\n".join([f"{j+1}. {x}" for j, x in enumerate(lote)])
        res = groq_request(
            f'Clasifica estas noticias mineras de Perú. Devuelve SOLO un JSON array sin preamble. '
            f'Valores posibles: "ALTO", "MEDIO", "BAJO". '
            f'ALTO=protesta/violencia/huelga/paro, MEDIO=tensión/comunidades/debate/riesgo, BAJO=inversión/neutro/nombramiento. '
            f'Noticias:\n{lista}\nArray JSON estricto:',
            max_tokens=300
        )
        try:
            if res:
                start = res.find('[')
                end   = res.rfind(']') + 1
                if start != -1 and end > start:
                    todas_clases.extend(json.loads(res[start:end]))
                else:
                    todas_clases.extend(["BAJO"] * len(lote))
            else:
                todas_clases.extend(["BAJO"] * len(lote))
        except:
            todas_clases.extend(["BAJO"] * len(lote))
        time.sleep(0.8)

    todas_clases.extend(["BAJO"] * (len(titulos) - len(titulos_clasificar)))

    if len(todas_clases) >= len(df):
        df['riesgo'] = todas_clases[:len(df)]
    else:
        df['riesgo'] = todas_clases + ["BAJO"] * (len(df) - len(todas_clases))

    def normalize(x):
        x = str(x).upper()
        if 'ALTO' in x:  return 'ALTO'
        if 'MEDIO' in x: return 'MEDIO'
        return 'BAJO'

    df['riesgo'] = df['riesgo'].apply(normalize)
    return df

@st.cache_data(ttl=3600)
def fetch_and_process_news():
    db = load_db()
    today = datetime.now().strftime('%Y-%m-%d')

    if db.get('date') == today and len(db.get('articles', [])) > 0:
        return pd.DataFrame(db['articles'])

    fecha_limite = datetime.now() - timedelta(days=90)
    todos = fetch_articles_from_rss(QUERIES, fecha_limite)

    if not todos:
        st.warning("No se pudieron obtener artículos. Revisa tu conexión.")
        return pd.DataFrame(columns=['titulo', 'fuente', 'fecha', 'fecha_iso', 'url', 'riesgo'])

    df = (
        pd.DataFrame(todos)
        .drop_duplicates(subset='titulo')
        .reset_index(drop=True)
        .sort_values('fecha_iso', ascending=False)
    )

    df = classify_articles(df)

    # Guardar histórico de tendencias
    history = db.get('history', [])
    today_counts = {
        'fecha': today,
        'alto':  int((df[df['fecha_iso'] == today]['riesgo'] == 'ALTO').sum()) if today in df['fecha_iso'].values else 0,
        'medio': int((df[df['fecha_iso'] == today]['riesgo'] == 'MEDIO').sum()) if today in df['fecha_iso'].values else 0,
        'bajo':  int((df[df['fecha_iso'] == today]['riesgo'] == 'BAJO').sum()) if today in df['fecha_iso'].values else 0,
    }
    # Solo agregar si no existe ya hoy
    if not any(h['fecha'] == today for h in history):
        history.append(today_counts)
    history = sorted(history, key=lambda x: x['fecha'])[-30:]  # últimos 30 días

    db['date']     = today
    db['articles'] = df.to_dict('records')
    db['history']  = history
    save_db(db)

    return df


# ─────────────────────────────── SESSION STATE ───────────────────────────────
if 'tab' not in st.session_state:            st.session_state.tab = "HOY"
if 'selected_article' not in st.session_state: st.session_state.selected_article = None
if 'prev_tab' not in st.session_state:       st.session_state.prev_tab = "HOY"
if 'feed_filter' not in st.session_state:    st.session_state.feed_filter = "TODOS"
if 'ai_summary' not in st.session_state:     st.session_state.ai_summary = {}
if 'ai_impact' not in st.session_state:      st.session_state.ai_impact = {}


# ─────────────────────────────── LOAD DATA ───────────────────────────────────
with st.spinner(""):
    df_total = fetch_and_process_news()


# ─────────────────────────────── TOPBAR ──────────────────────────────────────
today_str = datetime.now().strftime("%A %-d de %B").capitalize()
st.markdown(f"""
<div class="topbar">
    <div>
        <div class="logo">El Reducto</div>
        <div class="topdate">{today_str} &nbsp;·&nbsp; Lima</div>
    </div>
    <div style="font-size:9px; font-family:'DM Sans',sans-serif; color:#9C9790; letter-spacing:0.1em; text-transform:uppercase;">
        ⛏️ Inteligencia Minera
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────── HELPERS ─────────────────────────────────────
def set_tab(t):
    st.session_state.tab = t
    st.session_state.selected_article = None

def open_article(row):
    st.session_state.prev_tab = st.session_state.tab
    st.session_state.selected_article = row
    st.session_state.tab = "DETALLE"

def pill_class(riesgo, dark=False):
    prefix = "pill-dark-" if dark else "pill-"
    return f"{prefix}{riesgo.lower()}"

def extract_keywords(df, n=5):
    """Extrae keywords más frecuentes de los títulos (TF-IDF simple)."""
    stopwords = {'de','la','el','en','y','a','los','del','que','con','por','las','un','una','se','es','al','para','su','sus','como','más','no','este','esta','sobre','entre','fue','han','hay','pero','sin','también','desde','hasta','durante','tiene','pueden','nuevo','nuevos'}
    words = []
    for titulo in df['titulo']:
        tokens = re.findall(r'\b[a-záéíóúñ]{4,}\b', titulo.lower())
        words.extend([w for w in tokens if w not in stopwords])
    return Counter(words).most_common(n)


# ─────────────────────────────── SCREENS ─────────────────────────────────────

# ── PANTALLA: HOY ──
if st.session_state.tab == "HOY" and len(df_total) > 0:
    st.markdown('<div class="screen">', unsafe_allow_html=True)

    # Featured card (primera noticia)
    top = df_total.iloc[0]
    words = top['titulo'].split()
    half = len(words) // 2
    title_line1 = ' '.join(words[:half])
    title_line2 = ' '.join(words[half:])

    st.markdown(f"""
    <div class="featured-card">
        <div class="featured-org">{top['fuente']} &nbsp;·&nbsp; {top['fecha']}</div>
        <div class="featured-title">{title_line1}<br><em>{title_line2}</em></div>
        <div class="featured-meta">
            <div>
                <div class="meta-item-label">Fuente</div>
                <div class="meta-item-value">{top['fuente']}</div>
            </div>
            <div>
                <div class="meta-item-label">Riesgo</div>
                <div class="meta-item-value">{top['riesgo']}</div>
            </div>
            <div>
                <div class="meta-item-label">Fecha</div>
                <div class="meta-item-value">{top['fecha']}</div>
            </div>
        </div>
        <span class="pill pill-dark-{top['riesgo'].lower()}">{top['riesgo']}</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Abrir despacho →", key="open_featured"):
        open_article(top)
        st.rerun()

    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Últimos despachos</div>', unsafe_allow_html=True)

    for i, row in df_total.iloc[1:8].iterrows():
        st.markdown(f"""
        <div class="news-item">
            <div style="flex:1">
                <div class="news-item-fuente">{row['fuente']}</div>
                <div class="news-item-title">{row['titulo']}</div>
                <div style="display:flex; gap:6px; align-items:center;">
                    <span class="pill {pill_class(row['riesgo'])}">{row['riesgo']}</span>
                    <span class="news-item-date">{row['fecha']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Ver", key=f"hoy_{i}", use_container_width=False):
            open_article(row)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ── PANTALLA: FEED ──
elif st.session_state.tab == "FEED":
    st.markdown('<div class="screen">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Filtrar por nivel de riesgo</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        if st.button("TODOS", use_container_width=True): st.session_state.feed_filter = "TODOS"; st.rerun()
    with c2:
        if st.button("ALTO",  use_container_width=True): st.session_state.feed_filter = "ALTO"; st.rerun()
    with c3:
        if st.button("MEDIO", use_container_width=True): st.session_state.feed_filter = "MEDIO"; st.rerun()
    with c4:
        if st.button("BAJO",  use_container_width=True): st.session_state.feed_filter = "BAJO"; st.rerun()

    active = {'TODOS':1,'ALTO':2,'MEDIO':3,'BAJO':4}[st.session_state.feed_filter]
    st.markdown(f"""
    <style>
    div[data-testid="column"]:nth-child({active}) .stButton > button {{
        background: #0E0D0B !important; color: #F0EDE6 !important; border-color: #0E0D0B !important;
    }}
    </style>""", unsafe_allow_html=True)

    feed = df_total if st.session_state.feed_filter == "TODOS" else df_total[df_total['riesgo'] == st.session_state.feed_filter]

    st.markdown(f'<div style="margin:12px 0 4px; font-family:\'DM Sans\'; font-size:9px; color:#9C9790; letter-spacing:0.1em; text-transform:uppercase;">{len(feed)} despachos</div>', unsafe_allow_html=True)

    for i, row in feed.head(40).iterrows():
        st.markdown(f"""
        <div class="news-item">
            <div style="flex:1">
                <div class="news-item-fuente">{row['fuente']}</div>
                <div class="news-item-title">{row['titulo']}</div>
                <div style="display:flex; gap:6px; align-items:center; margin-top:4px;">
                    <span class="pill {pill_class(row['riesgo'])}">{row['riesgo']}</span>
                    <span class="news-item-date">{row['fecha']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Ver", key=f"feed_{i}"):
            open_article(row)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ── PANTALLA: BUSCAR ──
elif st.session_state.tab == "BUSCAR":
    st.markdown('<div class="screen">', unsafe_allow_html=True)

    query = st.text_input("", placeholder="🔍  Buscar por tema, fuente, empresa...", label_visibility="collapsed")

    if not query:
        st.markdown('<div class="section-label" style="margin-top:16px;">Temas frecuentes</div>', unsafe_allow_html=True)
        keywords = extract_keywords(df_total, 8)
        kw_html = " ".join([f'<span class="pill pill-medio" style="cursor:pointer; margin:3px; font-size:9px;">{w}</span>' for w,_ in keywords])
        st.markdown(f'<div style="margin-bottom:16px;">{kw_html}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label">Sugerencias rápidas</div>', unsafe_allow_html=True)
        tags = ["IAMGOLD", "Cajamarca", "Conga", "Huelga", "Inversión", "Comunidades"]
        tag_html = " ".join([f'<span class="pill pill-medio" style="cursor:pointer; margin:3px; font-size:9px;">{t}</span>' for t in tags])
        st.markdown(f'<div>{tag_html}</div>', unsafe_allow_html=True)
    else:
        mask = (
            df_total['titulo'].str.contains(query, case=False, na=False) |
            df_total['fuente'].str.contains(query, case=False, na=False)
        )
        results = df_total[mask]
        st.markdown(f'<div style="margin:10px 0; font-family:\'DM Sans\'; font-size:9px; color:#9C9790; letter-spacing:0.1em; text-transform:uppercase;">{len(results)} resultados para "{query}"</div>', unsafe_allow_html=True)

        if len(results) == 0:
            st.markdown('<div style="font-family:\'Cormorant Garamond\',serif; font-size:18px; font-style:italic; color:#B0AB9E; text-align:center; margin-top:40px;">Sin resultados</div>', unsafe_allow_html=True)
        else:
            for i, row in results.iterrows():
                st.markdown(f"""
                <div class="news-item">
                    <div style="flex:1">
                        <div class="news-item-fuente">{row['fuente']}</div>
                        <div class="news-item-title">{row['titulo']}</div>
                        <div style="display:flex; gap:6px; align-items:center; margin-top:4px;">
                            <span class="pill {pill_class(row['riesgo'])}">{row['riesgo']}</span>
                            <span class="news-item-date">{row['fecha']}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Ver", key=f"search_{i}"):
                    open_article(row)
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ── PANTALLA: DETALLE ──
elif st.session_state.tab == "DETALLE" and st.session_state.selected_article is not None:
    row = st.session_state.selected_article
    art_id = str(hash(row['titulo']))

    st.markdown('<div class="screen">', unsafe_allow_html=True)

    if st.button("← Volver", key="back_btn"):
        st.session_state.tab = st.session_state.prev_tab
        st.session_state.selected_article = None
        st.rerun()

    st.markdown(f"""
    <div class="detail-meta">{row['fuente']} &nbsp;·&nbsp; {row['fecha']}</div>
    """, unsafe_allow_html=True)

    words = row['titulo'].split()
    half  = max(2, len(words) // 2)
    l1, l2 = ' '.join(words[:half]), ' '.join(words[half:])
    st.markdown(f'<div class="detail-title">{l1}<br><em>{l2}</em></div>', unsafe_allow_html=True)

    st.markdown(f'<span class="pill {pill_class(row["riesgo"])}">{row["riesgo"]}</span>', unsafe_allow_html=True)
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

    # ── RESUMEN IA ──
    st.markdown('<div class="section-label">Resumen del despacho</div>', unsafe_allow_html=True)

    if art_id not in st.session_state.ai_summary:
        with st.spinner("Generando resumen..."):
            resumen = groq_request(
                f'Resume en máximo 3 oraciones claras y directas esta noticia minera peruana, sin preamble: "{row["titulo"]}"',
                system=GEOLOGIST_PERSONA,
                max_tokens=200
            )
            st.session_state.ai_summary[art_id] = resumen or "No se pudo generar el resumen."

    st.markdown(f'<div class="detail-summary">{st.session_state.ai_summary[art_id]}</div>', unsafe_allow_html=True)

    # ── BOTÓN VER FUENTE ──
    st.markdown(f'<a href="{row["url"]}" target="_blank" style="font-family:\'DM Sans\'; font-size:12px; color:#0E0D0B; border-bottom:1px solid #0E0D0B; padding-bottom:1px; text-decoration:none;">Ver fuente original ↗</a>', unsafe_allow_html=True)
    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)

    # ── ANÁLISIS IAMGOLD ──
    st.markdown('<div class="section-label">Análisis de impacto</div>', unsafe_allow_html=True)

    company_input = st.text_input("", value="IAMGOLD", placeholder="Empresa a analizar...", label_visibility="collapsed", key="company_input")

    if st.button(f"¿Cómo afecta a {company_input}? →", use_container_width=True, key="analyze_btn"):
        cache_key = f"{art_id}_{company_input}"
        with st.spinner("Analizando con criterio geológico..."):
            impacto = groq_request(
                f'''Analiza brevemente cómo esta noticia puede afectar a {company_input} en sus operaciones mineras en Perú.
                Sé específica y técnica. Indica si el impacto es POSITIVO, NEGATIVO o NEUTRO al inicio de tu respuesta.
                Noticia: "{row["titulo"]}"
                Resumen: "{st.session_state.ai_summary.get(art_id, "")}"
                Máximo 4 oraciones.''',
                system=GEOLOGIST_PERSONA,
                max_tokens=300
            )
            st.session_state.ai_impact[cache_key] = impacto or "No se pudo generar el análisis."

    cache_key = f"{art_id}_{company_input}"
    if cache_key in st.session_state.ai_impact:
        texto = st.session_state.ai_impact[cache_key]
        impact_class = ""
        if "POSITIVO" in texto.upper()[:30]:   impact_class = "impact-positivo"
        elif "NEGATIVO" in texto.upper()[:30]:  impact_class = "impact-negativo"
        else:                                    impact_class = "impact-neutro"

        st.markdown(f"""
        <div class="ai-analysis-box">
            <div class="ai-analysis-label">Dra. Carmen Quispe · Ing. Geóloga</div>
            <div class="ai-analysis-text {impact_class}">{texto}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ── PANTALLA: RADAR ──
elif st.session_state.tab == "RADAR":
    st.markdown('<div class="screen">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Radar de riesgo territorial</div>', unsafe_allow_html=True)

    # Métricas de la semana
    semana_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    df_semana = df_total[df_total['fecha_iso'] >= semana_inicio]

    total_semana = len(df_semana)
    altos_semana = int((df_semana['riesgo'] == 'ALTO').sum())
    ratio_alto = altos_semana / total_semana if total_semana > 0 else 0

    if ratio_alto > 0.4:
        diagnosis = "Semana de alta tensión"
    elif ratio_alto > 0.2:
        diagnosis = "Semana de tensión moderada"
    else:
        diagnosis = "Semana de actividad baja"

    st.markdown(f"""
    <div class="radar-pulse">
        <div class="radar-num">{altos_semana}</div>
        <div class="radar-label">Alertas ALTO esta semana</div>
        <div class="radar-diagnosis">{diagnosis}</div>
    </div>
    """, unsafe_allow_html=True)

    # Estadísticas de la semana
    medio_semana = int((df_semana['riesgo'] == 'MEDIO').sum())
    bajo_semana  = int((df_semana['riesgo'] == 'BAJO').sum())
    fuente_top   = df_semana['fuente'].value_counts().index[0] if len(df_semana) > 0 else "—"
    keywords     = extract_keywords(df_semana, 3)
    kw_str       = " · ".join([w for w,_ in keywords]) if keywords else "—"

    c1, c2 = st.columns(2, gap="small")
    with c1:
        st.markdown(f'<div class="radar-stat"><div class="radar-stat-label">Despachos MEDIO</div><div class="radar-stat-value">{medio_semana}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="radar-stat"><div class="radar-stat-label">Fuente más activa</div><div class="radar-stat-value">{fuente_top}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="radar-stat"><div class="radar-stat-label">Despachos BAJO</div><div class="radar-stat-value">{bajo_semana}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="radar-stat"><div class="radar-stat-label">Total procesados</div><div class="radar-stat-value">{total_semana}</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="radar-stat" style="margin-top:0;"><div class="radar-stat-label">Keywords más frecuentes</div><div class="radar-stat-value" style="font-size:12px;">{kw_str}</div></div>', unsafe_allow_html=True)

    # ── GRÁFICO DE TENDENCIA ──
    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Tendencia de riesgo — últimos 14 días</div>', unsafe_allow_html=True)

    # Construir serie temporal desde df_total
    df_trend = df_total.copy()
    df_trend['fecha_iso'] = pd.to_datetime(df_trend['fecha_iso'])
    fechas_range = pd.date_range(end=datetime.now(), periods=14, freq='D')
    trend_data = []
    for fecha in fechas_range:
        f = fecha.strftime('%Y-%m-%d')
        dia = df_trend[df_trend['fecha_iso'].dt.strftime('%Y-%m-%d') == f]
        trend_data.append({
            'fecha': fecha,
            'ALTO':  int((dia['riesgo'] == 'ALTO').sum()),
            'MEDIO': int((dia['riesgo'] == 'MEDIO').sum()),
            'BAJO':  int((dia['riesgo'] == 'BAJO').sum()),
        })

    df_plot = pd.DataFrame(trend_data)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_plot['fecha'], y=df_plot['ALTO'],  name='ALTO',  line=dict(color='#C0392B', width=2), fill='tozeroy', fillcolor='rgba(192,57,43,0.08)'))
    fig.add_trace(go.Scatter(x=df_plot['fecha'], y=df_plot['MEDIO'], name='MEDIO', line=dict(color='#9C9790', width=1.5, dash='dot')))
    fig.add_trace(go.Scatter(x=df_plot['fecha'], y=df_plot['BAJO'],  name='BAJO',  line=dict(color='#27AE60', width=1.5)))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans', color='#9C9790', size=10),
        margin=dict(l=0, r=0, t=10, b=0),
        height=200,
        legend=dict(orientation='h', y=-0.3, x=0, font=dict(size=9)),
        xaxis=dict(showgrid=False, tickformat='%d %b', tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.06)', zeroline=False, tickfont=dict(size=9)),
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ── DETECCIÓN DE ANOMALÍA ──
    promedio_historico = df_plot['ALTO'].mean()
    if altos_semana > promedio_historico * 1.5 and promedio_historico > 0:
        st.markdown(f"""
        <div style="background:#FDF2F0; border:1.5px solid #C0392B; border-radius:12px; padding:14px 16px; margin-top:8px;">
            <div style="font-family:'DM Sans'; font-size:8.5px; color:#C0392B; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:4px;">⚠ Anomalía detectada</div>
            <div style="font-family:'DM Sans'; font-size:12.5px; color:#4A4540;">Actividad ALTO inusualmente alta esta semana ({altos_semana} alertas vs. promedio de {promedio_historico:.1f}).</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────── BOTTOM NAV ──────────────────────────────────
def nav_item(label, key_tab):
    is_active = (st.session_state.tab == key_tab) or (st.session_state.tab == "DETALLE" and st.session_state.prev_tab == key_tab)
    return f'<div class="nav-item {"active" if is_active else ""}" onclick="">{label}</div>'

st.markdown(f"""
<div class="bottom-nav">
    {nav_item("HOY", "HOY")}
    {nav_item("FEED", "FEED")}
    {nav_item("BUSCAR", "BUSCAR")}
    {nav_item("RADAR", "RADAR")}
</div>
""", unsafe_allow_html=True)

# Nav real con botones ocultos dentro de columnas
nav1, nav2, nav3, nav4 = st.columns(4)
with nav1:
    if st.button("HOY",    key="nav_hoy",    use_container_width=True): set_tab("HOY");    st.rerun()
with nav2:
    if st.button("FEED",   key="nav_feed",   use_container_width=True): set_tab("FEED");   st.rerun()
with nav3:
    if st.button("BUSCAR", key="nav_buscar", use_container_width=True): set_tab("BUSCAR"); st.rerun()
with nav4:
    if st.button("RADAR",  key="nav_radar",  use_container_width=True): set_tab("RADAR");  st.rerun()
