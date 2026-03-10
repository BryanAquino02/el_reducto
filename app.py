import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import plotly.express as px
import json
import os
import time
import logging

logging.basicConfig(level=logging.WARNING)

GROQ_KEY    = st.secrets["GROQ_KEY"]
DB_PATH     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "news_db_v4.json")

st.set_page_config(
    page_title="El Reducto — Inteligencia",
    page_icon="🗞️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── INITIALIZE STATE FOR NAVIGATION ──
if 'current_tab' not in st.session_state: st.session_state.current_tab = "Monitor"

# ─────────────────────────────── CSS EDITORIAL LUXURY ───────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,900;1,900&family=DM+Sans:wght@300;400&display=swap');
@import url('https://cdn.jsdelivr.net/npm/geist@1.0.0/dist/fonts/geist-mono/style.css');

*, html, body, [class*="css"], .stApp { box-sizing: border-box; font-family: 'DM Sans', sans-serif !important; }

.stApp { background: #F4F1EB; }

.block-container {
    padding: 1.5rem 20px 2rem !important; 
    max-width: 600px !important; margin: 0 auto !important;
}

#MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }

h1, h2, h3, .playfair { font-family: 'Playfair Display', serif !important; font-weight: 900 !important; color: #111009 !important; letter-spacing: -0.04em !important; }
.geist { font-family: 'Geist Mono', monospace !important; text-transform: uppercase !important; font-weight: 300 !important; }
p, span, div { color: #6B6660; }
strong { color: #111009; font-weight: 400; }

hr { border: none; border-top: 1px solid #DDD9D0; margin: 2rem 0; }
.hr-thick { border-top: 2px solid #0E0D0B; margin: 1.5rem 0 1rem 0; }

.section-title { font-family: 'Geist Mono', monospace; font-size: 0.65rem; font-weight: 300; letter-spacing: 0.15em; text-transform: uppercase; color: #6B6660; margin-bottom: 0.5rem; }

/* ── CARDS ── */
.news-card { background: #FAFAF7; border: 1px solid #DDD9D0; border-radius: 14px; padding: 1.25rem; margin-bottom: 1rem; }
.news-title { font-family: 'Playfair Display', serif; font-size: 1.15rem; font-weight: 900; color: #111009; line-height: 1.3; letter-spacing: -0.02em; margin-bottom: 0.8rem; }
.featured-card { background: #0E0D0B; border: none; border-radius: 14px; padding: 1.5rem; margin-bottom: 1.5rem; }
.featured-card .news-title { color: #F4F1EB; font-size: 1.4rem; }
.featured-card p, .featured-card span, .featured-card .geist { color: #A8A39C !important; }
.featured-card .pill { border-color: #A8A39C; color: #F4F1EB; }

/* ── BRIEF CARD (NEW) ── */
.brief-card { background: #FAFAF7; border-left: 4px solid #0E0D0B; padding: 1.5rem; margin-bottom: 2rem; position: relative; }
.dropcap { font-family: 'Playfair Display', serif; font-size: 3.5rem; float: left; line-height: 0.8; margin-right: 0.5rem; color: #111009; font-style: italic; font-weight: 900; }
.brief-text { font-family: 'DM Sans', sans-serif; font-size: 0.95rem; line-height: 1.6; color: #111009; }

/* ── META & PILLS ── */
.news-meta { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.pill { font-family: 'Geist Mono', monospace; font-size: 0.55rem; font-weight: 300; letter-spacing: 0.05em; text-transform: uppercase; padding: 0.2rem 0.5rem; border-radius: 100px; border: 1px solid #DDD9D0; color: #111009; }
.pill-alto { background: transparent; border-color: #111009; color: #111009; }
.pill-medio { background: transparent; color: #6B6660; }
.pill-bajo { background: #3A6B4A; border-color: #3A6B4A; color: #FAFAF7; }
.source-date { font-family: 'Geist Mono', monospace; font-size: 0.6rem; color: #A8A39C; text-transform: uppercase; letter-spacing: 0.05em; }

/* ── BUTTONS ── */
.read-more { font-family: 'DM Sans', sans-serif; font-size: 0.8rem; font-weight: 400; color: #111009; text-decoration: none; border-bottom: 1px solid #111009; padding-bottom: 1px; }
.featured-card .read-more { color: #F4F1EB; border-color: #F4F1EB; }
.stButton > button { background: transparent; color: #6B6660; border: 1px solid #DDD9D0; border-radius: 100px; font-family: 'Geist Mono', monospace !important; font-size: 0.6rem !important; font-weight: 300; letter-spacing: 0.05em; text-transform: uppercase; padding: 0.4rem 0.8rem; width: 100%; box-shadow: none !important; }
.stButton > button:hover { background: #0E0D0B !important; color: #F4F1EB !important; border-color: #0E0D0B !important; }

/* ── SKELETON LOADER ── */
.skeleton { background: #EAE7E0; border-radius: 4px; animation: pulse 1.5s infinite ease-in-out; }
@keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }

/* ── METRIC OVERRIDE ── */
[data-testid="metric-container"] { border-top: 2px solid #111009; border-bottom: 1px solid #DDD9D0; background: transparent; }

</style>
""", unsafe_allow_html=True)


# ─────────────────────────────── HELPERS & DB ───────────────────────────────
def init_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w') as f:
            json.dump({'date': '', 'articles': []}, f)
init_db()

def load_db():
    try: return json.load(open(DB_PATH, 'r'))
    except: return {'date': '', 'articles': []}

def save_db(data):
    with open(DB_PATH, 'w') as f: json.dump(data, f)

def groq_request(prompt, max_tokens=1000):
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens},
            timeout=15
        )
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        logging.warning("Groq API timeout")
        return None
    except requests.exceptions.RequestException as e:
        logging.warning(f"Groq API error: {e}")
        return None
    except (KeyError, IndexError) as e:
        logging.warning(f"Groq response parse error: {e}")
        return None

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
    """Scrape Google News RSS for all queries and return raw article list."""
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
                except Exception:
                    continue
        except Exception as e:
            logging.warning(f"Error fetching query '{q}': {e}")
            continue
    return todos

def classify_articles(df):
    """Classify article titles into ALTO/MEDIO/BAJO using Groq in batches."""
    titulos = df['titulo'].tolist()
    todas_clases = []
    titulos_clasificar = titulos[:60]

    for i in range(0, len(titulos_clasificar), 20):
        lote = titulos_clasificar[i:i+20]
        lista = "\n".join([f"{j+1}. {x}" for j, x in enumerate(lote)])
        res = groq_request(
            f'Clasifica noticias mineras de Perú. JSON array SOLO sin preamble. '
            f'Valores: "ALTO", "MEDIO", "BAJO". '
            f'ALTO=protesta/violencia/huelga, MEDIO=tensión/minería/comunidades, BAJO=inversión/neutro/nombramientos. '
            f'Noticias:\n{lista}\nArray JSON estricto:', 300
        )
        try:
            if res:
                start = res.find('[')
                end = res.rfind(']') + 1
                if start != -1 and end > start:
                    todas_clases.extend(json.loads(res[start:end]))
                else:
                    todas_clases.extend(["BAJO"] * len(lote))
            else:
                todas_clases.extend(["BAJO"] * len(lote))
        except Exception as e:
            logging.warning(f"Classification parse error on batch {i}: {e}")
            todas_clases.extend(["BAJO"] * len(lote))
        time.sleep(1)

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

    fecha_limite = datetime.now() - timedelta(days=180)
    todos = fetch_articles_from_rss(QUERIES, fecha_limite)

    if not todos:
        st.warning("No se pudieron obtener artículos. Revisa la conexión o los parámetros de búsqueda.")
        return pd.DataFrame(columns=['titulo', 'fuente', 'fecha', 'fecha_iso', 'url', 'riesgo'])

    df = (
        pd.DataFrame(todos)
        .drop_duplicates(subset='titulo')
        .reset_index(drop=True)
        .sort_values('fecha_iso', ascending=False)
    )

    df = classify_articles(df)

    db['date'] = today
    db['articles'] = df.to_dict('records')
    save_db(db)

    return df

# ── FETCH DATA ──
holder = st.empty()
holder.markdown("""<div style="padding:4rem 0;text-align:center;"><div class="skeleton" style="width:100px;height:12px;margin:1rem auto;"></div><div class="skeleton" style="width:200px;height:24px;margin:1rem auto;"></div></div>""", unsafe_allow_html=True)

df_total = fetch_and_process_news()
holder.empty()

# ─────────────────────────────── UI VIEWS ───────────────────────────────────

# TOP BAR
top_c1, top_c2, top_c3 = st.columns([6, 1.5, 1.5], gap="small", vertical_alignment="bottom")
with top_c1:
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:0.5rem;">
        <div style="font-family:'Playfair Display', serif; font-size:1.8rem; font-weight:900; color:#111009; letter-spacing:-0.05em; line-height:0.8;">
            El Reducto
        </div>
    </div>
    """, unsafe_allow_html=True)

with top_c2:
    if st.session_state.current_tab == "Search":
        if st.button("INICIO", key="home_btn", use_container_width=True):
            st.session_state.current_tab = "Monitor"
            st.rerun()
    else:
        if st.button("BUSCAR", key="search_btn", use_container_width=True):
            st.session_state.current_tab = "Search"
            st.rerun()

with top_c3:
    if st.session_state.current_tab == "About":
        if st.button("INICIO", key="home_btn_2", use_container_width=True):
            st.session_state.current_tab = "Monitor"
            st.rerun()
    else:
        if st.button("INFO", key="info_btn", use_container_width=True):
            st.session_state.current_tab = "About"
            st.rerun()


if st.session_state.current_tab == "Monitor":
    
    # ── RECENT INTEL ──
    st.markdown('<div class="hr-thick"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">ÚLTIMA INTELIGENCIA</div>', unsafe_allow_html=True)

    if 'risk_filter' not in st.session_state: st.session_state.risk_filter = "TODOS"
    
    st.markdown("<div id='filter-container' style='margin-bottom: 1rem;'>", unsafe_allow_html=True)
    # Using 5 columns, the last one is blank to prevent buttons from stretching too wide
    f1, f2, f3, f4, _ = st.columns([1.5, 1.2, 1.2, 1.2, 1], gap="small", vertical_alignment="center")
    
    with f1:
        if st.button("TODOS", key="f_todos", use_container_width=True): st.session_state.risk_filter = "TODOS"; st.rerun()
    with f2:
        if st.button("ALTO", key="f_alto", use_container_width=True): st.session_state.risk_filter = "ALTO"; st.rerun()
    with f3:
        if st.button("MEDIO", key="f_medio", use_container_width=True): st.session_state.risk_filter = "MEDIO"; st.rerun()
    with f4:
        if st.button("BAJO", key="f_bajo", use_container_width=True): st.session_state.risk_filter = "BAJO"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    
    active_idx = {'TODOS':1, 'ALTO':2, 'MEDIO':3, 'BAJO':4}[st.session_state.risk_filter]
    st.markdown(f"""
    <style>
    div[data-testid="column"]:nth-child({active_idx}) button {{
        background: #0E0D0B !important; color: #F4F1EB !important; border-color: #0E0D0B !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    feed_df = df_total if st.session_state.risk_filter == "TODOS" else df_total[df_total['riesgo'] == st.session_state.risk_filter]

    if len(feed_df) == 0:
        st.markdown('<div class="brief-text" style="color:#A8A39C; margin-top:1rem; text-align:center;">No hay despachos con este nivel de riesgo.</div>', unsafe_allow_html=True)

    for i, row in feed_df.head(50).iterrows(): # Show top 50
        pill_class = f"pill-{row['riesgo'].lower()}"
        st.markdown(f"""
        <div class="news-card">
            <div class="news-meta">
                <span class="pill {pill_class}">{row['riesgo']}</span>
                <span class="source-date">{row['fuente']} · {row['fecha']}</span>
            </div>
            <div class="news-title">{row['titulo']}</div>
            <div style="display:flex; justify-content:space-between;">
                <a href="{row['url']}" target="_blank" class="read-more">Ver Original ↗</a>
                <span class="geist" style="font-size:0.5rem; color:#A8A39C;">MODO LECTURA EN CONST.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.current_tab == "Search":
    st.markdown('<div class="hr-thick"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">BÚSQUEDA DE INTELIGENCIA</div>', unsafe_allow_html=True)
    
    # Custom input styling
    st.markdown("""
    <style>
    div[data-baseweb="input"] { background: transparent; border: 1px solid #DDD9D0; border-radius: 100px; padding: 0.2rem 1rem; }
    div[data-baseweb="input"]:focus-within { border-color: #111009; }
    input[type="text"] { font-family: 'DM Sans', sans-serif !important; color: #111009; }
    </style>
    """, unsafe_allow_html=True)
    
    query = st.text_input("Buscar", placeholder="Palabra clave, lugar, empresa...", label_visibility="collapsed")
    
    if query:
        filtered_df = df_total[df_total['titulo'].str.contains(query, case=False, na=False) | df_total['fuente'].str.contains(query, case=False, na=False)]
        st.markdown(f'<div class="geist" style="font-size:0.6rem; color:#A8A39C; margin-bottom:1rem; text-transform:uppercase;">SE ENCONTRARON {len(filtered_df)} RESULTADOS PARA "{query}"</div>', unsafe_allow_html=True)
        
        for i, row in filtered_df.iterrows():
            pill_class = f"pill-{row['riesgo'].lower()}"
            st.markdown(f"""
            <div class="news-card">
                <div class="news-meta">
                    <span class="pill {pill_class}">{row['riesgo']}</span>
                    <span class="source-date">{row['fuente']} · {row['fecha']}</span>
                </div>
                <div class="news-title">{row['titulo']}</div>
                <div style="display:flex; justify-content:space-between;">
                    <a href="{row['url']}" target="_blank" class="read-more">Ver Original ↗</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="brief-text" style="color:#A8A39C; margin-top:1rem;">Ingrese una palabra clave arriba para buscar a través de todo el histórico de despachos.</div>', unsafe_allow_html=True)

elif st.session_state.current_tab == "About":
    st.markdown('<div class="hr-thick"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">ACERCA DE EL REDUCTO</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="brief-card" style="border-left-color: #A8A39C;">
        <div class="brief-text" style="margin-bottom: 1rem;">
            <strong>El Reducto</strong> es una herramienta analítica de monitorización ejecutiva diseñada bajo un enfoque <em>Quiet Luxury</em>. Su propósito principal es distilar la información clave referente al sector minero en el Perú.
        </div>
        <div class="brief-text" style="margin-bottom: 1rem;">
            El sistema clasifica las noticias en tres niveles:
        </div>
        <ul style="font-family:'DM Sans', sans-serif; font-size:0.9rem; color:#6B6660; line-height:1.6; padding-left:1.5rem; margin-bottom:1.5rem;">
            <li style="margin-bottom:0.8rem;"><span class="pill pill-alto" style="margin-right:0.5rem; display:inline-block;">ALTO</span> Conflictos sociales, huelgas, protestas o violencia.</li>
            <li style="margin-bottom:0.8rem;"><span class="pill pill-medio" style="margin-right:0.5rem; display:inline-block;">MEDIO</span> Tensiones comunitarias, debates legislativos, posibles riesgos operativos.</li>
            <li><span class="pill pill-bajo" style="margin-right:0.5rem; display:inline-block;">BAJO</span> Inversiones, avances tecnológicos, reportes financieros neutros.</li>
        </ul>
        <div class="geist" style="font-size:0.55rem; color:#A8A39C; border-top:1px solid #DDD9D0; padding-top:1rem;">
            VERSIÓN 1.0 · SISTEMA NOMINAL 
        </div>
    </div>
    """, unsafe_allow_html=True)
