import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import plotly.graph_objects as go
import json, os, time, logging, re, hashlib
from collections import Counter

logging.basicConfig(level=logging.WARNING)
GROQ_KEY = st.secrets["GROQ_KEY"]
DB_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "news_db_v5.json")

st.set_page_config(
    page_title="El Reducto — Inteligencia Minera",
    page_icon="⛏️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ══════════════════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* ── BASE ──────────────────────────────────────────────────────────────────── */
*, html, body, [class*="css"], .stApp {
    box-sizing: border-box !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
.stApp { background: #F7F5F0 !important; }

/* Contenedor principal: padding lateral 20px — todo el contenido lo hereda */
.block-container {
    padding: 0 20px 80px !important;
    max-width: 440px !important;
    margin: 0 auto !important;
}

/* Ocultar chrome de Streamlit */
#MainMenu, footer, header, .stDeployButton,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* Eliminar gaps */
.block-container > div { gap: 0 !important; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }
[data-testid="stVerticalBlock"] > div:empty { display: none !important; }

/* ── TOPBAR ────────────────────────────────────────────────────────────────── */
/* Negative margin para romper el padding del block-container (full-bleed) */
.topbar {
    margin: 0 -20px;
    padding: 20px 20px 14px;
    background: #F7F5F0;
    border-bottom: 1px solid #E5E2DB;
}
.logo-name {
    font-family: 'Playfair Display', serif !important;
    font-size: 20px;
    font-weight: 700;
    color: #0F1F3D;
    line-height: 1;
}
.logo-name em { font-style: italic; font-weight: 400; }
.logo-tagline {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 8px;
    color: #6B7280;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 4px;
}

/* ── NAV ───────────────────────────────────────────────────────────────────── */
/* También full-bleed */
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stBaseButton-secondary"]) {
    gap: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    flex-wrap: nowrap !important;
    overflow: hidden !important;
    margin: 0 -20px !important;
    border-bottom: 1px solid #E5E2DB !important;
}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stBaseButton-secondary"]) > div[data-testid="stColumn"] {
    min-width: 0 !important;
    flex: 1 !important;
    padding: 0 !important;
}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stBaseButton-secondary"]) button {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    color: #9CA3AF !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 7px !important;
    font-weight: 400 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 8px 2px 7px !important;
    width: 100% !important;
    box-shadow: none !important;
    min-height: unset !important;
    height: auto !important;
    line-height: 1.2 !important;
    margin-bottom: -1px !important;
}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stBaseButton-secondary"]) button:hover {
    color: #0F1F3D !important;
    background: transparent !important;
    box-shadow: none !important;
}

