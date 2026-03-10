import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import plotly.graph_objects as go
import json, os, time, logging, re
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
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,700;1,400;1,700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── RESET & BASE ─────────────────────────────────────────────────────────── */
*, html, body, [class*="css"], .stApp {
    box-sizing: border-box !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stApp { background: #F4EFE6 !important; }
.block-container {
    padding: 0 !important;
    max-width: 440px !important;
    margin: 0 auto !important;
}
#MainMenu, footer, header, .stDeployButton,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── TOPBAR ───────────────────────────────────────────────────────────────── */
.topbar {
    background: #F4EFE6;
    padding: 16px 20px 0;
    border-bottom: 1px solid #E0D9CE;
}
.topbar-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 14px;
}
.logo { font-size: 16px; font-weight: 600; color: #1B2A4A; letter-spacing: -0.02em; line-height: 1.2; }
.logo-sub { font-size: 8px; font-weight: 300; color: #6B7A8D; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 2px; }
.badge { display: inline-flex; align-items: center; gap: 5px; background: #1B2A4A; border-radius: 100px; padding: 5px 12px; }
.badge-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.badge-txt { font-size: 9px; font-weight: 600; letter-spacing: 0.06em; }

/* ── NAV RADIO ────────────────────────────────────────────────────────────── */
div[data-testid="stRadio"][data-key="nav"] > div,
div[data-testid="stRadio"]:has(> div > label:first-child > div > p:first-child) > div {
    background: #EDE7DC !important;
    border-radius: 100px !important;
    padding: 3px !important;
    gap: 2px !important;
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
}
/* Target ALL radio containers for nav style */
div[data-testid="stRadio"] > label { display: none !important; }
div[data-testid="stRadio"] > div {
    background: #EDE7DC !important;
    border-radius: 100px !important;
    padding: 3px !important;
    gap: 2px !important;
    display: flex !important;
    flex-direction: row !important;
}
div[data-testid="stRadio"] > div > label {
    flex: 1 !important;
    text-align: center !important;
    padding: 6px 2px !important;
    font-size: 7.5px !important;
    font-weight: 400 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #A8B4C0 !important;
    border-radius: 100px !important;
    cursor: pointer !important;
    margin: 0 !important;
    border: none !important;
    background: transparent !important;
    transition: all 0.15s !important;
}
div[data-testid="stRadio"] > div > label:has(input:checked) {
    font-weight: 600 !important;
    color: #1B2A4A !important;
    background: #FFFFFF !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1) !important;
}
div[data-testid="stRadio"] > div > label > div:first-child { display: none !important; }
div[data-testid="stRadio"] > div > label p {
    color: inherit !important;
    font-size: inherit !important;
    font-family: inherit !important;
    margin: 0 !important;
    line-height: 1 !important;
}

/* ── FEED FILTER OVERRIDE (second radio on page) ──────────────────────────── */
/* We'll use a wrapper class trick via markdown */
.feed-filter-wrap div[data-testid="stRadio"] > div {
    background: transparent !important;
    padding: 0 !important;
    gap: 6px !important;
    flex-wrap: wrap !important;
}
.feed-filter-wrap div[data-testid="stRadio"] > div > label {
    flex: none !important;
    padding: 5px 14px !important;
    font-size: 8px !important;
    border: 1.5px solid #E0D9CE !important;
    color: #6B7A8D !important;
    background: transparent !important;
    box-shadow: none !important;
}
.feed-filter-wrap div[data-testid="stRadio"] > div > label:has(input:checked) {
    color: #FFFFFF !important;
    box-shadow: none !important;
}

/* ── GOLD LINE ────────────────────────────────────────────────────────────── */
.gold-line { height: 1px; background: linear-gradient(to right, #C9A84C 40%, transparent); }
.divider   { height: 1px; background: #E0D9CE; margin: 4px 0 14px; }

/* ── SCREEN ───────────────────────────────────────────────────────────────── */
.screen { padding: 18px 20px 60px; }

/* ── SECTION LABEL ────────────────────────────────────────────────────────── */
.slabel {
    font-size: 8px; font-weight: 400; letter-spacing: 0.22em;
    text-transform: uppercase; color: #6B7A8D; margin-bottom: 10px;
    font-family: 'DM Sans', sans-serif;
}

/* ── FEATURED CARD ────────────────────────────────────────────────────────── */
.fc { background: #1B2A4A; border-radius: 20px; padding: 20px; margin-bottom: 18px; }
.fc-meta { font-size: 8px; color: #8A9AB0; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 10px; }
.fc-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 700; font-size: 21px; line-height: 1.15;
    color: #F5F0E8; letter-spacing: -0.02em; margin-bottom: 14px;
}
.fc-title em { font-weight: 400; font-style: italic; }
.fc-sep { height: 1px; background: rgba(255,255,255,0.07); margin-bottom: 14px; }
.fc-stats { display: flex; gap: 24px; margin-bottom: 14px; }
.fc-sl { font-size: 7px; letter-spacing: 0.14em; text-transform: uppercase; color: #4A5A72; margin-bottom: 3px; }
.fc-sv { font-size: 11px; font-weight: 600; color: #F5F0E8; }
.fc-sv.r { color: #E05252 !important; }
.fc-foot { display: flex; justify-content: space-between; align-items: center; }
.fc-link { font-size: 10px; color: #C9A84C; border-bottom: 1px solid rgba(201,168,76,0.4); padding-bottom: 1px; }

/* ── PILLS ────────────────────────────────────────────────────────────────── */
.pill { font-size: 7.5px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; padding: 3px 9px; border-radius: 100px; display: inline-block; }
.pa  { border: 1.5px solid #A82020; color: #A82020; background: rgba(168,32,32,0.06); }
.pm  { border: 1.5px solid #C9A84C; color: #C9A84C; background: rgba(201,168,76,0.06); }
.pb  { border: 1.5px solid #2A6B42; color: #2A6B42; background: rgba(42,107,66,0.06); }
.pad { border: 1.5px solid #E05252; color: #E05252; background: rgba(255,255,255,0.05); }
.pmd { border: 1.5px solid #D4A94C; color: #D4A94C; background: rgba(255,255,255,0.05); }
.pbd { border: 1.5px solid #4CAF7D; color: #4CAF7D; background: rgba(255,255,255,0.05); }

/* ── NEWS ITEM ────────────────────────────────────────────────────────────── */
.ni { display: flex; gap: 10px; padding: 12px 0; border-bottom: 1px solid #E0D9CE; align-items: flex-start; }
.rb { width: 3px; border-radius: 4px; align-self: stretch; flex-shrink: 0; min-height: 36px; }
.rba { background: #A82020; } .rbm { background: #C9A84C; } .rbb { background: #2A6B42; }
.ns { font-size: 8px; color: #A8B4C0; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 3px; }
.nt { font-size: 12px; font-weight: 500; color: #1B2A4A; line-height: 1.4; margin-bottom: 6px; }
.ni-arrow { font-size: 16px; color: #C8D0D8; align-self: center; flex-shrink: 0; padding-bottom: 2px; }

/* ── DETAIL ───────────────────────────────────────────────────────────────── */
.ds { font-size: 8.5px; color: #A8B4C0; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 10px; }
.dt { font-family: 'Cormorant Garamond', serif !important; font-weight: 700; font-size: 26px; line-height: 1.1; color: #1B2A4A; letter-spacing: -0.03em; margin-bottom: 14px; }
.dt em { font-weight: 400; font-style: italic; }
.summary-box { background: #FFF; border-left: 3px solid #1B2A4A; border-radius: 0 10px 10px 0; padding: 13px 15px; margin-bottom: 14px; font-size: 12px; color: #3A4A5A; line-height: 1.75; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.source-btn { font-size: 11px; color: #1B2A4A; border-bottom: 1px solid #1B2A4A; padding-bottom: 1px; text-decoration: none; display: inline-block; margin-bottom: 18px; }
.gdiv { height: 1px; background: linear-gradient(to right, #C9A84C, transparent); margin: 4px 0 16px; }
.ai-box { background: #1B2A4A; border-radius: 14px; padding: 16px; margin-top: 12px; }
.ai-label { font-size: 7.5px; color: #4A5A72; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 8px; }
.ai-impact { font-size: 8.5px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px; }
.ai-neg { color: #E05252; } .ai-pos { color: #4CAF7D; } .ai-neu { color: #8A9AB0; }
.ai-text { font-size: 11px; color: #A8B4C0; line-height: 1.7; }

/* ── RADAR ────────────────────────────────────────────────────────────────── */
.pulse-card { background: #1B2A4A; border-radius: 20px; padding: 24px 20px; margin-bottom: 14px; text-align: center; }
.pulse-num { font-family: 'Cormorant Garamond', serif !important; font-size: 64px; font-weight: 700; color: #F5F0E8; line-height: 1; letter-spacing: -0.04em; }
.pulse-lbl { font-size: 8px; color: #8A9AB0; letter-spacing: 0.16em; text-transform: uppercase; margin-top: 6px; }
.pulse-diag { font-family: 'Cormorant Garamond', serif !important; font-size: 15px; font-style: italic; color: #6B7A8D; margin-top: 6px; }
.anomaly { background: #FDF0F0; border: 1.5px solid #A82020; border-radius: 12px; padding: 11px 15px; margin-bottom: 16px; }
.anomaly-lbl { font-size: 7.5px; color: #A82020; letter-spacing: 0.15em; text-transform: uppercase; font-weight: 700; margin-bottom: 4px; }
.anomaly-txt { font-size: 11px; color: #5A2020; line-height: 1.55; }
.stat-card { background: #FFF; border-radius: 12px; padding: 11px 13px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 8px; }
.stat-lbl { font-size: 7.5px; color: #A8B4C0; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 4px; }
.stat-val { font-size: 13px; font-weight: 600; color: #1B2A4A; }

/* ── ACERCA ───────────────────────────────────────────────────────────────── */
.hero-title { font-family: 'Cormorant Garamond', serif !important; font-size: 38px; font-weight: 700; color: #1B2A4A; line-height: 1.05; letter-spacing: -0.04em; margin-bottom: 6px; }
.hero-title em { font-weight: 400; font-style: italic; }
.hero-sub { font-size: 8.5px; color: #C9A84C; letter-spacing: 0.18em; text-transform: uppercase; }
.qes-text { font-size: 12.5px; color: #3A4A5A; line-height: 1.8; margin-bottom: 22px; }
.feature-card { background: #FFF; border-radius: 12px; padding: 12px 14px; margin-bottom: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); display: flex; gap: 12px; align-items: flex-start; }
.feature-num { font-family: 'Cormorant Garamond', serif !important; font-size: 16px; font-style: italic; color: #C9A84C; min-width: 20px; flex-shrink: 0; line-height: 1.5; }
.feature-txt { font-size: 11.5px; color: #3A4A5A; line-height: 1.6; }
.creator-card { background: #1B2A4A; border-radius: 18px; padding: 20px; margin-bottom: 16px; }
.creator-name { font-family: 'Cormorant Garamond', serif !important; font-size: 22px; font-style: italic; color: #F5F0E8; margin-bottom: 4px; }
.creator-role { font-size: 8.5px; color: #C9A84C; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 14px; }
.creator-sep { height: 1px; background: rgba(255,255,255,0.07); margin-bottom: 14px; }
.creator-txt { font-size: 11.5px; color: #A8B4C0; line-height: 1.8; }
.skill-card { background: #FFF; border-radius: 12px; padding: 11px 13px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.skill-icon { font-size: 18px; margin-bottom: 5px; }
.skill-name { font-size: 10.5px; font-weight: 600; color: #1B2A4A; margin-bottom: 3px; }
.skill-desc { font-size: 9.5px; color: #6B7A8D; line-height: 1.5; }
.acerca-footer { text-align: center; padding-top: 16px; border-top: 1px solid #E0D9CE; }
.acerca-footer-txt { font-size: 8.5px; color: #A8B4C0; letter-spacing: 0.14em; text-transform: uppercase; }
.acerca-footer-note { font-size: 8px; color: #C8D0D8; margin-top: 4px; }

/* ── SEARCH INPUT ─────────────────────────────────────────────────────────── */
div[data-baseweb="input"] { background: #FFF !important; border: 1.5px solid #E0D9CE !important; border-radius: 100px !important; box-shadow: none !important; }
div[data-baseweb="input"]:focus-within { border-color: #1B2A4A !important; }
input { font-family: 'DM Sans', sans-serif !important; font-size: 13px !important; color: #1B2A4A !important; background: transparent !important; }

/* ── BUTTONS ──────────────────────────────────────────────────────────────── */
.stButton > button {
    background: transparent !important; color: #6B7A8D !important;
    border: 1.5px solid #E0D9CE !important; border-radius: 100px !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 8.5px !important;
    font-weight: 500 !important; letter-spacing: 0.1em !important;
    text-transform: uppercase !important; padding: 0.4rem 1rem !important;
    box-shadow: none !important; transition: all 0.18s !important;
}
.stButton > button:hover { background: #1B2A4A !important; color: #F5F0E8 !important; border-color: #1B2A4A !important; }

/* ── SKELETON ─────────────────────────────────────────────────────────────── */
.sk { background: linear-gradient(90deg,#E8E2D6 25%,#F0EBE0 50%,#E8E2D6 75%); background-size:200% 100%; animation:sh 1.4s infinite; border-radius:6px; }
@keyframes sh { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* ── PLOTLY ───────────────────────────────────────────────────────────────── */
[data-testid="stPlotlyChart"] { border-radius: 14px; overflow: hidden; }

/* ── EMPTY STATE ──────────────────────────────────────────────────────────── */
.empty { text-align:center; padding:40px 20px; }
.empty-t { font-family:'Cormorant Garamond',serif!important; font-size:20px; font-style:italic; color:#A8B4C0; margin-bottom:6px; }
.empty-s { font-size:11px; color:#C8D0D8; }
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
    try: return json.load(open(DB_PATH))
    except: return {'date': '', 'articles': [], 'history': []}

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
    # Cajamarca — conflictos y comunidades
    "mineria+Cajamarca+conflicto",
    "mineria+Cajamarca+comunidades",
    "protesta+minera+Cajamarca",
    "huelga+minera+Cajamarca",
    "Conga+mina+Cajamarca",
    "rondas+campesinas+mineria",

    # IAMGOLD y empresas específicas
    "IAMGOLD+Peru",
    "IAMGOLD+Cajamarca",
    "Yanacocha+Cajamarca",
    "minera+Buenaventura+Peru",
    "Southern+Copper+Peru",

    # Conflictos a nivel nacional
    "conflictos+mineros+Peru",
    "paro+minero+Peru",
    "bloqueo+minero+Peru",
    "comunidades+mineria+Peru",
    "conflicto+socioambiental+Peru",

    # Regulación y política
    "MINEM+Peru+mineria",
    "OEFA+fiscalizacion+mineria",
    "inversion+minera+Peru",
    "concesion+minera+Peru",

    # Regiones mineras clave
    "mineria+La+Libertad+Peru",
    "mineria+Ancash+Peru",
    "mineria+Apurimac+Peru",
    "mineria+Arequipa+Peru",
]

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
    todos = []
    for i in range(0, min(len(df), 200), 20):
        lote  = df['titulo'].tolist()[i:i+20]
        lista = "\n".join([f"{j+1}. {x}" for j, x in enumerate(lote)])
        res   = groq_call(
            f'Clasifica estas noticias mineras de Perú. Devuelve SOLO un JSON array. '
            f'"ALTO"=protesta/huelga/paro/bloqueo, "MEDIO"=tensión/diálogo/riesgo, "BAJO"=inversión/neutro.\n'
            f'{lista}\nArray JSON:', max_tokens=300
        )
        try:
            if res:
                s, e = res.find('['), res.rfind(']') + 1
                if s != -1 and e > s: todos.extend(json.loads(res[s:e]))
                else: todos.extend(["BAJO"] * len(lote))
            else: todos.extend(["BAJO"] * len(lote))
        except: todos.extend(["BAJO"] * len(lote))
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
          'nuevos','tras','ante','según','así','ser','tras','tras'}
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
    df = (pd.DataFrame(todos)
          .drop_duplicates(subset='titulo')
          .sort_values('fecha_iso', ascending=False)
          .reset_index(drop=True))
    df = classify(df)
    history  = db.get('history', [])
    td       = df[df['fecha_iso'] == today]
    entry    = {'fecha': today,
                'alto':  int((td['riesgo'] == 'ALTO').sum()),
                'medio': int((td['riesgo'] == 'MEDIO').sum()),
                'bajo':  int((td['riesgo'] == 'BAJO').sum())}
    if not any(h['fecha'] == today for h in history): history.append(entry)
    history  = sorted(history, key=lambda x: x['fecha'])[-30:]
    db.update({'date': today, 'articles': df.to_dict('records'), 'history': history})
    save_db(db)
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for k, v in {'tab': 'HOY', 'prev_tab': 'HOY', 'sel': None,
             'summaries': {}, 'impacts': {}, 'company': 'IAMGOLD'}.items():
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

def rbar(r):
    return f'<div class="rb rb{r[0].lower()}"></div>'

def news_row(row, key):
    c1, c2 = st.columns([13, 1], gap="small")
    with c1:
        st.markdown(
            f'<div class="ni">{rbar(row["riesgo"])}'
            f'<div style="flex:1"><div class="ns">{row["fuente"]} · {row["fecha"]}</div>'
            f'<div class="nt">{row["titulo"]}</div>{pill(row["riesgo"])}</div>'
            f'<div class="ni-arrow">›</div></div>',
            unsafe_allow_html=True
        )
    with c2:
        st.write("")  # vertical spacer
    # invisible full-row button
    if st.button("", key=key, help=row['titulo'],
                 use_container_width=True):
        open_art(row); st.rerun()

def skeleton():
    st.markdown("""
    <div style="padding:20px;">
      <div class="sk" style="height:10px;width:35%;margin-bottom:16px;"></div>
      <div style="background:#1B2A4A;border-radius:20px;padding:20px;margin-bottom:18px;">
        <div class="sk" style="height:8px;width:50%;margin-bottom:12px;background:#2A3A5A;"></div>
        <div class="sk" style="height:16px;width:90%;margin-bottom:8px;background:#2A3A5A;"></div>
        <div class="sk" style="height:16px;width:70%;margin-bottom:16px;background:#2A3A5A;"></div>
        <div class="sk" style="height:10px;width:25%;background:#2A3A5A;"></div>
      </div>
      <div class="sk" style="height:8px;width:28%;margin-bottom:14px;"></div>
      <div class="sk" style="height:48px;width:100%;margin-bottom:8px;border-radius:10px;"></div>
      <div class="sk" style="height:48px;width:100%;margin-bottom:8px;border-radius:10px;"></div>
      <div class="sk" style="height:48px;width:100%;border-radius:10px;"></div>
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

today_str   = datetime.now().strftime('%Y-%m-%d')
alert_count = int((df[df['fecha_iso'] == today_str]['riesgo'] == 'ALTO').sum()) if len(df) > 0 else 0
dot_color   = "#A82020" if alert_count >= 3 else "#C9A84C" if alert_count >= 1 else "#2A6B42"
weekday_es  = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"][datetime.now().weekday()]
today_label = datetime.now().strftime("%-d de %B").capitalize()


# ══════════════════════════════════════════════════════════════════════════════
#  TOPBAR
# ══════════════════════════════════════════════════════════════════════════════
NAV = ["HOY", "FEED", "BUSCAR", "RADAR", "ACERCA"]

st.markdown(f"""
<div class="topbar">
  <div class="topbar-row">
    <div>
      <div class="logo">El Reducto</div>
      <div class="logo-sub">{weekday_es} {today_label} · Lima</div>
    </div>
    <div class="badge">
      <span class="badge-dot" style="background:{dot_color};"></span>
      <span class="badge-txt" style="color:{dot_color};">{alert_count} alertas hoy</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

current  = st.session_state.prev_tab if st.session_state.tab == "DETALLE" else st.session_state.tab
nav_idx  = NAV.index(current) if current in NAV else 0
selected = st.radio("nav", NAV, index=nav_idx, horizontal=True,
                    label_visibility="collapsed", key="nav_radio")
if selected != current:
    st.session_state.tab = selected
    st.session_state.sel = None
    st.rerun()

st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN: HOY
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.tab == "HOY":
    st.markdown('<div class="screen">', unsafe_allow_html=True)

    if len(df) == 0:
        st.markdown('<div class="empty"><div class="empty-t">Sin noticias disponibles</div>'
                    '<div class="empty-s">No se pudo conectar con las fuentes. Intenta más tarde.</div></div>',
                    unsafe_allow_html=True)
    else:
        top  = df.iloc[0]
        l1, l2 = split_title(top['titulo'])
        riesgo_color = "r" if top['riesgo'] == "ALTO" else ""

        st.markdown(f"""
        <div class="slabel" style="display:flex;justify-content:space-between;margin-bottom:10px;">
          <span>Noticia principal</span>
          <span style="color:#C9A84C;letter-spacing:0.12em;">1 / {min(len(df),8)}</span>
        </div>
        <div class="fc">
          <div class="fc-meta">{top['fuente']} · {top['fecha']}</div>
          <div class="fc-title">{l1}<br><em>{l2}</em></div>
          <div class="fc-stats">
            <div><div class="fc-sl">Fuente</div><div class="fc-sv">{top['fuente']}</div></div>
            <div><div class="fc-sl">Riesgo</div><div class="fc-sv {riesgo_color}">{top['riesgo']}</div></div>
            <div><div class="fc-sl">Fecha</div><div class="fc-sv">{top['fecha']}</div></div>
          </div>
          <div class="fc-sep"></div>
          <div class="fc-foot">
            {pill(top['riesgo'], dark=True)}
            <span class="fc-link">Abrir noticia →</span>
          </div>
        </div>""", unsafe_allow_html=True)

        if st.button("Abrir noticia principal →", use_container_width=True, key="open_top"):
            open_art(top); st.rerun()

        st.markdown('<div class="gold-line" style="margin:14px 0;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="slabel">Últimas noticias</div>', unsafe_allow_html=True)

        for i, row in df.iloc[1:8].iterrows():
            news_row(row, f"h{i}")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN: FEED
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "FEED":
    st.markdown('<div class="screen">', unsafe_allow_html=True)

    FOPTS = ["TODOS", "ALTO", "MEDIO", "BAJO"]
    fcol  = {"TODOS": "#1B2A4A", "ALTO": "#A82020", "MEDIO": "#C9A84C", "BAJO": "#2A6B42"}
    fidx  = FOPTS.index(st.session_state.get('feed_f', 'TODOS'))

    # Styled filter buttons
    cols = st.columns(len(FOPTS), gap="small")
    for col, opt in zip(cols, FOPTS):
        with col:
            active = st.session_state.get('feed_f', 'TODOS') == opt
            color  = fcol[opt]
            st.markdown(f"""
            <div style="text-align:center;">
              <span style="display:inline-block;padding:5px 0;width:100%;border-radius:100px;
                border:1.5px solid {''+color+'' if active else '#E0D9CE'};
                background:{''+color+'' if active else 'transparent'};
                color:{'#FFF' if active else '#6B7A8D'};
                font-size:8px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;
                font-family:'DM Sans',sans-serif;cursor:pointer;">{opt}</span>
            </div>""", unsafe_allow_html=True)
            if st.button(opt, key=f"ff_{opt}", use_container_width=True):
                st.session_state['feed_f'] = opt
                st.rerun()

    ff   = st.session_state.get('feed_f', 'TODOS')
    feed = df if ff == "TODOS" else df[df['riesgo'] == ff]

    st.markdown(f'<div class="slabel" style="margin-top:14px;">{len(feed)} noticias · {ff}</div>',
                unsafe_allow_html=True)

    if len(feed) == 0:
        st.markdown(f'<div class="empty"><div class="empty-t">Sin noticias {ff.lower()}</div>'
                    '<div class="empty-s">No hay noticias con este nivel de riesgo.</div></div>',
                    unsafe_allow_html=True)
    else:
        for i, row in feed.head(40).iterrows():
            news_row(row, f"f{i}")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN: BUSCAR
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "BUSCAR":
    st.markdown('<div class="screen">', unsafe_allow_html=True)

    q = st.text_input("", placeholder="🔍  Buscar por tema, fuente o empresa...",
                      label_visibility="collapsed")

    if not q:
        kw = get_keywords(df, 8)
        if kw:
            st.markdown('<div class="slabel" style="margin-top:10px;">Temas frecuentes</div>',
                        unsafe_allow_html=True)
            tags = " ".join([f'<span class="pill pm" style="margin:3px 2px;">{w}</span>'
                             for w, _ in kw])
            st.markdown(f'<div style="line-height:2.6;margin-bottom:16px;">{tags}</div>',
                        unsafe_allow_html=True)

        st.markdown('<div class="slabel">Sugerencias</div>', unsafe_allow_html=True)
        sugs = " ".join([f'<span class="pill pb" style="margin:3px 2px;">{t}</span>'
                         for t in ["IAMGOLD", "Cajamarca", "Conga", "Huelga", "MINEM", "Yanacocha"]])
        st.markdown(f'<div style="line-height:2.6;">{sugs}</div>', unsafe_allow_html=True)
    else:
        mask    = (df['titulo'].str.contains(q, case=False, na=False) |
                   df['fuente'].str.contains(q, case=False, na=False))
        results = df[mask]
        st.markdown(f'<div class="slabel" style="margin-top:10px;">'
                    f'{len(results)} resultados para "{q}"</div>',
                    unsafe_allow_html=True)
        if len(results) == 0:
            st.markdown(f'<div class="empty"><div class="empty-t">Sin resultados para "{q}"</div>'
                        '<div class="empty-s">Prueba con otra palabra clave.</div></div>',
                        unsafe_allow_html=True)
        else:
            for i, row in results.iterrows():
                news_row(row, f"s{i}")

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN: DETALLE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "DETALLE" and st.session_state.sel is not None:
    row    = st.session_state.sel
    art_id = str(hash(row['titulo']))

    st.markdown('<div class="screen">', unsafe_allow_html=True)

    if st.button("← Volver", key="back"):
        st.session_state.tab = st.session_state.prev_tab
        st.session_state.sel = None
        st.rerun()

    l1, l2 = split_title(row['titulo'])
    st.markdown(f"""
    <div class="ds">{row['fuente']} · {row['fecha']}</div>
    <div class="dt">{l1}<br><em>{l2}</em></div>
    {pill(row['riesgo'])}
    <div style="height:16px;"></div>""", unsafe_allow_html=True)

    # Resumen IA
    st.markdown('<div class="gold-line" style="margin-bottom:14px;"></div>', unsafe_allow_html=True)
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

    # Análisis de impacto
    st.markdown('<div class="gdiv"></div>', unsafe_allow_html=True)
    st.markdown('<div class="slabel">Análisis de impacto</div>', unsafe_allow_html=True)

    company = st.text_input("", value=st.session_state.company,
                            placeholder="Empresa a analizar...",
                            label_visibility="collapsed", key="co_input")
    st.session_state.company = company

    if st.button(f"¿Cómo afecta a {company}? →", use_container_width=True, key="analyze"):
        ck = f"{art_id}_{company}"
        with st.spinner("Analizando con criterio geológico..."):
            imp = groq_call(
                f'Analiza cómo afecta a {company} en Perú. '
                f'Empieza con "POSITIVO:", "NEGATIVO:" o "NEUTRO:". Máx 4 oraciones.\n'
                f'Noticia: "{row["titulo"]}"\nContexto: "{st.session_state.summaries.get(art_id, "")}"',
                system=GEO_PERSONA, max_tokens=300
            )
            st.session_state.impacts[ck] = imp or "No se pudo generar el análisis."

    ck = f"{art_id}_{company}"
    if ck in st.session_state.impacts:
        txt = st.session_state.impacts[ck]
        u   = txt.upper()
        if u.startswith("POSITIVO"):   ic, il = "ai-pos", "▲ IMPACTO POSITIVO"
        elif u.startswith("NEGATIVO"): ic, il = "ai-neg", "▼ IMPACTO NEGATIVO"
        else:                          ic, il = "ai-neu", "● IMPACTO NEUTRO"
        st.markdown(f"""
        <div class="ai-box">
          <div class="ai-label">Análisis IA · Especialista en Minería Peruana</div>
          <div class="ai-impact {ic}">{il}</div>
          <div class="ai-text">{txt}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN: RADAR
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "RADAR":
    st.markdown('<div class="screen">', unsafe_allow_html=True)
    st.markdown('<div class="slabel">Radar de riesgo territorial</div>', unsafe_allow_html=True)

    sem    = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    dfs    = df[df['fecha_iso'] >= sem] if len(df) > 0 else pd.DataFrame()
    tot    = len(dfs)
    altos  = int((dfs['riesgo'] == 'ALTO').sum())  if tot > 0 else 0
    medios = int((dfs['riesgo'] == 'MEDIO').sum()) if tot > 0 else 0
    ratio  = altos / tot if tot > 0 else 0
    diag   = ("Semana de alta tensión"    if ratio > 0.4 else
              "Semana de tensión moderada" if ratio > 0.2 else
              "Semana tranquila")

    st.markdown(f"""
    <div class="pulse-card">
      <div class="pulse-num">{altos}</div>
      <div class="pulse-lbl">Noticias ALTO esta semana</div>
      <div class="pulse-diag">{diag}</div>
    </div>""", unsafe_allow_html=True)

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
            <div class="anomaly">
              <div class="anomaly-lbl">⚠ Anomalía detectada</div>
              <div class="anomaly-txt">Actividad ALTO inusualmente alta esta semana
                ({altos} alertas vs. promedio de {prom:.1f}).</div>
            </div>""", unsafe_allow_html=True)

    # Stat grid 2×2
    ft  = dfs['fuente'].value_counts().index[0] if tot > 0 else "—"
    kws = " · ".join([w for w, _ in get_keywords(dfs, 3)]) if tot > 0 else "—"

    c1, c2 = st.columns(2, gap="small")
    with c1:
        st.markdown(f'<div class="stat-card"><div class="stat-lbl">Noticias MEDIO</div>'
                    f'<div class="stat-val">{medios}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-card"><div class="stat-lbl">Fuente más activa</div>'
                    f'<div class="stat-val" style="font-size:11px;">{ft}</div></div>',
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card"><div class="stat-lbl">Total procesado</div>'
                    f'<div class="stat-val">{tot}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-card"><div class="stat-lbl">Keywords</div>'
                    f'<div class="stat-val" style="font-size:10px;">{kws}</div></div>',
                    unsafe_allow_html=True)

    # Tendencia
    st.markdown('<div class="gold-line" style="margin:14px 0;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="slabel">Tendencia · últimos 14 días</div>', unsafe_allow_html=True)

    if len(df) > 0:
        dp     = df.copy()
        dp['fecha_iso'] = pd.to_datetime(dp['fecha_iso'])
        fechas = pd.date_range(end=datetime.now(), periods=14, freq='D')

        def day_count(f, r):
            return int((dp[dp['fecha_iso'].dt.strftime('%Y-%m-%d') == f.strftime('%Y-%m-%d')]['riesgo'] == r).sum())

        td     = [{'f': f, 'A': day_count(f, 'ALTO'), 'M': day_count(f, 'MEDIO'), 'B': day_count(f, 'BAJO')}
                  for f in fechas]
        dplot  = pd.DataFrame(td)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dplot['f'], y=dplot['A'], name='ALTO',
                                 line=dict(color='#A82020', width=2.5),
                                 fill='tozeroy', fillcolor='rgba(168,32,32,0.08)'))
        fig.add_trace(go.Scatter(x=dplot['f'], y=dplot['M'], name='MEDIO',
                                 line=dict(color='#C9A84C', width=1.8, dash='dot')))
        fig.add_trace(go.Scatter(x=dplot['f'], y=dplot['B'], name='BAJO',
                                 line=dict(color='#2A6B42', width=1.5)))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='DM Sans', color='#6B7A8D', size=10),
            margin=dict(l=0, r=0, t=10, b=0), height=200,
            legend=dict(orientation='h', y=-0.4, x=0, font=dict(size=9)),
            xaxis=dict(showgrid=False, tickformat='%d %b', tickfont=dict(size=9), color='#6B7A8D'),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.06)',
                       zeroline=False, tickfont=dict(size=9)),
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN: ACERCA
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "ACERCA":
    st.markdown('<div class="screen">', unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <div style="padding-bottom:20px;border-bottom:1px solid #E0D9CE;margin-bottom:22px;">
      <div class="hero-title">El<br><em>Reducto</em></div>
      <div class="hero-sub">Inteligencia Minera · Perú</div>
    </div>""", unsafe_allow_html=True)

    # Qué es
    st.markdown('<div class="slabel">Qué es</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="qes-text">
      <strong style="color:#1B2A4A;font-weight:600;">El Reducto</strong> es un monitor de
      inteligencia en tiempo real para el sector minero peruano. Recopila noticias de medios
      nacionales e internacionales, las clasifica automáticamente por nivel de riesgo mediante
      inteligencia artificial, y genera análisis de impacto específicos para empresas del sector.<br><br>
      Pensado para analistas, gestores de riesgo y equipos de relaciones comunitarias que necesitan
      estar informados sin perder horas filtrando ruido.
    </div>""", unsafe_allow_html=True)

    # Para qué sirve
    st.markdown('<div class="slabel">Para qué sirve</div>', unsafe_allow_html=True)
    for n, t in [
        ("01", "Monitorear conflictos sociales, huelgas y bloqueos en zonas de operación minera."),
        ("02", "Clasificar automáticamente noticias en ALTO, MEDIO o BAJO riesgo."),
        ("03", "Analizar cómo cada noticia impacta a una empresa específica con criterio de IA especializada."),
        ("04", "Detectar semanas anómalas y tendencias de escalada territorial antes de que se agraven."),
    ]:
        st.markdown(f"""
        <div class="feature-card">
          <div class="feature-num">{n}</div>
          <div class="feature-txt">{t}</div>
        </div>""", unsafe_allow_html=True)

    # Creado por
    st.markdown('<div class="gold-line" style="margin:22px 0 20px;"></div>', unsafe_allow_html=True)
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

    # Skills grid 2×2
    st.markdown('<div class="slabel">Técnicas y herramientas</div>', unsafe_allow_html=True)

    skills = [
        ("⛏", "Web Scraping",       "Google News RSS + BeautifulSoup"),
        ("🤖", "NLP & Clasificación","LLM-based risk scoring con Groq"),
        ("📊", "Series temporales",  "Detección de anomalías estadísticas"),
        ("🔍", "TF-IDF",             "Extracción automática de keywords"),
        ("🧠", "Prompt Engineering", "Persona especializada en minería peruana"),
        ("🐍", "Python · Streamlit", "App desplegada en Streamlit Cloud"),
    ]

    for i in range(0, len(skills), 2):
        c1, c2 = st.columns(2, gap="small")
        for col, (icon, name, desc) in zip([c1, c2], skills[i:i+2]):
            with col:
                st.markdown(f"""
                <div class="skill-card" style="margin-bottom:8px;">
                  <div class="skill-icon">{icon}</div>
                  <div class="skill-name">{name}</div>
                  <div class="skill-desc">{desc}</div>
                </div>""", unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="acerca-footer" style="margin-top:8px;">
      <div class="acerca-footer-txt">Lima, Perú · 2025</div>
      <div class="acerca-footer-note">Todas las opiniones son generadas por IA, no por un experto humano.</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
