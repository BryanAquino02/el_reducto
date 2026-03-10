import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
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
    page_title="El Reducto — Inteligencia Minera",
    page_icon="⛏️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────── CSS ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,700&family=DM+Sans:wght@300;400;500;600&display=swap');

*, html, body, [class*="css"], .stApp {
    box-sizing: border-box;
    font-family: 'DM Sans', sans-serif !important;
}
.stApp { background: #F5F0E8; }
.block-container {
    padding: 0 !important;
    max-width: 480px !important;
    margin: 0 auto !important;
}
#MainMenu, footer, header, .stDeployButton,
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }

/* ── TOPBAR ── */
.topbar-wrap {
    background: #F5F0E8;
    padding: 18px 24px 0;
    border-bottom: 1px solid #DDD8CE;
    position: sticky;
    top: 0;
    z-index: 100;
}
.topbar-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 14px;
}
.logo-title {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 16px;
    font-weight: 600;
    color: #1B2A4A;
    letter-spacing: -0.02em;
}
.logo-sub {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8.5px;
    font-weight: 300;
    color: #6B7A8D;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 2px;
}
.alert-badge {
    display: flex;
    align-items: center;
    gap: 5px;
    background: #1B2A4A;
    border-radius: 100px;
    padding: 5px 12px;
}
.alert-dot { width: 6px; height: 6px; border-radius: 50%; }
.alert-text {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 0.06em;
}
.nav-rail {
    background: #E8E2D6;
    border-radius: 100px;
    padding: 3px;
    display: flex;
    gap: 2px;
}
.nav-item {
    flex: 1;
    text-align: center;
    padding: 5px 0;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 7px;
    font-weight: 400;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #A8B4C0;
    border-radius: 100px;
}
.nav-item.active {
    font-weight: 600;
    color: #1B2A4A;
    background: #FFFFFF;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}
.gold-sep {
    height: 1px;
    background: linear-gradient(to right, #C9A84C, transparent);
    margin: 0;
}

/* ── SCREEN ── */
.screen { padding: 20px 24px 80px; }

/* ── LABELS ── */
.section-label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8px;
    font-weight: 400;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #6B7A8D;
    margin-bottom: 10px;
}

/* ── FEATURED CARD ── */
.featured-card {
    background: #1B2A4A;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 16px;
}
.featured-meta {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8.5px;
    color: #8A9AB0;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.featured-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 700;
    font-size: 22px;
    line-height: 1.15;
    color: #F5F0E8;
    letter-spacing: -0.02em;
    margin-bottom: 14px;
}
.featured-title em { font-weight: 400; font-style: italic; }
.featured-divider { height: 1px; background: rgba(255,255,255,0.07); margin-bottom: 14px; }
.featured-stats { display: flex; gap: 20px; margin-bottom: 14px; }
.stat-label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 7.5px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #4A5A72;
    margin-bottom: 3px;
}
.stat-value {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11px;
    font-weight: 600;
    color: #F5F0E8;
}
.stat-value.alto { color: #E05252 !important; }
.featured-footer { display: flex; justify-content: space-between; align-items: center; }
.open-link {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 10px;
    color: #C9A84C;
    border-bottom: 1px solid rgba(201,168,76,0.4);
    padding-bottom: 1px;
}

/* ── PILLS ── */
.pill {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 7.5px;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 100px;
    display: inline-block;
    white-space: nowrap;
}
.pill-alto  { border: 1.5px solid #A82020; color: #A82020; }
.pill-medio { border: 1.5px solid #C9A84C; color: #C9A84C; }
.pill-bajo  { border: 1.5px solid #2A6B42; color: #2A6B42; }
.pill-alto-dark  { border: 1.5px solid #E05252; color: #E05252; }
.pill-medio-dark { border: 1.5px solid #D4A94C; color: #D4A94C; }
.pill-bajo-dark  { border: 1.5px solid #4CAF7D; color: #4CAF7D; }

/* ── NEWS ITEM ── */
.news-item {
    display: flex;
    gap: 10px;
    padding: 12px 0;
    border-bottom: 1px solid #DDD8CE;
    align-items: flex-start;
}
.risk-bar { width: 3px; border-radius: 4px; align-self: stretch; flex-shrink: 0; min-height: 32px; }
.risk-bar-alto  { background: #A82020; }
.risk-bar-medio { background: #C9A84C; }
.risk-bar-bajo  { background: #2A6B42; }
.news-source {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8px;
    color: #A8B4C0;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 3px;
}
.news-title {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 12px;
    font-weight: 500;
    color: #1B2A4A;
    line-height: 1.4;
    margin-bottom: 5px;
}

/* ── SKELETON ── */
.skeleton {
    background: linear-gradient(90deg, #E8E2D6 25%, #F0EBE0 50%, #E8E2D6 75%);
    background-size: 200% 100%;
    animation: shimmer 1.4s infinite;
    border-radius: 6px;
}
@keyframes shimmer {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* ── DETAIL ── */
.detail-source {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8.5px;
    color: #A8B4C0;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 10px;
}
.detail-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 700;
    font-size: 28px;
    line-height: 1.1;
    color: #1B2A4A;
    letter-spacing: -0.03em;
    margin-bottom: 14px;
}
.detail-title em { font-weight: 400; font-style: italic; }
.summary-box {
    background: #FFFFFF;
    border-left: 3px solid #1B2A4A;
    border-radius: 0 10px 10px 0;
    padding: 14px 16px;
    margin-bottom: 14px;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 12px;
    color: #3A4A5A;
    line-height: 1.75;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.source-link {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11px;
    color: #1B2A4A;
    border-bottom: 1px solid #1B2A4A;
    padding-bottom: 1px;
    text-decoration: none;
    display: inline-block;
    margin-bottom: 18px;
}
.gold-divider { height: 1px; background: linear-gradient(to right, #C9A84C, transparent); margin: 4px 0 16px; }
.ai-box { background: #1B2A4A; border-radius: 14px; padding: 16px; margin-top: 10px; }
.ai-label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 7.5px;
    color: #4A5A72;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.ai-impact {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8.5px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.ai-impact.negativo { color: #E05252; }
.ai-impact.positivo { color: #4CAF7D; }
.ai-impact.neutro   { color: #8A9AB0; }
.ai-text {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11px;
    color: #A8B4C0;
    line-height: 1.7;
}

/* ── RADAR ── */
.pulse-card {
    background: #1B2A4A;
    border-radius: 18px;
    padding: 22px 20px;
    margin-bottom: 14px;
    text-align: center;
}
.pulse-num {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 58px;
    font-weight: 700;
    color: #F5F0E8;
    line-height: 1;
    letter-spacing: -0.04em;
}
.pulse-label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8px;
    color: #8A9AB0;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-top: 6px;
}
.pulse-diagnosis {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 16px;
    font-style: italic;
    color: #6B7A8D;
    margin-top: 6px;
}
.anomaly-box {
    background: #FDF0F0;
    border: 1.5px solid #A82020;
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 16px;
}
.anomaly-label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 7.5px;
    color: #A82020;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 4px;
}
.anomaly-text {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11px;
    color: #5A2020;
    line-height: 1.55;
}
.stat-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 12px 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    margin-bottom: 8px;
}
.stat-card-label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 7.5px;
    color: #A8B4C0;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 4px;
}
.stat-card-value {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px;
    font-weight: 600;
    color: #1B2A4A;
}

/* ── ACERCA ── */
.acerca-hero-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 38px;
    font-weight: 700;
    color: #1B2A4A;
    line-height: 1.05;
    letter-spacing: -0.04em;
    margin-bottom: 6px;
}
.acerca-hero-sub {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8.5px;
    color: #C9A84C;
    letter-spacing: 0.18em;
    text-transform: uppercase;
}
.feature-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    display: flex;
    gap: 12px;
    align-items: flex-start;
}
.feature-num {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 16px;
    font-style: italic;
    color: #C9A84C;
    min-width: 20px;
    flex-shrink: 0;
}
.feature-text {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11.5px;
    color: #3A4A5A;
    line-height: 1.6;
}
.bryan-name {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 22px;
    font-style: italic;
    color: #1B2A4A;
    margin-bottom: 12px;
}
.bryan-text {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11.5px;
    color: #3A4A5A;
    line-height: 1.8;
    margin-bottom: 10px;
}
.bryan-footer {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8.5px;
    color: #A8B4C0;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 14px;
}

/* ── EMPTY STATE ── */
.empty-state { text-align: center; padding: 40px 20px; }
.empty-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 20px;
    font-style: italic;
    color: #A8B4C0;
    margin-bottom: 6px;
}
.empty-sub {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11px;
    color: #C8D0D8;
}

/* ── INPUTS & BUTTONS ── */
div[data-baseweb="input"] {
    background: #FFFFFF !important;
    border: 1.5px solid #DDD8CE !important;
    border-radius: 100px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
}
div[data-baseweb="input"]:focus-within { border-color: #1B2A4A !important; }
input[type="text"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    color: #1B2A4A !important;
    background: transparent !important;
}
.stButton > button {
    background: transparent !important;
    color: #6B7A8D !important;
    border: 1.5px solid #DDD8CE !important;
    border-radius: 100px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 8.5px !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.4rem 1rem !important;
    box-shadow: none !important;
    transition: all 0.18s !important;
}
.stButton > button:hover {
    background: #1B2A4A !important;
    color: #F5F0E8 !important;
    border-color: #1B2A4A !important;
}
[data-testid="stPlotlyChart"] { border-radius: 14px; overflow: hidden; }
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
GEOLOGIST_PERSONA = """Eres una ingeniera geóloga peruana con 18 años de experiencia en minería metálica,
especializada en gestión de conflictos socioambientales en la sierra norte del Perú.
Conoces profundamente el proyecto Conga de IAMGOLD en Cajamarca, la historia de conflictos con comunidades
campesinas y rondas campesinas, la normativa peruana de concesiones mineras (MINEM), el rol del OEFA
y la Defensoría del Pueblo, y la dinámica entre empresas extractivas y comunidades.
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
            json={"model": "llama-3.1-8b-instant", "messages": messages, "max_tokens": max_tokens},
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
    "mineria+Peru+conflicto",
    "conflictos+mineros+Peru",
    "inversion+minera+Peru",
    "protesta+minera+Peru"
]

def fetch_articles_from_rss(queries, fecha_limite):
    headers = {"User-Agent": "Mozilla/5.0"}
    todos, seen = [], set()
    for q in queries:
        try:
            url  = f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=PE&ceid=PE:es-419"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'xml')
            for item in soup.find_all('item'):
                titulo  = item.find('title').get_text(strip=True) if item.find('title') else ""
                pub_raw = item.find('pubDate').get_text(strip=True) if item.find('pubDate') else ""
                fuente  = item.find('source').get_text(strip=True) if item.find('source') else "Google News"
                link    = item.find('link').get_text(strip=True) if item.find('link') else ""
                if not titulo or titulo in seen:
                    continue
                seen.add(titulo)
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
    titulos           = df['titulo'].tolist()
    todas_clases      = []
    titulos_clasificar = titulos[:60]
    for i in range(0, len(titulos_clasificar), 20):
        lote  = titulos_clasificar[i:i+20]
        lista = "\n".join([f"{j+1}. {x}" for j, x in enumerate(lote)])
        res   = groq_request(
            f'Clasifica estas noticias mineras de Perú. Devuelve SOLO un JSON array sin preamble ni texto extra. '
            f'Valores posibles: "ALTO", "MEDIO", "BAJO". '
            f'ALTO=protesta/violencia/huelga/paro/bloqueo, MEDIO=tensión/comunidades/debate/riesgo/diálogo, BAJO=inversión/neutro/nombramiento/avance. '
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

def extract_keywords(df, n=5):
    stopwords = {
        'de','la','el','en','y','a','los','del','que','con','por','las','un','una',
        'se','es','al','para','su','sus','como','más','no','este','esta','sobre',
        'entre','fue','han','hay','pero','sin','también','desde','hasta','durante',
        'tiene','pueden','nuevo','nuevos','tras','ante','según','así','ser'
    }
    words = []
    for titulo in df['titulo']:
        tokens = re.findall(r'\b[a-záéíóúñ]{4,}\b', titulo.lower())
        words.extend([w for w in tokens if w not in stopwords])
    return Counter(words).most_common(n)

@st.cache_data(ttl=3600)
def fetch_and_process_news():
    db    = load_db()
    today = datetime.now().strftime('%Y-%m-%d')
    if db.get('date') == today and len(db.get('articles', [])) > 0:
        return pd.DataFrame(db['articles'])

    fecha_limite = datetime.now() - timedelta(days=90)
    todos        = fetch_articles_from_rss(QUERIES, fecha_limite)
    if not todos:
        return pd.DataFrame(columns=['titulo', 'fuente', 'fecha', 'fecha_iso', 'url', 'riesgo'])

    df = (
        pd.DataFrame(todos)
        .drop_duplicates(subset='titulo')
        .reset_index(drop=True)
        .sort_values('fecha_iso', ascending=False)
        .reset_index(drop=True)
    )
    df = classify_articles(df)

    history     = db.get('history', [])
    today_data  = df[df['fecha_iso'] == today]
    today_entry = {
        'fecha': today,
        'alto':  int((today_data['riesgo'] == 'ALTO').sum()),
        'medio': int((today_data['riesgo'] == 'MEDIO').sum()),
        'bajo':  int((today_data['riesgo'] == 'BAJO').sum()),
    }
    if not any(h['fecha'] == today for h in history):
        history.append(today_entry)
    history = sorted(history, key=lambda x: x['fecha'])[-30:]

    db.update({'date': today, 'articles': df.to_dict('records'), 'history': history})
    save_db(db)
    return df


# ─────────────────────────────── SESSION STATE ───────────────────────────────
for k, v in {
    'tab': 'HOY', 'selected_article': None, 'prev_tab': 'HOY',
    'feed_filter': 'TODOS', 'ai_summary': {}, 'ai_impact': {}, 'company_input': 'IAMGOLD'
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────── HELPERS ─────────────────────────────────────
def set_tab(t):
    st.session_state.tab = t
    st.session_state.selected_article = None

def open_article(row):
    st.session_state.prev_tab = st.session_state.tab
    st.session_state.selected_article = row
    st.session_state.tab = 'DETALLE'

def pill_html(riesgo, dark=False):
    suffix = "-dark" if dark else ""
    return f'<span class="pill pill-{riesgo.lower()}{suffix}">{riesgo}</span>'

def risk_bar_html(riesgo):
    return f'<div class="risk-bar risk-bar-{riesgo.lower()}"></div>'

def render_news_item(row, key):
    c1, c2 = st.columns([11, 1], gap="small")
    with c1:
        st.markdown(f"""
        <div class="news-item">
            {risk_bar_html(row['riesgo'])}
            <div style="flex:1">
                <div class="news-source">{row['fuente']} · {row['fecha']}</div>
                <div class="news-title">{row['titulo']}</div>
                {pill_html(row['riesgo'])}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        if st.button("→", key=key):
            open_article(row)
            st.rerun()

def skeleton_loader():
    st.markdown("""
    <div style="padding:20px 24px;">
        <div class="skeleton" style="height:10px;width:35%;margin-bottom:16px;"></div>
        <div style="background:#1B2A4A;border-radius:18px;padding:20px;margin-bottom:20px;">
            <div class="skeleton" style="height:8px;width:50%;margin-bottom:12px;background:#2A3A5A;"></div>
            <div class="skeleton" style="height:16px;width:90%;margin-bottom:8px;background:#2A3A5A;"></div>
            <div class="skeleton" style="height:16px;width:70%;margin-bottom:8px;background:#2A3A5A;"></div>
            <div class="skeleton" style="height:16px;width:80%;margin-bottom:16px;background:#2A3A5A;"></div>
            <div class="skeleton" style="height:10px;width:25%;background:#2A3A5A;"></div>
        </div>
        <div class="skeleton" style="height:8px;width:28%;margin-bottom:14px;"></div>
        <div class="skeleton" style="height:44px;width:100%;margin-bottom:8px;border-radius:8px;"></div>
        <div class="skeleton" style="height:44px;width:100%;margin-bottom:8px;border-radius:8px;"></div>
        <div class="skeleton" style="height:44px;width:100%;border-radius:8px;"></div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────── TOPBAR ──────────────────────────────────────
NAV_TABS    = ["HOY", "FEED", "BUSCAR", "RADAR", "ACERCA"]
weekday_es  = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"][datetime.now().weekday()]
today_label = datetime.now().strftime("%-d de %B").capitalize()

def render_topbar(alert_count):
    dot_color = "#A82020" if alert_count >= 3 else "#C9A84C" if alert_count >= 1 else "#2A6B42"
    nav_items_html = "".join([
        f'<div class="nav-item {"active" if (st.session_state.tab == t or (st.session_state.tab == "DETALLE" and st.session_state.prev_tab == t)) else ""}">{t}</div>'
        for t in NAV_TABS
    ])
    st.markdown(f"""
    <div class="topbar-wrap">
        <div class="topbar-row">
            <div>
                <div class="logo-title">El Reducto</div>
                <div class="logo-sub">{weekday_es} {today_label} · Lima</div>
            </div>
            <div class="alert-badge">
                <div class="alert-dot" style="background:{dot_color};"></div>
                <span class="alert-text" style="color:{dot_color};">{alert_count} alertas hoy</span>
            </div>
        </div>
        <div class="nav-rail">{nav_items_html}</div>
    </div>
    <div class="gold-sep"></div>
    """, unsafe_allow_html=True)

    cols = st.columns(len(NAV_TABS), gap="small")
    for col, t in zip(cols, NAV_TABS):
        with col:
            if st.button(t, key=f"nav_{t}", use_container_width=True):
                set_tab(t)
                st.rerun()


# ─────────────────────────────── LOAD DATA ───────────────────────────────────
placeholder = st.empty()
with placeholder:
    skeleton_loader()

df_total = fetch_and_process_news()
placeholder.empty()

today_str   = datetime.now().strftime('%Y-%m-%d')
alert_count = 0
if len(df_total) > 0 and 'fecha_iso' in df_total.columns:
    alert_count = int((df_total[df_total['fecha_iso'] == today_str]['riesgo'] == 'ALTO').sum())

render_topbar(alert_count)


# ─────────────────────────────── HOY ─────────────────────────────────────────
if st.session_state.tab == "HOY":
    st.markdown('<div class="screen">', unsafe_allow_html=True)
    if len(df_total) == 0:
        st.markdown('<div class="empty-state"><div class="empty-title">Sin noticias disponibles</div><div class="empty-sub">No se pudo conectar con las fuentes. Intenta más tarde.</div></div>', unsafe_allow_html=True)
    else:
        top   = df_total.iloc[0]
        words = top['titulo'].split()
        mid   = max(2, len(words) // 2)
        l1, l2 = ' '.join(words[:mid]), ' '.join(words[mid:])

        st.markdown(f"""
        <div class="section-label" style="display:flex;justify-content:space-between;">
            <span>Noticia principal</span>
            <span style="color:#C9A84C;">1 / {min(len(df_total), 8)}</span>
        </div>
        <div class="featured-card">
            <div class="featured-meta">{top['fuente']} · {top['fecha']}</div>
            <div class="featured-title">{l1}<br><em>{l2}</em></div>
            <div class="featured-stats">
                <div><div class="stat-label">Fuente</div><div class="stat-value">{top['fuente']}</div></div>
                <div><div class="stat-label">Riesgo</div><div class="stat-value {'alto' if top['riesgo'] == 'ALTO' else ''}">{top['riesgo']}</div></div>
                <div><div class="stat-label">Fecha</div><div class="stat-value">{top['fecha']}</div></div>
            </div>
            <div class="featured-divider"></div>
            <div class="featured-footer">
                {pill_html(top['riesgo'], dark=True)}
                <span class="open-link">Abrir noticia →</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Abrir noticia principal →", use_container_width=True, key="open_top"):
            open_article(top)
            st.rerun()

        st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="gold-sep" style="margin-bottom:14px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Últimas noticias</div>', unsafe_allow_html=True)
        for i, row in df_total.iloc[1:8].iterrows():
            render_news_item(row, key=f"hoy_{i}")
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────── FEED ────────────────────────────────────────
elif st.session_state.tab == "FEED":
    st.markdown('<div class="screen">', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4 = st.columns(4, gap="small")
    for label, col in [("TODOS", fc1), ("ALTO", fc2), ("MEDIO", fc3), ("BAJO", fc4)]:
        with col:
            if st.button(label, key=f"filter_{label}", use_container_width=True):
                st.session_state.feed_filter = label
                st.rerun()

    active_idx = {"TODOS": 1, "ALTO": 2, "MEDIO": 3, "BAJO": 4}[st.session_state.feed_filter]
    st.markdown(f"""<style>
    div[data-testid="column"]:nth-child({active_idx}) .stButton > button {{
        background: #1B2A4A !important; color: #F5F0E8 !important; border-color: #1B2A4A !important;
    }}</style>""", unsafe_allow_html=True)

    feed = df_total if st.session_state.feed_filter == "TODOS" else df_total[df_total['riesgo'] == st.session_state.feed_filter]
    st.markdown(f'<div class="section-label" style="margin-top:14px;">{len(feed)} noticias · {st.session_state.feed_filter}</div>', unsafe_allow_html=True)

    if len(feed) == 0:
        st.markdown(f'<div class="empty-state"><div class="empty-title">Sin noticias {st.session_state.feed_filter.lower()}</div><div class="empty-sub">No hay noticias con este nivel de riesgo.</div></div>', unsafe_allow_html=True)
    else:
        for i, row in feed.head(40).iterrows():
            render_news_item(row, key=f"feed_{i}")
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────── BUSCAR ──────────────────────────────────────
elif st.session_state.tab == "BUSCAR":
    st.markdown('<div class="screen">', unsafe_allow_html=True)
    query = st.text_input("", placeholder="🔍  Buscar por tema, fuente o empresa...", label_visibility="collapsed")

    if not query:
        keywords = extract_keywords(df_total, 8)
        if keywords:
            st.markdown('<div class="section-label" style="margin-top:10px;">Temas frecuentes</div>', unsafe_allow_html=True)
            kw_html = " ".join([f'<span class="pill pill-medio" style="margin:3px 2px;">{w}</span>' for w, _ in keywords])
            st.markdown(f'<div style="margin-bottom:16px;line-height:2.4;">{kw_html}</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Sugerencias</div>', unsafe_allow_html=True)
        tags = ["IAMGOLD", "Cajamarca", "Conga", "Huelga", "MINEM", "Comunidades"]
        tag_html = " ".join([f'<span class="pill pill-medio" style="margin:3px 2px;">{t}</span>' for t in tags])
        st.markdown(f'<div style="line-height:2.4;">{tag_html}</div>', unsafe_allow_html=True)
    else:
        mask    = df_total['titulo'].str.contains(query, case=False, na=False) | df_total['fuente'].str.contains(query, case=False, na=False)
        results = df_total[mask]
        st.markdown(f'<div class="section-label" style="margin-top:10px;">{len(results)} resultados para "{query}"</div>', unsafe_allow_html=True)
        if len(results) == 0:
            st.markdown(f'<div class="empty-state"><div class="empty-title">Sin resultados para "{query}"</div><div class="empty-sub">Intenta con otra palabra clave.</div></div>', unsafe_allow_html=True)
        else:
            for i, row in results.iterrows():
                render_news_item(row, key=f"search_{i}")
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────── DETALLE ─────────────────────────────────────
elif st.session_state.tab == "DETALLE" and st.session_state.selected_article is not None:
    row    = st.session_state.selected_article
    art_id = str(hash(row['titulo']))

    st.markdown('<div class="screen">', unsafe_allow_html=True)
    if st.button("← Volver", key="back_btn"):
        st.session_state.tab = st.session_state.prev_tab
        st.session_state.selected_article = None
        st.rerun()

    words   = row['titulo'].split()
    mid     = max(2, len(words) // 2)
    l1, l2  = ' '.join(words[:mid]), ' '.join(words[mid:])

    st.markdown(f"""
    <div class="detail-source">{row['fuente']} · {row['fecha']}</div>
    <div class="detail-title">{l1}<br><em>{l2}</em></div>
    {pill_html(row['riesgo'])}
    <div style="height:16px;"></div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="gold-sep" style="margin-bottom:14px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Resumen de la noticia</div>', unsafe_allow_html=True)

    if art_id not in st.session_state.ai_summary:
        with st.spinner("Generando resumen..."):
            resumen = groq_request(
                f'Resume en máximo 3 oraciones claras y directas esta noticia minera peruana, sin preamble: "{row["titulo"]}"',
                system=GEOLOGIST_PERSONA, max_tokens=200
            )
            st.session_state.ai_summary[art_id] = resumen or "No se pudo generar el resumen."

    st.markdown(f'<div class="summary-box">{st.session_state.ai_summary[art_id]}</div>', unsafe_allow_html=True)

    if row.get('url') and str(row['url']).startswith('http'):
        st.markdown(f'<a href="{row["url"]}" target="_blank" class="source-link">Ver fuente original ↗</a>', unsafe_allow_html=True)

    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Análisis de impacto</div>', unsafe_allow_html=True)

    company = st.text_input("", value=st.session_state.company_input, placeholder="Empresa a analizar...", label_visibility="collapsed", key="company_field")
    st.session_state.company_input = company

    if st.button(f"¿Cómo afecta a {company}? →", use_container_width=True, key="analyze_btn"):
        cache_key = f"{art_id}_{company}"
        with st.spinner("Analizando con criterio geológico..."):
            impacto = groq_request(
                f'''Analiza cómo esta noticia puede afectar a {company} en Perú.
Empieza OBLIGATORIAMENTE con "POSITIVO:", "NEGATIVO:" o "NEUTRO:".
Sé técnica y directa. Máximo 4 oraciones.
Noticia: "{row["titulo"]}"
Contexto: "{st.session_state.ai_summary.get(art_id, "")}"''',
                system=GEOLOGIST_PERSONA, max_tokens=300
            )
            st.session_state.ai_impact[f"{art_id}_{company}"] = impacto or "No se pudo generar el análisis."

    cache_key = f"{art_id}_{company}"
    if cache_key in st.session_state.ai_impact:
        texto = st.session_state.ai_impact[cache_key]
        upper = texto.upper()
        if upper.startswith("POSITIVO"):   impact_class, impact_label = "positivo", "▲ IMPACTO POSITIVO"
        elif upper.startswith("NEGATIVO"): impact_class, impact_label = "negativo", "▼ IMPACTO NEGATIVO"
        else:                              impact_class, impact_label = "neutro",   "● IMPACTO NEUTRO"
        st.markdown(f"""
        <div class="ai-box">
            <div class="ai-label">Análisis IA · Especialista en Minería Peruana</div>
            <div class="ai-impact {impact_class}">{impact_label}</div>
            <div class="ai-text">{texto}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────── RADAR ───────────────────────────────────────
elif st.session_state.tab == "RADAR":
    st.markdown('<div class="screen">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Radar de riesgo territorial</div>', unsafe_allow_html=True)

    semana_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    df_semana     = df_total[df_total['fecha_iso'] >= semana_inicio] if len(df_total) > 0 else pd.DataFrame()
    total_semana  = len(df_semana)
    altos_semana  = int((df_semana['riesgo'] == 'ALTO').sum())  if total_semana > 0 else 0
    medios_semana = int((df_semana['riesgo'] == 'MEDIO').sum()) if total_semana > 0 else 0
    ratio_alto    = altos_semana / total_semana if total_semana > 0 else 0
    diagnosis     = "Semana de alta tensión" if ratio_alto > 0.4 else "Semana de tensión moderada" if ratio_alto > 0.2 else "Semana tranquila"

    st.markdown(f"""
    <div class="pulse-card">
        <div class="pulse-num">{altos_semana}</div>
        <div class="pulse-label">Noticias ALTO esta semana</div>
        <div class="pulse-diagnosis">{diagnosis}</div>
    </div>""", unsafe_allow_html=True)

    # Detección de anomalía
    if len(df_total) > 0:
        df_check = df_total.copy()
        df_check['fecha_iso'] = pd.to_datetime(df_check['fecha_iso'])
        fechas_prev  = pd.date_range(end=datetime.now() - timedelta(days=7), periods=14, freq='D')
        prev_altos   = [int((df_check[df_check['fecha_iso'].dt.strftime('%Y-%m-%d') == f.strftime('%Y-%m-%d')]['riesgo'] == 'ALTO').sum()) for f in fechas_prev]
        promedio     = sum(prev_altos) / len(prev_altos) if prev_altos else 0
        if altos_semana > promedio * 1.5 and promedio > 0:
            st.markdown(f"""
            <div class="anomaly-box">
                <div class="anomaly-label">⚠ Anomalía detectada</div>
                <div class="anomaly-text">Actividad ALTO inusualmente alta esta semana ({altos_semana} alertas vs. promedio de {promedio:.1f}).</div>
            </div>""", unsafe_allow_html=True)

    fuente_top = df_semana['fuente'].value_counts().index[0] if total_semana > 0 else "—"
    keywords   = extract_keywords(df_semana, 3) if total_semana > 0 else []
    kw_str     = " · ".join([w for w, _ in keywords]) if keywords else "—"

    c1, c2 = st.columns(2, gap="small")
    with c1:
        st.markdown(f'<div class="stat-card"><div class="stat-card-label">Noticias MEDIO</div><div class="stat-card-value">{medios_semana}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-card"><div class="stat-card-label">Fuente más activa</div><div class="stat-card-value" style="font-size:11px;">{fuente_top}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card"><div class="stat-card-label">Total procesado</div><div class="stat-card-value">{total_semana}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-card"><div class="stat-card-label">Keywords</div><div class="stat-card-value" style="font-size:10px;">{kw_str}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="gold-sep" style="margin:14px 0;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Tendencia · últimos 14 días</div>', unsafe_allow_html=True)

    if len(df_total) > 0:
        df_p = df_total.copy()
        df_p['fecha_iso'] = pd.to_datetime(df_p['fecha_iso'])
        fechas   = pd.date_range(end=datetime.now(), periods=14, freq='D')
        td = [{'fecha': f, 'ALTO': int((df_p[df_p['fecha_iso'].dt.strftime('%Y-%m-%d') == f.strftime('%Y-%m-%d')]['riesgo'] == 'ALTO').sum()),
               'MEDIO': int((df_p[df_p['fecha_iso'].dt.strftime('%Y-%m-%d') == f.strftime('%Y-%m-%d')]['riesgo'] == 'MEDIO').sum()),
               'BAJO':  int((df_p[df_p['fecha_iso'].dt.strftime('%Y-%m-%d') == f.strftime('%Y-%m-%d')]['riesgo'] == 'BAJO').sum())} for f in fechas]
        df_plot = pd.DataFrame(td)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_plot['fecha'], y=df_plot['ALTO'],  name='ALTO',  line=dict(color='#A82020', width=2.5), fill='tozeroy', fillcolor='rgba(168,32,32,0.08)'))
        fig.add_trace(go.Scatter(x=df_plot['fecha'], y=df_plot['MEDIO'], name='MEDIO', line=dict(color='#C9A84C', width=1.8, dash='dot')))
        fig.add_trace(go.Scatter(x=df_plot['fecha'], y=df_plot['BAJO'],  name='BAJO',  line=dict(color='#2A6B42', width=1.5)))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='DM Sans', color='#6B7A8D', size=10),
            margin=dict(l=0, r=0, t=10, b=0), height=200,
            legend=dict(orientation='h', y=-0.35, x=0, font=dict(size=9)),
            xaxis=dict(showgrid=False, tickformat='%d %b', tickfont=dict(size=9), color='#6B7A8D'),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.06)', zeroline=False, tickfont=dict(size=9)),
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────── ACERCA ──────────────────────────────────────
elif st.session_state.tab == "ACERCA":
    st.markdown('<div class="screen">', unsafe_allow_html=True)
    st.markdown("""
    <div style="padding-bottom:20px;border-bottom:1px solid #DDD8CE;margin-bottom:22px;">
        <div class="acerca-hero-title">El<br><em style="font-weight:400;">Reducto</em></div>
        <div class="acerca-hero-sub">Inteligencia Minera · Perú</div>
    </div>
    <div class="section-label">Qué es</div>
    <div style="font-family:'DM Sans',sans-serif;font-size:12.5px;color:#3A4A5A;line-height:1.75;margin-bottom:22px;">
        <strong style="color:#1B2A4A;font-weight:600;">El Reducto</strong> es un monitor de inteligencia ejecutiva
        especializado en el sector minero del Perú. Agrega, clasifica y analiza noticias en tiempo real
        para que puedas tomar decisiones informadas sin perder tiempo filtrando información irrelevante.
    </div>
    <div class="section-label">Para qué sirve</div>
    <div class="feature-card"><div class="feature-num">01</div><div class="feature-text">Monitorear conflictos sociales y riesgos operativos en zonas mineras.</div></div>
    <div class="feature-card"><div class="feature-num">02</div><div class="feature-text">Clasificar noticias automáticamente por nivel de riesgo: ALTO, MEDIO o BAJO.</div></div>
    <div class="feature-card"><div class="feature-num">03</div><div class="feature-text">Analizar el impacto de cada noticia en empresas específicas con criterio de IA especializada en minería peruana.</div></div>
    <div class="feature-card"><div class="feature-num">04</div><div class="feature-text">Detectar anomalías y tendencias de escalada en el territorio mediante análisis de series temporales.</div></div>
    <div style="height:22px;"></div>
    <div class="gold-sep" style="margin-bottom:18px;"></div>
    <div class="bryan-name">Bryan Perez Aquino</div>
    <div class="bryan-text">
        El Reducto fue diseñado y desarrollado por <strong style="color:#1B2A4A;">Bryan Perez Aquino</strong>
        como proyecto de portafolio profesional. Combina scraping de noticias en tiempo real,
        clasificación automática por nivel de riesgo mediante NLP, y análisis de impacto generado por
        inteligencia artificial especializada en minería peruana. Todas las opiniones y análisis de impacto
        que lees en esta aplicación son generados por IA, no por un humano experto.
    </div>
    <div class="bryan-text">
        Construido con Python, Streamlit y modelos de lenguaje de gran escala (LLMs) como parte
        de una formación en Ciencia de Datos con IA.
    </div>
    <div class="bryan-footer">Lima, Perú · 2025</div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