/* ── GOLD LINE ─────────────────────────────────────────────────────────────── */
.gold-line {
    height: 1px;
    background: linear-gradient(to right, #B8860B 30%, transparent);
    margin: 18px 0;
}

/* ── SECTION LABEL ─────────────────────────────────────────────────────────── */
.slabel {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 8px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #6B7280;
    margin-bottom: 12px;
    margin-top: 18px;
    display: block;
}

/* ── FEATURED CARD ─────────────────────────────────────────────────────────── */
.fc { background: #0F1F3D; border-radius: 16px; padding: 20px; margin-bottom: 22px; }
.fc-meta { font-family: 'IBM Plex Mono', monospace !important; font-size: 8px; color: #4A5A72; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 10px; }
.fc-title { font-family: 'Playfair Display', serif !important; font-size: 19px; font-weight: 700; color: #F5F0E8; line-height: 1.2; margin-bottom: 16px; }
.fc-title em { font-style: italic; font-weight: 400; }
.fc-sep { height: 1px; background: rgba(255,255,255,0.07); margin-bottom: 14px; }
.fc-stats { display: flex; gap: 20px; margin-bottom: 4px; }
.fc-sl { font-family: 'IBM Plex Mono', monospace !important; font-size: 7px; color: #4A5A72; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 3px; }
.fc-sv { font-family: 'IBM Plex Mono', monospace !important; font-size: 12px; font-weight: 500; color: #F5F0E8; }
.fc-sv.r { color: #F87171 !important; }

/* Botón abrir noticia dentro del fc */
.fc-open-btn > div > button {
    background: #B8860B !important;
    border: none !important;
    border-radius: 100px !important;
    color: #fff !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 7px !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 5px 14px !important;
    box-shadow: none !important;
    width: auto !important;
    min-height: unset !important;
    height: auto !important;
    line-height: 1.4 !important;
    margin-top: 12px !important;
}
.fc-open-btn > div > button:hover { background: #A07609 !important; }

/* ── PILLS ─────────────────────────────────────────────────────────────────── */
.pill {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 7px; font-weight: 500;
    letter-spacing: 0.1em; text-transform: uppercase;
    padding: 3px 9px; border-radius: 4px; display: inline-block;
}
.pa  { background: #FEF2F2; color: #B91C1C; border: 1px solid #FECACA; }
.pm  { background: #FFFBEB; color: #92670A; border: 1px solid #FDE68A; }
.pb  { background: #F0FDF4; color: #166534; border: 1px solid #BBF7D0; }
.pad { background: rgba(255,255,255,0.05); color: #F87171; border: 1px solid rgba(248,113,113,0.3); }
.pmd { background: rgba(255,255,255,0.05); color: #FCD34D; border: 1px solid rgba(252,211,77,0.3); }
.pbd { background: rgba(255,255,255,0.05); color: #4ADE80; border: 1px solid rgba(74,222,128,0.3); }

/* ── NEWS ROW ──────────────────────────────────────────────────────────────── */
.ni-top { display: flex; gap: 12px; padding: 13px 0 6px; align-items: flex-start; }
.ni-divider { height: 1px; background: #E5E2DB; margin-top: 4px; }
.rb { width: 2.5px; border-radius: 4px; align-self: stretch; flex-shrink: 0; min-height: 36px; }
.ns { font-family: 'IBM Plex Mono', monospace !important; font-size: 7.5px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 3px; }
.nt { font-size: 12.5px; font-weight: 500; color: #1C1C1E; line-height: 1.45; }

/* ── BOTONES GLOBALES ──────────────────────────────────────────────────────── */
.stButton > button {
    background: transparent !important;
    color: #6B7280 !important;
    border: 1px solid #E5E2DB !important;
    border-radius: 100px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 7px !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 3px 10px !important;
    min-height: unset !important;
    height: auto !important;
    line-height: 1.4 !important;
    box-shadow: none !important;
    transition: all 0.18s !important;
}
.stButton > button:hover {
    background: #0F1F3D !important;
    color: #F5F0E8 !important;
    border-color: #0F1F3D !important;
}

/* ── FILTER BUTTONS ────────────────────────────────────────────────────────── */
.filter-todos button, .filter-alto button, .filter-medio button, .filter-bajo button {
    border-radius: 5px !important;
    padding: 3px 0 !important;
    font-size: 7px !important;
    min-height: unset !important;
    height: auto !important;
    line-height: 1.3 !important;
}
.filter-todos button { background: #0F1F3D !important; color: #fff !important; border-color: #0F1F3D !important; }
.filter-alto  button { background: #FEF2F2 !important; color: #B91C1C !important; border-color: #FECACA !important; }
.filter-medio button { background: #FFFBEB !important; color: #92670A !important; border-color: #FDE68A !important; }
.filter-bajo  button { background: #F0FDF4 !important; color: #166534 !important; border-color: #BBF7D0 !important; }

/* ── SEARCH ────────────────────────────────────────────────────────────────── */
div[data-baseweb="input"] { background: #fff !important; border: 1.5px solid #E5E2DB !important; border-radius: 10px !important; box-shadow: none !important; }
div[data-baseweb="input"]:focus-within { border-color: #0F1F3D !important; }
input { font-family: 'IBM Plex Sans', sans-serif !important; font-size: 13px !important; color: #0F1F3D !important; background: transparent !important; }

/* ── DETAIL ────────────────────────────────────────────────────────────────── */
.ds { font-family: 'IBM Plex Mono', monospace !important; font-size: 8px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 10px; }
.dt { font-family: 'Playfair Display', serif !important; font-weight: 700; font-size: 26px; line-height: 1.1; color: #0F1F3D; letter-spacing: -0.03em; margin-bottom: 14px; }
.dt em { font-style: italic; font-weight: 400; }
.summary-box { background: #fff; border-left: 3px solid #0F1F3D; border-radius: 0 10px 10px 0; padding: 14px 16px; margin-bottom: 14px; font-size: 12px; color: #374151; line-height: 1.75; }
.source-btn { font-size: 11px; color: #0F1F3D; border-bottom: 1px solid #0F1F3D; padding-bottom: 1px; text-decoration: none; display: inline-block; margin-bottom: 18px; }
.gdiv { height: 1px; background: linear-gradient(to right, #B8860B, transparent); margin: 4px 0 16px; }
.ai-box { background: #0F1F3D; border-radius: 14px; padding: 16px; margin-top: 12px; }
.ai-label { font-family: 'IBM Plex Mono', monospace !important; font-size: 7px; color: #3A4A62; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 8px; }
.ai-impact { font-family: 'IBM Plex Mono', monospace !important; font-size: 8.5px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px; display: flex; align-items: center; gap: 7px; }
.ai-neg { color: #F87171; } .ai-pos { color: #4ADE80; } .ai-neu { color: #8A9AB0; }
.ai-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; display: inline-block; }
.ai-dot-neg { background: #F87171; } .ai-dot-pos { background: #4ADE80; } .ai-dot-neu { background: #8A9AB0; }
.ai-text { font-size: 11px; color: #8A9AB0; line-height: 1.75; }

/* ── RADAR ─────────────────────────────────────────────────────────────────── */
.pulse-card { background: #0F1F3D; border-radius: 16px; padding: 28px 20px; margin-bottom: 18px; text-align: center; }
.pulse-num { font-family: 'Playfair Display', serif !important; font-size: 72px; font-weight: 700; color: #F5F0E8; line-height: 1; letter-spacing: -0.04em; }
.pulse-lbl { font-family: 'IBM Plex Mono', monospace !important; font-size: 8px; color: #4A5A72; letter-spacing: 0.2em; text-transform: uppercase; margin-top: 10px; }
.pulse-diag { font-family: 'Playfair Display', serif !important; font-size: 14px; font-style: italic; color: #6B7A8D; margin-top: 8px; }
.anomaly { background: #FEF2F2; border: 1.5px solid #B91C1C; border-radius: 12px; padding: 14px 16px; margin-bottom: 18px; }
.anomaly-lbl { font-family: 'IBM Plex Mono', monospace !important; font-size: 7.5px; color: #B91C1C; letter-spacing: 0.15em; text-transform: uppercase; font-weight: 700; margin-bottom: 6px; }
.anomaly-txt { font-size: 11px; color: #5A2020; line-height: 1.65; }
.stat-card { background: #fff; border-radius: 10px; padding: 14px; border: 1px solid #E5E2DB; margin-bottom: 10px; }
.stat-lbl { font-family: 'IBM Plex Mono', monospace !important; font-size: 7px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 6px; }
.stat-val { font-family: 'IBM Plex Mono', monospace !important; font-size: 22px; font-weight: 500; color: #0F1F3D; }

/* ── ACERCA ────────────────────────────────────────────────────────────────── */
.hero-title { font-family: 'Playfair Display', serif !important; font-size: 40px; font-weight: 700; color: #0F1F3D; line-height: 1; letter-spacing: -0.03em; margin-bottom: 6px; }
.hero-title em { font-style: italic; font-weight: 400; }
.hero-sub { font-family: 'IBM Plex Mono', monospace !important; font-size: 8px; color: #B8860B; letter-spacing: 0.2em; text-transform: uppercase; }
.qes-text { font-size: 12px; color: #374151; line-height: 1.8; margin-bottom: 20px; }
.feat-item { display: flex; gap: 14px; align-items: flex-start; padding: 12px 0; border-bottom: 1px solid #E5E2DB; }
.feat-num { font-family: 'Playfair Display', serif !important; font-size: 16px; font-style: italic; color: #B8860B; min-width: 22px; flex-shrink: 0; line-height: 1.5; }
.feat-txt { font-size: 11.5px; color: #374151; line-height: 1.7; }
.creator-card { background: #0F1F3D; border-radius: 16px; padding: 22px; margin-bottom: 20px; }
.creator-name { font-family: 'Playfair Display', serif !important; font-size: 22px; font-style: italic; color: #F5F0E8; margin-bottom: 6px; }
.creator-role { font-family: 'IBM Plex Mono', monospace !important; font-size: 8px; color: #B8860B; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 16px; }
.creator-sep { height: 1px; background: rgba(255,255,255,0.07); margin-bottom: 16px; }
.creator-txt { font-size: 11.5px; color: #8A9AB0; line-height: 1.9; }
.skill-card { background: #fff; border-radius: 12px; padding: 14px; margin-bottom: 8px; border: 1px solid #E5E2DB; }
.skill-icon { font-size: 18px; margin-bottom: 7px; }
.skill-name { font-size: 10.5px; font-weight: 600; color: #0F1F3D; margin-bottom: 4px; }
.skill-desc { font-size: 9.5px; color: #6B7280; line-height: 1.6; }
.acerca-footer { text-align: center; padding-top: 20px; margin-top: 8px; border-top: 1px solid #E5E2DB; }
.acerca-footer-txt { font-family: 'IBM Plex Mono', monospace !important; font-size: 8px; color: #9CA3AF; letter-spacing: 0.14em; text-transform: uppercase; }
.acerca-footer-note { font-size: 8px; color: #D1D5DB; margin-top: 6px; }

/* ── SKELETON ──────────────────────────────────────────────────────────────── */
.sk { background: linear-gradient(90deg,#EAE7E0 25%,#F2EFE8 50%,#EAE7E0 75%); background-size:200% 100%; animation:sh 1.4s infinite; border-radius:6px; }
@keyframes sh { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* ── PLOTLY ────────────────────────────────────────────────────────────────── */
[data-testid="stPlotlyChart"] { border-radius: 14px; overflow: hidden; }

/* ── EMPTY ─────────────────────────────────────────────────────────────────── */
.empty { text-align:center; padding:40px 0; }
.empty-t { font-family:'Playfair Display',serif !important; font-size:20px; font-style:italic; color:#9CA3AF; margin-bottom:6px; }
.empty-s { font-size:11px; color:#D1D5DB; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  DB
# ══════════════════════════════════════════════════════════════════════════════
def init_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w') as f:
            json.dump({'date': '', 'articles': [], 'history': []}, f)

def load_db():
    try:
        with open(DB_PATH) as f: return json.load(f)
    except:
        return {'date': '', 'articles': [], 'history': []}

def save_db(data):
    with open(DB_PATH, 'w') as f: json.dump(data, f)

init_db()


# ══════════════════════════════════════════════════════════════════════════════
#  GROQ
# ══════════════════════════════════════════════════════════════════════════════
GEO_PERSONA = """Eres una ingeniera geóloga peruana con 18 años de experiencia en minería metálica,
especializada en conflictos socioambientales en la sierra norte del Perú.
Conoces el proyecto Conga de IAMGOLD en Cajamarca, la normativa del MINEM, el OEFA
y la dinámica entre empresas extractivas y comunidades campesinas. Eres directa y técnica."""

def groq_call(prompt, system=None, max_tokens=600):
    try:
        msgs = []
        if system: msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.1-8b-instant", "messages": msgs, "max_tokens": max_tokens},
            timeout=20
        )
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        logging.warning(f"Groq: {e}"); return None


# ══════════════════════════════════════════════════════════════════════════════
#  FETCH & CLASSIFY
# ══════════════════════════════════════════════════════════════════════════════
QUERIES = [
    "mineria+Cajamarca+conflicto", "mineria+Cajamarca+comunidades",
    "protesta+minera+Cajamarca",   "huelga+minera+Cajamarca",
    "Conga+mina+Cajamarca",        "rondas+campesinas+mineria",
    "IAMGOLD+Peru",                "IAMGOLD+Cajamarca",
    "Yanacocha+Cajamarca",         "minera+Buenaventura+Peru",
    "Southern+Copper+Peru",        "conflictos+mineros+Peru",
    "paro+minero+Peru",            "bloqueo+minero+Peru",
    "comunidades+mineria+Peru",    "conflicto+socioambiental+Peru",
    "MINEM+Peru+mineria",          "OEFA+fiscalizacion+mineria",
    "inversion+minera+Peru",       "concesion+minera+Peru",
    "mineria+La+Libertad+Peru",    "mineria+Ancash+Peru",
    "mineria+Apurimac+Peru",       "mineria+Arequipa+Peru",
]

FUENTE_RANK = {}
for _f in ["rpp","la republica","la república","peru21"]: FUENTE_RANK[_f] = 1
for _f in ["el comercio","gestion","gestión","correo"]:   FUENTE_RANK[_f] = 2
for _f in ["reuters","afp","ap news","associated press"]: FUENTE_RANK[_f] = 3
for _f in ["proactivo","mining","mineria","andina"]:       FUENTE_RANK[_f] = 4

def fuente_rank(nombre):
    n = nombre.lower()
    for k, v in FUENTE_RANK.items():
        if k in n: return v
    return 5

def limpiar_titulo(t):
    t = re.sub(r'\s*[\-\u2013\u2014|]\s*[^\-\u2013\u2014|]{1,60}$', '', t)
    return re.sub(r'\s+', ' ', t).strip().lower()

def dedup_por_fuente(articulos):
    grupos = {}
    for art in articulos:
        clave = limpiar_titulo(art['titulo'])
        if clave not in grupos or fuente_rank(art['fuente']) < fuente_rank(grupos[clave]['fuente']):
            grupos[clave] = art
    return list(grupos.values())

def fetch_rss(fecha_limite):
    headers = {"User-Agent": "Mozilla/5.0"}
    todos, seen = [], set()
    for q in QUERIES:
        try:
            r = requests.get(
                f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=PE&ceid=PE:es-419",
                headers=headers, timeout=10
            )
            r.raise_for_status()
            for item in BeautifulSoup(r.text, 'xml').find_all('item'):
                titulo  = item.find('title').get_text(strip=True)  if item.find('title')   else ""
                pub_raw = item.find('pubDate').get_text(strip=True) if item.find('pubDate') else ""
                fuente  = item.find('source').get_text(strip=True)  if item.find('source')  else "Google News"
                link    = item.find('link').get_text(strip=True)    if item.find('link')    else ""
                if not titulo or titulo in seen: continue
                seen.add(titulo)
                try:
                    dt = parsedate_to_datetime(pub_raw).replace(tzinfo=None)
                    if dt < fecha_limite: continue
                    todos.append({"titulo": titulo, "fuente": fuente,
                                  "fecha": dt.strftime('%d.%m.%y'),
                                  "fecha_iso": dt.strftime('%Y-%m-%d'), "url": link})
                except: continue
        except Exception as e: logging.warning(f"RSS '{q}': {e}")
    return todos

def classify(df):
    df = df.copy()
    todos = []
    BATCH = 8
    for i in range(0, min(len(df), 200), BATCH):
        lote  = df['titulo'].tolist()[i:i+BATCH]
        lista = "\n".join([f"{j+1}. {x}" for j, x in enumerate(lote)])
        prompt = (
            f'Eres un analista de riesgo minero en Perú. '
            f'Clasifica cada noticia con exactamente una etiqueta:\n'
            f'- ALTO: huelga, paro, bloqueo, protesta violenta, derrame, accidente grave, muertos\n'
            f'- MEDIO: tensión social, diálogo en riesgo, denuncia ambiental, negociación fallida\n'
            f'- BAJO: inversión, producción, acuerdo firmado, exploración, precio de metales\n\n'
            f'Noticias:\n{lista}\n\n'
            f'Responde ÚNICAMENTE con un JSON array de {len(lote)} strings, en orden. '
            f'Ejemplo: ["ALTO","BAJO","MEDIO"]\nJSON:'
        )
        res = None
        for _ in range(2):
            res = groq_call(prompt, max_tokens=60 + len(lote) * 10)
            if res: break
            time.sleep(1.5)
        try:
            if res:
                s, e = res.find('['), res.rfind(']') + 1
                if s != -1 and e > s:
                    parsed = json.loads(res[s:e])
                    todos.extend(parsed[:len(lote)])
                    todos.extend(["BAJO"] * max(0, len(lote) - len(parsed)))
                else:
                    todos.extend(["BAJO"] * len(lote))
            else:
                todos.extend(["BAJO"] * len(lote))
        except:
            todos.extend(["BAJO"] * len(lote))
        time.sleep(0.8)
    todos.extend(["BAJO"] * (len(df) - len(todos)))
    df['riesgo'] = [str(x).upper() for x in todos[:len(df)]]
    def norm(x):
        if 'ALTO' in x:  return 'ALTO'
        if 'MEDIO' in x: return 'MEDIO'
        return 'BAJO'
    df['riesgo'] = df['riesgo'].apply(norm)
    return df

def get_keywords(df, n=6):
    sw = {'de','la','el','en','y','a','los','del','que','con','por','las','un','una','se','es',
          'al','para','su','sus','como','más','no','este','esta','sobre','entre','fue','han',
          'hay','pero','sin','también','desde','hasta','durante','tiene','pueden','nuevo',
          'nuevos','tras','ante','según','así','ser'}
    words = []
    for t in df['titulo']:
        words.extend([w for w in re.findall(r'\b[a-záéíóúñ]{4,}\b', t.lower()) if w not in sw])
    return Counter(words).most_common(n)

@st.cache_data(ttl=3600)
def get_news():
    db    = load_db()
    today = datetime.now().strftime('%Y-%m-%d')
    if db.get('date') == today and db.get('articles'):
        return pd.DataFrame(db['articles'])
    todos = fetch_rss(datetime.now() - timedelta(days=90))
    if not todos:
        return pd.DataFrame(columns=['titulo', 'fuente', 'fecha', 'fecha_iso', 'url', 'riesgo'])
    todos = dedup_por_fuente(todos)
    df = (pd.DataFrame(todos).sort_values('fecha_iso', ascending=False).reset_index(drop=True))
    clasificados = {
        hashlib.md5(a['titulo'].encode()).hexdigest()[:12]: a.get('riesgo', '')
        for a in db.get('articles', [])
        if a.get('riesgo') in ('ALTO', 'MEDIO', 'BAJO')
    }
    ids_df = df['titulo'].apply(lambda t: hashlib.md5(t.encode()).hexdigest()[:12])
    sin_clasificar = df[~ids_df.isin(clasificados)].copy()
    if len(sin_clasificar) > 0:
        sin_clasificar = classify(sin_clasificar)
        for _, fila in sin_clasificar.iterrows():
            aid = hashlib.md5(fila['titulo'].encode()).hexdigest()[:12]
            clasificados[aid] = fila['riesgo']
    df['riesgo'] = ids_df.apply(lambda aid: clasificados.get(aid, 'BAJO'))
    history = db.get('history', [])
    td      = df[df['fecha_iso'] == today]
    entry   = {'fecha': today,
               'alto':  int((td['riesgo'] == 'ALTO').sum()),
               'medio': int((td['riesgo'] == 'MEDIO').sum()),
               'bajo':  int((td['riesgo'] == 'BAJO').sum())}
    if not any(h['fecha'] == today for h in history): history.append(entry)
    history = sorted(history, key=lambda x: x['fecha'])[-30:]
    db.update({'date': today, 'articles': df.to_dict('records'), 'history': history})
    save_db(db)
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for k, v in {'tab': 'HOY', 'prev_tab': 'HOY', 'sel': None,
             'summaries': {}, 'impacts': {}, 'company': 'IAMGOLD',
             'noticias_filtro': 'TODOS'}.items():
    if k not in st.session_state: st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def open_art(row):
    st.session_state.prev_tab = st.session_state.tab
    st.session_state.sel = row
    st.session_state.tab = 'DETALLE'

def pill(r, dark=False):
    cls = {'ALTO': 'pad', 'MEDIO': 'pmd', 'BAJO': 'pbd'} if dark \
     else {'ALTO': 'pa',  'MEDIO': 'pm',  'BAJO': 'pb'}
    return f'<span class="pill {cls.get(r, "pb")}">{r}</span>'

def news_row(row, key):
    rc = {"ALTO": "#B91C1C", "MEDIO": "#92670A", "BAJO": "#166534"}.get(row["riesgo"], "#166534")
    pc = {"ALTO": "pa", "MEDIO": "pm", "BAJO": "pb"}.get(row["riesgo"], "pb")
    st.markdown(
        f'<div class="ni-top">'
        f'<div class="rb" style="background:{rc};"></div>'
        f'<div style="flex:1;">'
        f'<div class="ns">{row["fuente"]} &middot; {row["fecha"]}</div>'
        f'<div class="nt">{row["titulo"]}</div>'
        f'</div></div>',
        unsafe_allow_html=True
    )
    c1, c2 = st.columns([1, 2], gap="small")
    with c1:
        st.markdown(f'<div style="padding:4px 0;"><span class="pill {pc}">{row["riesgo"]}</span></div>',
                    unsafe_allow_html=True)
    with c2:
        if st.button("Ver noticia →", key=key, use_container_width=False):
            open_art(row); st.rerun()
    st.markdown('<div class="ni-divider"></div>', unsafe_allow_html=True)

def skeleton():
    st.markdown("""
    <div style="padding:20px 0;">
      <div style="background:#0F1F3D;border-radius:16px;padding:20px;margin-bottom:18px;">
        <div class="sk" style="height:8px;width:50%;margin-bottom:14px;background:#1A2F52;"></div>
        <div class="sk" style="height:16px;width:90%;margin-bottom:8px;background:#1A2F52;"></div>
        <div class="sk" style="height:16px;width:70%;margin-bottom:18px;background:#1A2F52;"></div>
        <div class="sk" style="height:10px;width:30%;background:#1A2F52;"></div>
      </div>
      <div class="sk" style="height:8px;width:28%;margin-bottom:14px;"></div>
      <div class="sk" style="height:50px;width:100%;margin-bottom:10px;border-radius:8px;"></div>
      <div class="sk" style="height:50px;width:100%;margin-bottom:10px;border-radius:8px;"></div>
      <div class="sk" style="height:50px;width:100%;border-radius:8px;"></div>
    </div>""", unsafe_allow_html=True)

def split_title(titulo):
    words = titulo.split()
    mid   = max(3, len(words) // 2)
    return ' '.join(words[:mid]), ' '.join(words[mid:])


# ══════════════════════════════════════════════════════════════════════════════
#  LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
ph = st.empty()
with ph: skeleton()
df = get_news()
ph.empty()

today_str = datetime.now().strftime('%Y-%m-%d')


# ══════════════════════════════════════════════════════════════════════════════
#  TOPBAR + NAV
# ══════════════════════════════════════════════════════════════════════════════
NAV = ["HOY", "NOTICIAS", "RADAR", "ACERCA"]

st.markdown("""
<div class="topbar">
  <div class="logo-name">El <em>Reducto</em></div>
  <div class="logo-tagline">Inteligencia Minera · Perú</div>
</div>""", unsafe_allow_html=True)

current = st.session_state.prev_tab if st.session_state.tab == "DETALLE" else st.session_state.tab

nav_cols = st.columns(4, gap="small")
for col, t in zip(nav_cols, NAV):
    with col:
        is_active = (current == t)
        if st.button(t, key=f"nav_{'a' if is_active else 'i'}_{t}", use_container_width=False):
            if t != current:
                st.session_state.tab = t
                st.session_state.sel = None
                st.rerun()

# Underline en tab activo
nav_idx = (NAV.index(current) + 1) if current in NAV else 1
st.markdown(f"""<style>
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stBaseButton-secondary"])
  > div[data-testid="stColumn"]:nth-child({nav_idx}) button {{
    color: #0F1F3D !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #B8860B !important;
}}
</style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN: HOY
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.tab == "HOY":

    if len(df) == 0:
        st.markdown('<div class="empty"><div class="empty-t">Sin noticias disponibles</div>'
                    '<div class="empty-s">No se pudo conectar con las fuentes.</div></div>',
                    unsafe_allow_html=True)
    else:
        top = df.iloc[0]
        l1, l2 = split_title(top['titulo'])
        riesgo_color = "r" if top['riesgo'] == "ALTO" else ""

        st.markdown(f"""
        <div class="slabel" style="margin-top:18px;">Noticia principal</div>
        <div class="fc">
          <div class="fc-meta">{top['fuente']} · {top['fecha']}</div>
          <div class="fc-title">{l1}<br><em>{l2}</em></div>
          <div class="fc-sep"></div>
          <div class="fc-stats">
            <div><div class="fc-sl">Fuente</div><div class="fc-sv">{top['fuente']}</div></div>
            <div><div class="fc-sl">Riesgo</div><div class="fc-sv {riesgo_color}">{top['riesgo']}</div></div>
            <div><div class="fc-sl">Fecha</div><div class="fc-sv">{top['fecha']}</div></div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="fc-open-btn">', unsafe_allow_html=True)
        if st.button("Abrir noticia →", use_container_width=False, key="open_top"):
            open_art(top); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)
        st.markdown('<div class="slabel">Últimas noticias</div>', unsafe_allow_html=True)

        for i, row in df.iloc[1:8].iterrows():
            news_row(row, f"h{i}")


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN: NOTICIAS (búsqueda + filtros + listado completo)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "NOTICIAS":

    st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)

    # Buscador
    q = st.text_input("Buscar noticias", placeholder="🔍  Buscar por tema, fuente o empresa...",
                      label_visibility="collapsed")

    # Filtros: 4 botones nativos
    ff = st.session_state.noticias_filtro
    opciones = ["TODOS", "ALTO", "MEDIO", "BAJO"]
    estilos  = ["filter-todos", "filter-alto", "filter-medio", "filter-bajo"]
    fcols = st.columns(4, gap="small")
    for col, opt, cls in zip(fcols, opciones, estilos):
        with col:
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            if st.button(opt, key=f"fn_{opt}", use_container_width=False):
                st.session_state.noticias_filtro = opt
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Aplicar filtros
    feed = df.copy() if len(df) > 0 else pd.DataFrame()
    if q and len(feed) > 0:
        mask = (feed['titulo'].str.contains(q, case=False, na=False) |
                feed['fuente'].str.contains(q, case=False, na=False))
        feed = feed[mask]
    if ff != "TODOS" and len(feed) > 0:
        feed = feed[feed['riesgo'] == ff]

    label_filtro = f' · {ff.lower()}' if ff != 'TODOS' else ''
    label_query  = f' · "{q}"' if q else ''
    st.markdown(
        f'<div class="slabel" style="margin-top:14px;">'
        f'{len(feed)} noticias{label_filtro}{label_query}</div>',
        unsafe_allow_html=True
    )

    if len(feed) == 0:
        st.markdown('<div class="empty"><div class="empty-t">Sin resultados</div>'
                    '<div class="empty-s">Prueba con otro término o filtro.</div></div>',
                    unsafe_allow_html=True)
    else:
        for i, row in feed.head(50).iterrows():
            news_row(row, f"n{i}")


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN: DETALLE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "DETALLE" and st.session_state.sel is not None:
    row    = st.session_state.sel
    art_id = hashlib.md5(row['titulo'].encode()).hexdigest()[:12]

    st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)

    if st.button("← Volver", key="back"):
        st.session_state.tab = st.session_state.prev_tab
        st.session_state.sel = None
        st.rerun()

    l1, l2 = split_title(row['titulo'])
    st.markdown(f"""
    <div class="ds" style="margin-top:14px;">{row['fuente']} · {row['fecha']}</div>
    <div class="dt">{l1}<br><em>{l2}</em></div>
    {pill(row['riesgo'])}
    <div style="height:16px;"></div>""", unsafe_allow_html=True)

    st.markdown('<div class="gdiv"></div>', unsafe_allow_html=True)
    st.markdown('<div class="slabel">Resumen de la noticia</div>', unsafe_allow_html=True)

    if art_id not in st.session_state.summaries:
        with st.spinner("Generando resumen..."):
            r = groq_call(
                f'Resume en 3 oraciones claras esta noticia minera peruana, sin preamble: "{row["titulo"]}"',
                system=GEO_PERSONA, max_tokens=200
            )
            st.session_state.summaries[art_id] = r or "No se pudo generar el resumen."

    st.markdown(f'<div class="summary-box">{st.session_state.summaries[art_id]}</div>',
                unsafe_allow_html=True)

    if row.get('url') and str(row['url']).startswith('http'):
        st.markdown(f'<a href="{row["url"]}" target="_blank" class="source-btn">Ver fuente original ↗</a>',
                    unsafe_allow_html=True)

    st.markdown('<div class="gdiv"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="slabel">Impacto para {st.session_state.company}</div>',
                unsafe_allow_html=True)

    ck = f"{art_id}_{st.session_state.company}"
    if ck not in st.session_state.impacts:
        with st.spinner("Analizando impacto..."):
            imp = groq_call(
                f'Eres especialista en el proyecto Conga de {st.session_state.company} en Cajamarca, Perú. '
                f'Analiza el impacto DIRECTO de esta noticia sobre {st.session_state.company}. '
                f'Si no involucra directamente, explica si podría afectarle indirectamente. '
                f'Empieza con una palabra: POSITIVO, NEGATIVO o NEUTRO, seguido de dos puntos. Máx 4 oraciones.\n'
                f'Noticia: "{row["titulo"]}"',
                system=GEO_PERSONA, max_tokens=300
            )
            st.session_state.impacts[ck] = imp or "No se pudo generar el análisis."

    txt = st.session_state.impacts[ck]
    u   = txt.upper()
    if u.startswith("POSITIVO"):   ic, il = "ai-pos", "▲ IMPACTO POSITIVO"
    elif u.startswith("NEGATIVO"): ic, il = "ai-neg", "▼ IMPACTO NEGATIVO"
    else:                          ic, il = "ai-neu", "● IMPACTO NEUTRO"
    dot_cls = {"ai-pos": "ai-dot-pos", "ai-neg": "ai-dot-neg", "ai-neu": "ai-dot-neu"}.get(ic)
    st.markdown(f"""
    <div class="ai-box">
      <div class="ai-label">Análisis IA · Especialista en Minería Peruana</div>
      <div class="ai-impact {ic}"><span class="ai-dot {dot_cls}"></span>{il}</div>
      <div style="height:1px;background:rgba(255,255,255,0.06);margin:10px 0;"></div>
      <div class="ai-text">{txt}</div>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN: RADAR
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "RADAR":

    sem    = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    dfs    = df[df['fecha_iso'] >= sem] if len(df) > 0 else pd.DataFrame()
    tot    = len(dfs)
    altos  = int((dfs['riesgo'] == 'ALTO').sum())  if tot > 0 else 0
    medios = int((dfs['riesgo'] == 'MEDIO').sum()) if tot > 0 else 0
    ratio  = altos / tot if tot > 0 else 0
    diag   = ("Semana de alta tensión"    if ratio > 0.4 else
              "Semana de tensión moderada" if ratio > 0.2 else
              "Semana tranquila")

    st.markdown('<div class="slabel" style="margin-top:18px;">Pulso · esta semana</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="pulse-card">
      <div class="pulse-num">{altos}</div>
      <div class="pulse-lbl">Alertas ALTO esta semana</div>
      <div class="pulse-diag">{diag}</div>
    </div>""", unsafe_allow_html=True)

    # 3 stat cards
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        st.markdown(f'<div class="stat-card"><div class="stat-lbl">Alto</div>'
                    f'<div class="stat-val" style="color:#B91C1C;">{altos}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card"><div class="stat-lbl">Medio</div>'
                    f'<div class="stat-val" style="color:#92670A;">{medios}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-card"><div class="stat-lbl">Total</div>'
                    f'<div class="stat-val">{tot}</div></div>', unsafe_allow_html=True)

    # Anomalía
    if len(df) > 0:
        dc   = df.copy()
        dc['fecha_iso'] = pd.to_datetime(dc['fecha_iso'])
        prev = pd.date_range(end=datetime.now() - timedelta(days=7), periods=14, freq='D')
        pa   = [int((dc[dc['fecha_iso'].dt.strftime('%Y-%m-%d') == f.strftime('%Y-%m-%d')]['riesgo'] == 'ALTO').sum())
                for f in prev]
        prom = sum(pa) / len(pa) if pa else 0
        if altos > prom * 1.5 and prom > 0:
            st.markdown(f"""
            <div class="anomaly" style="margin-top:14px;">
              <div class="anomaly-lbl">⚠ Anomalía detectada</div>
              <div class="anomaly-txt">Actividad ALTO inusualmente alta esta semana
                ({altos} alertas vs. promedio de {prom:.1f}).</div>
            </div>""", unsafe_allow_html=True)

    # Gráfico tendencia 21 días
    st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)
    st.markdown('<div class="slabel">Tendencia · últimos 21 días</div>', unsafe_allow_html=True)

    if len(df) > 0:
        dp     = df.copy()
        dp['fecha_iso'] = pd.to_datetime(dp['fecha_iso'])
        fechas = pd.date_range(end=datetime.now(), periods=21, freq='D')

        def day_count(f, r):
            return int((dp[dp['fecha_iso'].dt.strftime('%Y-%m-%d') == f.strftime('%Y-%m-%d')]['riesgo'] == r).sum())

        td    = [{'f': f, 'A': day_count(f, 'ALTO'), 'M': day_count(f, 'MEDIO'), 'B': day_count(f, 'BAJO')}
                 for f in fechas]
        dplot = pd.DataFrame(td)
        xlbls = [f.strftime('%-d %b') for f in fechas]

        fig = go.Figure()
        fig.add_trace(go.Bar(x=xlbls, y=dplot['B'], name='BAJO',
                             marker_color='rgba(22,101,52,0.45)', marker_line_width=0,
                             hovertemplate='%{y} BAJO<extra></extra>'))
        fig.add_trace(go.Bar(x=xlbls, y=dplot['M'], name='MEDIO',
                             marker_color='rgba(146,103,10,0.65)', marker_line_width=0,
                             hovertemplate='%{y} MEDIO<extra></extra>'))
        fig.add_trace(go.Bar(x=xlbls, y=dplot['A'], name='ALTO',
                             marker_color='#B91C1C', marker_line_width=0,
                             hovertemplate='%{y} ALTO<extra></extra>'))
        fig.update_layout(
            barmode='stack',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='IBM Plex Mono', color='#6B7280', size=9),
            margin=dict(l=0, r=0, t=6, b=0), height=200, bargap=0.25,
            legend=dict(orientation='h', y=-0.28, x=0, font=dict(size=8.5),
                        bgcolor='rgba(0,0,0,0)', itemsizing='constant'),
            xaxis=dict(showgrid=False, tickfont=dict(size=8), color='#6B7280',
                       tickvals=xlbls[::7], ticktext=xlbls[::7]),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)',
                       zeroline=False, tickfont=dict(size=8)),
            hoverlabel=dict(bgcolor='#0F1F3D', font_color='#F5F0E8', font_size=10),
        )
        st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': False})

    # Resumen IA semanal
    st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)
    st.markdown('<div class="slabel">Lectura semanal · IA</div>', unsafe_allow_html=True)

    if 'radar_resumen' not in st.session_state:       st.session_state.radar_resumen = None
    if 'radar_resumen_fecha' not in st.session_state: st.session_state.radar_resumen_fecha = None

    today_str2 = datetime.now().strftime('%Y-%m-%d')
    if st.session_state.radar_resumen_fecha != today_str2 or st.session_state.radar_resumen is None:
        if tot > 0:
            titulos_semana = "\n".join([f"- {r['titulo']}" for _, r in dfs.head(25).iterrows()])
            with st.spinner("Generando lectura semanal..."):
                resumen_ia = groq_call(
                    f'Redacta UN párrafo corto (máx 4 oraciones) resumiendo el panorama de riesgo '
                    f'de la semana en la minería peruana basándote en estas noticias. '
                    f'Sé directo, técnico y sin preamble:\n{titulos_semana}',
                    system=GEO_PERSONA, max_tokens=250
                )
            st.session_state.radar_resumen = resumen_ia or "No se pudo generar la lectura semanal."
            st.session_state.radar_resumen_fecha = today_str2
        else:
            st.session_state.radar_resumen = "Sin suficientes noticias esta semana."

    st.markdown(f"""
    <div class="ai-box">
      <div class="ai-label">Análisis IA · Especialista en Minería Peruana</div>
      <div class="ai-text" style="margin-top:6px;">{st.session_state.radar_resumen}</div>
    </div>""", unsafe_allow_html=True)

    # Top alertas críticas
    st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)
    st.markdown('<div class="slabel">Alertas críticas · esta semana</div>', unsafe_allow_html=True)

    top_altos = dfs[dfs['riesgo'] == 'ALTO'].head(3) if tot > 0 else pd.DataFrame()

    if len(top_altos) == 0:
        st.markdown('<div class="empty"><div class="empty-t">Sin alertas ALTO esta semana</div>'
                    '<div class="empty-s">El panorama semanal es tranquilo.</div></div>',
                    unsafe_allow_html=True)
    else:
        for i, (_, row) in enumerate(top_altos.iterrows()):
            st.markdown(f"""
            <div style="display:flex;gap:12px;align-items:flex-start;
                        padding:12px 0;border-bottom:1px solid #E5E2DB;">
              <div style="font-family:'Playfair Display',serif;font-size:18px;
                          font-style:italic;color:#B91C1C;min-width:18px;
                          line-height:1.4;flex-shrink:0;">0{i+1}</div>
              <div style="flex:1;">
                <div style="font-family:'IBM Plex Mono',monospace;font-size:7.5px;
                            color:#9CA3AF;text-transform:uppercase;
                            letter-spacing:0.08em;margin-bottom:4px;">
                  {row['fuente']} · {row['fecha']}
                </div>
                <div style="font-size:12px;font-weight:500;color:#0F1F3D;line-height:1.45;">
                  {row['titulo']}
                </div>
              </div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Ver noticia {i+1}", key=f"radar_top_{i}"):
                open_art(row); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN: ACERCA
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "ACERCA":

    st.markdown("""
    <div style="padding:18px 0 20px;border-bottom:1px solid #E5E2DB;margin-bottom:18px;">
      <div class="hero-title">El<br><em>Reducto</em></div>
      <div class="hero-sub">Inteligencia Minera · Perú</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="slabel" style="margin-top:0;">Qué es</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="qes-text">
      <strong style="color:#0F1F3D;font-weight:600;">El Reducto</strong> es un monitor de
      inteligencia en tiempo real para el sector minero peruano. Recopila noticias de medios
      nacionales e internacionales, las clasifica automáticamente por nivel de riesgo mediante
      inteligencia artificial, y genera análisis de impacto específicos para empresas del sector.<br><br>
      Pensado para analistas, gestores de riesgo y equipos de relaciones comunitarias que necesitan
      estar informados sin perder horas filtrando ruido.
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="slabel">Para qué sirve</div>', unsafe_allow_html=True)
    for n, t in [
        ("01", "Monitorear conflictos sociales, huelgas y bloqueos en zonas de operación minera."),
        ("02", "Clasificar automáticamente noticias en ALTO, MEDIO o BAJO riesgo."),
        ("03", "Analizar cómo cada noticia impacta a una empresa específica con criterio de IA especializada."),
        ("04", "Detectar semanas anómalas y tendencias de escalada territorial antes de que se agraven."),
    ]:
        st.markdown(f"""
        <div class="feat-item">
          <div class="feat-num">{n}</div>
          <div class="feat-txt">{t}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)
    st.markdown('<div class="slabel">Creado por</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="creator-card">
      <div class="creator-name">Bryan Perez Aquino</div>
      <div class="creator-role">Científico de Datos e IA · En formación</div>
      <div class="creator-sep"></div>
      <div class="creator-txt">
        Este proyecto fue desarrollado como parte de mi formación en Ciencia de Datos con IA,
        con el objetivo de demostrar la aplicación de técnicas reales de machine learning,
        procesamiento de lenguaje natural y desarrollo de productos de datos en un contexto
        de alto impacto: la industria minera peruana.
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="slabel">Técnicas y herramientas</div>', unsafe_allow_html=True)
    skills = [
        ("⛏", "Web Scraping",        "Google News RSS + BeautifulSoup"),
        ("🤖", "NLP & Clasificación", "LLM-based risk scoring con Groq"),
        ("📊", "Series temporales",   "Detección de anomalías estadísticas"),
        ("🔍", "TF-IDF",              "Extracción automática de keywords"),
        ("🧠", "Prompt Engineering",  "Persona especializada en minería peruana"),
        ("🐍", "Python · Streamlit",  "App desplegada en Streamlit Cloud"),
    ]
    for i in range(0, len(skills), 2):
        c1, c2 = st.columns(2, gap="small")
        for col, (icon, name, desc) in zip([c1, c2], skills[i:i+2]):
            with col:
                st.markdown(f"""
                <div class="skill-card">
                  <div class="skill-icon">{icon}</div>
                  <div class="skill-name">{name}</div>
                  <div class="skill-desc">{desc}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="acerca-footer" style="margin-top:12px;">
      <div class="acerca-footer-txt">Lima, Perú · 2025</div>
      <div class="acerca-footer-note">Todas las opiniones son generadas por IA, no por un experto humano.</div>
    </div>""", unsafe_allow_html=True)
