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

st.set_page_config(page_title="El Reducto", page_icon="⛏️", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,700;1,400;1,700&family=DM+Sans:wght@300;400;500;600&display=swap');
*,html,body,[class*="css"],.stApp{box-sizing:border-box;font-family:'DM Sans',sans-serif!important;}
.stApp{background:#F5F0E8;}
.block-container{padding:0!important;max-width:480px!important;margin:0 auto!important;}
#MainMenu,footer,header,.stDeployButton,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important;}

/* TOPBAR */
.tb{background:#F5F0E8;padding:18px 22px 12px;border-bottom:1px solid #DDD8CE;}
.tb-row{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;}
.logo{font-size:16px;font-weight:600;color:#1B2A4A;letter-spacing:-0.02em;}
.logo-sub{font-size:8px;font-weight:300;color:#6B7A8D;letter-spacing:0.08em;text-transform:uppercase;margin-top:2px;}
.badge{display:inline-flex;align-items:center;gap:5px;background:#1B2A4A;border-radius:100px;padding:5px 12px;}
.badge-dot{width:6px;height:6px;border-radius:50%;display:inline-block;}
.badge-txt{font-size:9px;font-weight:600;letter-spacing:0.06em;}
.gold{height:1px;background:linear-gradient(to right,#C9A84C,transparent);}

/* RADIO NAV */
div[data-testid="stRadio"]{padding:0!important;margin:0!important;}
div[data-testid="stRadio"]>label{display:none!important;}
div[data-testid="stRadio"]>div{
    background:#E8E2D6!important;border-radius:100px!important;
    padding:3px!important;gap:2px!important;flex-direction:row!important;
    display:flex!important;flex-wrap:nowrap!important;
}
div[data-testid="stRadio"]>div>label{
    flex:1!important;text-align:center!important;padding:5px 2px!important;
    font-size:7.5px!important;font-weight:400!important;letter-spacing:0.1em!important;
    text-transform:uppercase!important;color:#A8B4C0!important;
    border-radius:100px!important;cursor:pointer!important;margin:0!important;
    border:none!important;background:transparent!important;
}
div[data-testid="stRadio"]>div>label:has(input:checked){
    font-weight:600!important;color:#1B2A4A!important;
    background:#FFFFFF!important;box-shadow:0 1px 4px rgba(0,0,0,0.1)!important;
}
div[data-testid="stRadio"]>div>label>div:first-child{display:none!important;}
div[data-testid="stRadio"]>div>label p{color:inherit!important;font-size:inherit!important;font-family:inherit!important;margin:0!important;}

/* SCREEN */
.screen{padding:18px 22px 60px;}
.slabel{font-size:8px;font-weight:400;letter-spacing:0.22em;text-transform:uppercase;color:#6B7A8D;margin-bottom:10px;}

/* FEATURED */
.fc{background:#1B2A4A;border-radius:18px;padding:20px;margin-bottom:16px;}
.fc-meta{font-size:8.5px;color:#8A9AB0;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;}
.fc-title{font-family:'Cormorant Garamond',serif!important;font-weight:700;font-size:22px;line-height:1.15;color:#F5F0E8;letter-spacing:-0.02em;margin-bottom:14px;}
.fc-title em{font-weight:400;font-style:italic;}
.fc-div{height:1px;background:rgba(255,255,255,0.07);margin-bottom:14px;}
.fc-stats{display:flex;gap:20px;margin-bottom:14px;}
.fc-sl{font-size:7.5px;letter-spacing:0.14em;text-transform:uppercase;color:#4A5A72;margin-bottom:3px;}
.fc-sv{font-size:11px;font-weight:600;color:#F5F0E8;}
.fc-sv.r{color:#E05252!important;}
.fc-foot{display:flex;justify-content:space-between;align-items:center;}
.fc-link{font-size:10px;color:#C9A84C;border-bottom:1px solid rgba(201,168,76,0.4);padding-bottom:1px;}

/* PILLS */
.pill{font-size:7.5px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;padding:3px 9px;border-radius:100px;display:inline-block;}
.pa{border:1.5px solid #A82020;color:#A82020;}
.pm{border:1.5px solid #C9A84C;color:#C9A84C;}
.pb{border:1.5px solid #2A6B42;color:#2A6B42;}
.pad{border:1.5px solid #E05252;color:#E05252;}
.pmd{border:1.5px solid #D4A94C;color:#D4A94C;}
.pbd{border:1.5px solid #4CAF7D;color:#4CAF7D;}

/* NEWS ITEM */
.ni{display:flex;gap:10px;padding:12px 0;border-bottom:1px solid #DDD8CE;align-items:flex-start;}
.rb{width:3px;border-radius:4px;align-self:stretch;flex-shrink:0;min-height:32px;}
.rba{background:#A82020;}.rbm{background:#C9A84C;}.rbb{background:#2A6B42;}
.ns{font-size:8px;color:#A8B4C0;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:3px;}
.nt{font-size:12px;font-weight:500;color:#1B2A4A;line-height:1.4;margin-bottom:5px;}

/* DETAIL */
.ds{font-size:8.5px;color:#A8B4C0;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:10px;}
.dt{font-family:'Cormorant Garamond',serif!important;font-weight:700;font-size:28px;line-height:1.1;color:#1B2A4A;letter-spacing:-0.03em;margin-bottom:14px;}
.dt em{font-weight:400;font-style:italic;}
.sb{background:#FFF;border-left:3px solid #1B2A4A;border-radius:0 10px 10px 0;padding:14px 16px;margin-bottom:14px;font-size:12px;color:#3A4A5A;line-height:1.75;box-shadow:0 2px 8px rgba(0,0,0,0.04);}
.sl{font-size:11px;color:#1B2A4A;border-bottom:1px solid #1B2A4A;padding-bottom:1px;text-decoration:none;display:inline-block;margin-bottom:18px;}
.gdiv{height:1px;background:linear-gradient(to right,#C9A84C,transparent);margin:4px 0 16px;}
.aib{background:#1B2A4A;border-radius:14px;padding:16px;margin-top:10px;}
.ail{font-size:7.5px;color:#4A5A72;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:8px;}
.aim{font-size:8.5px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:8px;}
.ain{color:#E05252;}.aip{color:#4CAF7D;}.aio{color:#8A9AB0;}
.ait{font-size:11px;color:#A8B4C0;line-height:1.7;}

/* RADAR */
.pc{background:#1B2A4A;border-radius:18px;padding:22px 20px;margin-bottom:14px;text-align:center;}
.pn{font-family:'Cormorant Garamond',serif!important;font-size:58px;font-weight:700;color:#F5F0E8;line-height:1;letter-spacing:-0.04em;}
.pl{font-size:8px;color:#8A9AB0;letter-spacing:0.16em;text-transform:uppercase;margin-top:6px;}
.pd{font-family:'Cormorant Garamond',serif!important;font-size:16px;font-style:italic;color:#6B7A8D;margin-top:6px;}
.ab{background:#FDF0F0;border:1.5px solid #A82020;border-radius:12px;padding:12px 16px;margin-bottom:16px;}
.al{font-size:7.5px;color:#A82020;letter-spacing:0.15em;text-transform:uppercase;font-weight:600;margin-bottom:4px;}
.at{font-size:11px;color:#5A2020;line-height:1.55;}
.sc{background:#FFF;border-radius:12px;padding:12px 14px;box-shadow:0 2px 8px rgba(0,0,0,0.04);margin-bottom:8px;}
.scl{font-size:7.5px;color:#A8B4C0;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:4px;}
.scv{font-size:13px;font-weight:600;color:#1B2A4A;}

/* ACERCA */
.ahn{font-family:'Cormorant Garamond',serif!important;font-size:38px;font-weight:700;color:#1B2A4A;line-height:1.05;letter-spacing:-0.04em;margin-bottom:6px;}
.ahs{font-size:8.5px;color:#C9A84C;letter-spacing:0.18em;text-transform:uppercase;}
.fcard{background:#FFF;border-radius:12px;padding:12px 14px;margin-bottom:8px;box-shadow:0 2px 8px rgba(0,0,0,0.04);display:flex;gap:12px;align-items:flex-start;}
.fnum{font-family:'Cormorant Garamond',serif!important;font-size:16px;font-style:italic;color:#C9A84C;min-width:20px;flex-shrink:0;}
.ftxt{font-size:11.5px;color:#3A4A5A;line-height:1.6;}
.bname{font-family:'Cormorant Garamond',serif!important;font-size:22px;font-style:italic;color:#1B2A4A;margin-bottom:12px;}
.btxt{font-size:11.5px;color:#3A4A5A;line-height:1.8;margin-bottom:10px;}
.bfoot{font-size:8.5px;color:#A8B4C0;letter-spacing:0.12em;text-transform:uppercase;margin-top:14px;}

/* SKELETON */
.sk{background:linear-gradient(90deg,#E8E2D6 25%,#F0EBE0 50%,#E8E2D6 75%);background-size:200% 100%;animation:sh 1.4s infinite;border-radius:6px;}
@keyframes sh{0%{background-position:200% 0}100%{background-position:-200% 0}}

/* INPUTS & BUTTONS */
div[data-baseweb="input"]{background:#FFF!important;border:1.5px solid #DDD8CE!important;border-radius:100px!important;}
div[data-baseweb="input"]:focus-within{border-color:#1B2A4A!important;}
input[type="text"]{font-family:'DM Sans',sans-serif!important;font-size:13px!important;color:#1B2A4A!important;background:transparent!important;}
.stButton>button{background:transparent!important;color:#6B7A8D!important;border:1.5px solid #DDD8CE!important;border-radius:100px!important;font-family:'DM Sans',sans-serif!important;font-size:8.5px!important;font-weight:500!important;letter-spacing:0.1em!important;text-transform:uppercase!important;padding:0.4rem 1rem!important;box-shadow:none!important;transition:all 0.18s!important;}
.stButton>button:hover{background:#1B2A4A!important;color:#F5F0E8!important;border-color:#1B2A4A!important;}
[data-testid="stPlotlyChart"]{border-radius:14px;overflow:hidden;}
</style>
""", unsafe_allow_html=True)


# ── DB ────────────────────────────────────────────────────────────────────────
def init_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH,'w') as f: json.dump({'date':'','articles':[],'history':[]},f)

def load_db():
    try: return json.load(open(DB_PATH,'r'))
    except: return {'date':'','articles':[],'history':[]}

def save_db(data):
    with open(DB_PATH,'w') as f: json.dump(data,f)

init_db()


# ── GROQ ──────────────────────────────────────────────────────────────────────
GEO = """Eres una ingeniera geóloga peruana con 18 años de experiencia en minería metálica,
especializada en conflictos socioambientales en la sierra norte del Perú.
Conoces el proyecto Conga de IAMGOLD en Cajamarca, la normativa del MINEM, el OEFA y la dinámica
entre empresas extractivas y comunidades campesinas. Eres directa y técnica."""

def groq(prompt, system=None, max_tokens=600):
    try:
        msgs = []
        if system: msgs.append({"role":"system","content":system})
        msgs.append({"role":"user","content":prompt})
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
            json={"model":"llama-3.1-8b-instant","messages":msgs,"max_tokens":max_tokens},timeout=20)
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        logging.warning(f"Groq: {e}"); return None


# ── FETCH ─────────────────────────────────────────────────────────────────────
QUERIES = ["mineria+Cajamarca+conflicto","mineria+Cajamarca+comunidades",
           "protesta+minera+Cajamarca","IAMGOLD+Peru","mineria+Peru+conflicto",
           "conflictos+mineros+Peru","inversion+minera+Peru","protesta+minera+Peru"]

def fetch_rss(queries, fecha_limite):
    headers = {"User-Agent":"Mozilla/5.0"}
    todos, seen = [], set()
    for q in queries:
        try:
            resp = requests.get(f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=PE&ceid=PE:es-419",
                headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text,'xml')
            for item in soup.find_all('item'):
                titulo  = item.find('title').get_text(strip=True) if item.find('title') else ""
                pub_raw = item.find('pubDate').get_text(strip=True) if item.find('pubDate') else ""
                fuente  = item.find('source').get_text(strip=True) if item.find('source') else "Google News"
                link    = item.find('link').get_text(strip=True) if item.find('link') else ""
                if not titulo or titulo in seen: continue
                seen.add(titulo)
                try:
                    dt = parsedate_to_datetime(pub_raw).replace(tzinfo=None)
                    if dt < fecha_limite: continue
                    todos.append({"titulo":titulo,"fuente":fuente,
                        "fecha":dt.strftime('%d.%m.%y'),"fecha_iso":dt.strftime('%Y-%m-%d'),"url":link})
                except: continue
        except Exception as e: logging.warning(f"RSS '{q}': {e}")
    return todos

def classify(df):
    titulos = df['titulo'].tolist()
    clases  = []
    for i in range(0, min(len(titulos),60), 20):
        lote  = titulos[i:i+20]
        lista = "\n".join([f"{j+1}. {x}" for j,x in enumerate(lote)])
        res   = groq(f'Clasifica noticias mineras peruanas. SOLO JSON array. '
                     f'"ALTO"=protesta/huelga/paro/bloqueo, "MEDIO"=tensión/diálogo/riesgo, "BAJO"=inversión/neutro.\n'
                     f'Noticias:\n{lista}\nArray JSON:', max_tokens=300)
        try:
            if res:
                s,e = res.find('['), res.rfind(']')+1
                if s!=-1 and e>s: clases.extend(json.loads(res[s:e]))
                else: clases.extend(["BAJO"]*len(lote))
            else: clases.extend(["BAJO"]*len(lote))
        except: clases.extend(["BAJO"]*len(lote))
        time.sleep(0.8)
    clases.extend(["BAJO"]*(len(titulos)-len(clases)))
    df['riesgo'] = clases[:len(df)]
    def norm(x):
        x=str(x).upper()
        if 'ALTO' in x: return 'ALTO'
        if 'MEDIO' in x: return 'MEDIO'
        return 'BAJO'
    df['riesgo'] = df['riesgo'].apply(norm)
    return df

def keywords(df, n=5):
    sw = {'de','la','el','en','y','a','los','del','que','con','por','las','un','una','se','es','al',
          'para','su','sus','como','más','no','este','esta','sobre','entre','fue','han','hay','pero',
          'sin','también','desde','hasta','durante','tiene','pueden','nuevo','nuevos','tras','ante','según'}
    words = []
    for t in df['titulo']:
        words.extend([w for w in re.findall(r'\b[a-záéíóúñ]{4,}\b',t.lower()) if w not in sw])
    return Counter(words).most_common(n)

@st.cache_data(ttl=3600)
def get_news():
    db=load_db(); today=datetime.now().strftime('%Y-%m-%d')
    if db.get('date')==today and db.get('articles'):
        return pd.DataFrame(db['articles'])
    todos = fetch_rss(QUERIES, datetime.now()-timedelta(days=90))
    if not todos:
        return pd.DataFrame(columns=['titulo','fuente','fecha','fecha_iso','url','riesgo'])
    df = pd.DataFrame(todos).drop_duplicates(subset='titulo').sort_values('fecha_iso',ascending=False).reset_index(drop=True)
    df = classify(df)
    history = db.get('history',[])
    td = df[df['fecha_iso']==today]
    entry = {'fecha':today,'alto':int((td['riesgo']=='ALTO').sum()),
             'medio':int((td['riesgo']=='MEDIO').sum()),'bajo':int((td['riesgo']=='BAJO').sum())}
    if not any(h['fecha']==today for h in history): history.append(entry)
    history = sorted(history,key=lambda x:x['fecha'])[-30:]
    db.update({'date':today,'articles':df.to_dict('records'),'history':history})
    save_db(db); return df


# ── SESSION ───────────────────────────────────────────────────────────────────
for k,v in {'tab':'HOY','prev_tab':'HOY','selected':None,'summary':{},'impact':{},'company':'IAMGOLD'}.items():
    if k not in st.session_state: st.session_state[k]=v


# ── HELPERS ───────────────────────────────────────────────────────────────────
def open_article(row):
    st.session_state.prev_tab = st.session_state.tab
    st.session_state.selected = row
    st.session_state.tab = 'DETALLE'

def pill(r, dark=False):
    cls = {'ALTO':'pad','MEDIO':'pmd','BAJO':'pbd'} if dark else {'ALTO':'pa','MEDIO':'pm','BAJO':'pb'}
    return f'<span class="pill {cls.get(r,"pb")}">{r}</span>'

def rbar(r):
    cls = {'ALTO':'rba','MEDIO':'rbm','BAJO':'rbb'}.get(r,'rbb')
    return f'<div class="rb {cls}"></div>'

def news_row(row, key):
    c1,c2 = st.columns([12,1],gap="small")
    with c1:
        st.markdown(f'<div class="ni">{rbar(row["riesgo"])}<div style="flex:1"><div class="ns">{row["fuente"]} · {row["fecha"]}</div><div class="nt">{row["titulo"]}</div>{pill(row["riesgo"])}</div></div>',unsafe_allow_html=True)
    with c2:
        if st.button("→",key=key): open_article(row); st.rerun()

def skeleton():
    st.markdown("""<div style="padding:20px 22px;">
    <div class="sk" style="height:10px;width:35%;margin-bottom:16px;"></div>
    <div style="background:#1B2A4A;border-radius:18px;padding:20px;margin-bottom:20px;">
        <div class="sk" style="height:8px;width:50%;margin-bottom:12px;background:#2A3A5A;"></div>
        <div class="sk" style="height:16px;width:90%;margin-bottom:8px;background:#2A3A5A;"></div>
        <div class="sk" style="height:16px;width:70%;margin-bottom:16px;background:#2A3A5A;"></div>
    </div>
    <div class="sk" style="height:8px;width:28%;margin-bottom:14px;"></div>
    <div class="sk" style="height:44px;width:100%;margin-bottom:8px;border-radius:8px;"></div>
    <div class="sk" style="height:44px;width:100%;border-radius:8px;"></div>
    </div>""",unsafe_allow_html=True)


# ── LOAD DATA ─────────────────────────────────────────────────────────────────
ph = st.empty()
with ph: skeleton()
df = get_news()
ph.empty()

today_str   = datetime.now().strftime('%Y-%m-%d')
alert_count = int((df[df['fecha_iso']==today_str]['riesgo']=='ALTO').sum()) if len(df)>0 else 0
dot_color   = "#A82020" if alert_count>=3 else "#C9A84C" if alert_count>=1 else "#2A6B42"
weekday_es  = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"][datetime.now().weekday()]
today_label = datetime.now().strftime("%-d de %B").capitalize()


# ── TOPBAR ────────────────────────────────────────────────────────────────────
NAV = ["HOY","FEED","BUSCAR","RADAR","ACERCA"]

st.markdown(f"""
<div class="tb">
  <div class="tb-row">
    <div><div class="logo">El Reducto</div><div class="logo-sub">{weekday_es} {today_label} · Lima</div></div>
    <div class="badge">
      <span class="badge-dot" style="background:{dot_color};"></span>
      <span class="badge-txt" style="color:{dot_color};">{alert_count} alertas hoy</span>
    </div>
  </div>
</div>""",unsafe_allow_html=True)

current  = st.session_state.prev_tab if st.session_state.tab=="DETALLE" else st.session_state.tab
nav_idx  = NAV.index(current) if current in NAV else 0
selected = st.radio("",NAV,index=nav_idx,horizontal=True,label_visibility="collapsed",key="nav_radio")

if selected != current:
    st.session_state.tab = selected
    st.session_state.selected = None
    st.rerun()

st.markdown('<div class="gold"></div>',unsafe_allow_html=True)


# ── HOY ───────────────────────────────────────────────────────────────────────
if st.session_state.tab=="HOY":
    st.markdown('<div class="screen">',unsafe_allow_html=True)
    if len(df)==0:
        st.markdown('<div style="text-align:center;padding:40px;"><div style="font-family:Cormorant Garamond,serif;font-size:20px;font-style:italic;color:#A8B4C0;">Sin noticias disponibles</div></div>',unsafe_allow_html=True)
    else:
        top   = df.iloc[0]
        words = top['titulo'].split()
        mid   = max(2,len(words)//2)
        l1,l2 = ' '.join(words[:mid]),' '.join(words[mid:])
        st.markdown(f"""
        <div class="slabel" style="display:flex;justify-content:space-between;"><span>Noticia principal</span><span style="color:#C9A84C;">1 / {min(len(df),8)}</span></div>
        <div class="fc">
          <div class="fc-meta">{top['fuente']} · {top['fecha']}</div>
          <div class="fc-title">{l1}<br><em>{l2}</em></div>
          <div class="fc-stats">
            <div><div class="fc-sl">Fuente</div><div class="fc-sv">{top['fuente']}</div></div>
            <div><div class="fc-sl">Riesgo</div><div class="fc-sv {'r' if top['riesgo']=='ALTO' else ''}">{top['riesgo']}</div></div>
            <div><div class="fc-sl">Fecha</div><div class="fc-sv">{top['fecha']}</div></div>
          </div>
          <div class="fc-div"></div>
          <div class="fc-foot">{pill(top['riesgo'],dark=True)}<span class="fc-link">Abrir noticia →</span></div>
        </div>""",unsafe_allow_html=True)
        if st.button("Abrir noticia principal →",use_container_width=True,key="open_top"):
            open_article(top); st.rerun()
        st.markdown('<div style="height:12px;"></div><div class="gold" style="margin-bottom:12px;"></div>',unsafe_allow_html=True)
        st.markdown('<div class="slabel">Últimas noticias</div>',unsafe_allow_html=True)
        for i,row in df.iloc[1:8].iterrows(): news_row(row,f"h{i}")
    st.markdown('</div>',unsafe_allow_html=True)


# ── FEED ──────────────────────────────────────────────────────────────────────
elif st.session_state.tab=="FEED":
    st.markdown('<div class="screen">',unsafe_allow_html=True)
    FOPTS = ["TODOS","ALTO","MEDIO","BAJO"]
    fidx  = FOPTS.index(st.session_state.get('feed_f','TODOS'))
    ff    = st.radio("",FOPTS,index=fidx,horizontal=True,label_visibility="collapsed",key="feed_radio")
    st.session_state['feed_f'] = ff
    feed  = df if ff=="TODOS" else df[df['riesgo']==ff]
    st.markdown(f'<div class="slabel" style="margin-top:12px;">{len(feed)} noticias · {ff}</div>',unsafe_allow_html=True)
    if len(feed)==0:
        st.markdown(f'<div style="text-align:center;padding:30px;"><div style="font-family:Cormorant Garamond,serif;font-size:18px;font-style:italic;color:#A8B4C0;">Sin noticias {ff.lower()}</div></div>',unsafe_allow_html=True)
    else:
        for i,row in feed.head(40).iterrows(): news_row(row,f"f{i}")
    st.markdown('</div>',unsafe_allow_html=True)


# ── BUSCAR ────────────────────────────────────────────────────────────────────
elif st.session_state.tab=="BUSCAR":
    st.markdown('<div class="screen">',unsafe_allow_html=True)
    q = st.text_input("",placeholder="🔍  Buscar por tema, fuente o empresa...",label_visibility="collapsed")
    if not q:
        kw = keywords(df,8)
        if kw:
            st.markdown('<div class="slabel" style="margin-top:10px;">Temas frecuentes</div>',unsafe_allow_html=True)
            st.markdown('<div style="line-height:2.4;">'+" ".join([f'<span class="pill pm" style="margin:3px 2px;">{w}</span>' for w,_ in kw])+'</div>',unsafe_allow_html=True)
        st.markdown('<div style="height:12px;"></div><div class="slabel">Sugerencias</div>',unsafe_allow_html=True)
        st.markdown('<div style="line-height:2.4;">'+" ".join([f'<span class="pill pm" style="margin:3px 2px;">{t}</span>' for t in ["IAMGOLD","Cajamarca","Conga","Huelga","MINEM","Comunidades"]])+'</div>',unsafe_allow_html=True)
    else:
        mask    = df['titulo'].str.contains(q,case=False,na=False)|df['fuente'].str.contains(q,case=False,na=False)
        results = df[mask]
        st.markdown(f'<div class="slabel" style="margin-top:10px;">{len(results)} resultados para "{q}"</div>',unsafe_allow_html=True)
        if len(results)==0:
            st.markdown(f'<div style="text-align:center;padding:30px;"><div style="font-family:Cormorant Garamond,serif;font-size:18px;font-style:italic;color:#A8B4C0;">Sin resultados para "{q}"</div></div>',unsafe_allow_html=True)
        else:
            for i,row in results.iterrows(): news_row(row,f"s{i}")
    st.markdown('</div>',unsafe_allow_html=True)


# ── DETALLE ───────────────────────────────────────────────────────────────────
elif st.session_state.tab=="DETALLE" and st.session_state.selected is not None:
    row    = st.session_state.selected
    art_id = str(hash(row['titulo']))
    st.markdown('<div class="screen">',unsafe_allow_html=True)
    if st.button("← Volver",key="back"):
        st.session_state.tab = st.session_state.prev_tab
        st.session_state.selected = None; st.rerun()
    words  = row['titulo'].split()
    mid    = max(2,len(words)//2)
    l1,l2  = ' '.join(words[:mid]),' '.join(words[mid:])
    st.markdown(f'<div class="ds">{row["fuente"]} · {row["fecha"]}</div><div class="dt">{l1}<br><em>{l2}</em></div>{pill(row["riesgo"])}<div style="height:16px;"></div>',unsafe_allow_html=True)
    st.markdown('<div class="gold" style="margin-bottom:14px;"></div><div class="slabel">Resumen de la noticia</div>',unsafe_allow_html=True)
    if art_id not in st.session_state.summary:
        with st.spinner("Generando resumen..."):
            r = groq(f'Resume en 3 oraciones esta noticia minera peruana, sin preamble: "{row["titulo"]}"',system=GEO,max_tokens=200)
            st.session_state.summary[art_id] = r or "No se pudo generar el resumen."
    st.markdown(f'<div class="sb">{st.session_state.summary[art_id]}</div>',unsafe_allow_html=True)
    if row.get('url') and str(row['url']).startswith('http'):
        st.markdown(f'<a href="{row["url"]}" target="_blank" class="sl">Ver fuente original ↗</a>',unsafe_allow_html=True)
    st.markdown('<div class="gdiv"></div><div class="slabel">Análisis de impacto</div>',unsafe_allow_html=True)
    company = st.text_input("",value=st.session_state.company,placeholder="Empresa...",label_visibility="collapsed",key="co")
    st.session_state.company = company
    if st.button(f"¿Cómo afecta a {company}? →",use_container_width=True,key="analyze"):
        ck = f"{art_id}_{company}"
        with st.spinner("Analizando..."):
            imp = groq(f'Analiza cómo afecta a {company} en Perú. Empieza con "POSITIVO:", "NEGATIVO:" o "NEUTRO:". Máx 4 oraciones.\nNoticia: "{row["titulo"]}"\nContexto: "{st.session_state.summary.get(art_id,"")}"',system=GEO,max_tokens=300)
            st.session_state.impact[ck] = imp or "No se pudo generar el análisis."
    ck = f"{art_id}_{company}"
    if ck in st.session_state.impact:
        txt = st.session_state.impact[ck]
        u   = txt.upper()
        if u.startswith("POSITIVO"):   ic,il = "aip","▲ IMPACTO POSITIVO"
        elif u.startswith("NEGATIVO"): ic,il = "ain","▼ IMPACTO NEGATIVO"
        else:                          ic,il = "aio","● IMPACTO NEUTRO"
        st.markdown(f'<div class="aib"><div class="ail">Análisis IA · Especialista en Minería Peruana</div><div class="aim {ic}">{il}</div><div class="ait">{txt}</div></div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)


# ── RADAR ─────────────────────────────────────────────────────────────────────
elif st.session_state.tab=="RADAR":
    st.markdown('<div class="screen">',unsafe_allow_html=True)
    st.markdown('<div class="slabel">Radar de riesgo territorial</div>',unsafe_allow_html=True)
    sem   = (datetime.now()-timedelta(days=7)).strftime('%Y-%m-%d')
    dfs   = df[df['fecha_iso']>=sem] if len(df)>0 else pd.DataFrame()
    tot   = len(dfs)
    altos = int((dfs['riesgo']=='ALTO').sum()) if tot>0 else 0
    medios= int((dfs['riesgo']=='MEDIO').sum()) if tot>0 else 0
    ratio = altos/tot if tot>0 else 0
    diag  = "Semana de alta tensión" if ratio>0.4 else "Semana de tensión moderada" if ratio>0.2 else "Semana tranquila"
    st.markdown(f'<div class="pc"><div class="pn">{altos}</div><div class="pl">Noticias ALTO esta semana</div><div class="pd">{diag}</div></div>',unsafe_allow_html=True)

    if len(df)>0:
        dc = df.copy(); dc['fecha_iso']=pd.to_datetime(dc['fecha_iso'])
        prev = pd.date_range(end=datetime.now()-timedelta(days=7),periods=14,freq='D')
        pa   = [int((dc[dc['fecha_iso'].dt.strftime('%Y-%m-%d')==f.strftime('%Y-%m-%d')]['riesgo']=='ALTO').sum()) for f in prev]
        prom = sum(pa)/len(pa) if pa else 0
        if altos>prom*1.5 and prom>0:
            st.markdown(f'<div class="ab"><div class="al">⚠ Anomalía detectada</div><div class="at">Actividad ALTO inusualmente alta ({altos} vs. promedio {prom:.1f}).</div></div>',unsafe_allow_html=True)

    ft  = dfs['fuente'].value_counts().index[0] if tot>0 else "—"
    kw  = keywords(dfs,3) if tot>0 else []
    kws = " · ".join([w for w,_ in kw]) if kw else "—"
    c1,c2 = st.columns(2,gap="small")
    with c1:
        st.markdown(f'<div class="sc"><div class="scl">Noticias MEDIO</div><div class="scv">{medios}</div></div>',unsafe_allow_html=True)
        st.markdown(f'<div class="sc"><div class="scl">Fuente más activa</div><div class="scv" style="font-size:11px;">{ft}</div></div>',unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="sc"><div class="scl">Total procesado</div><div class="scv">{tot}</div></div>',unsafe_allow_html=True)
        st.markdown(f'<div class="sc"><div class="scl">Keywords</div><div class="scv" style="font-size:10px;">{kws}</div></div>',unsafe_allow_html=True)

    st.markdown('<div class="gold" style="margin:14px 0;"></div><div class="slabel">Tendencia · últimos 14 días</div>',unsafe_allow_html=True)
    if len(df)>0:
        dp = df.copy(); dp['fecha_iso']=pd.to_datetime(dp['fecha_iso'])
        fechas = pd.date_range(end=datetime.now(),periods=14,freq='D')
        td = [{'fecha':f,
               'ALTO': int((dp[dp['fecha_iso'].dt.strftime('%Y-%m-%d')==f.strftime('%Y-%m-%d')]['riesgo']=='ALTO').sum()),
               'MEDIO':int((dp[dp['fecha_iso'].dt.strftime('%Y-%m-%d')==f.strftime('%Y-%m-%d')]['riesgo']=='MEDIO').sum()),
               'BAJO': int((dp[dp['fecha_iso'].dt.strftime('%Y-%m-%d')==f.strftime('%Y-%m-%d')]['riesgo']=='BAJO').sum())} for f in fechas]
        dplot = pd.DataFrame(td)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dplot['fecha'],y=dplot['ALTO'],name='ALTO',line=dict(color='#A82020',width=2.5),fill='tozeroy',fillcolor='rgba(168,32,32,0.08)'))
        fig.add_trace(go.Scatter(x=dplot['fecha'],y=dplot['MEDIO'],name='MEDIO',line=dict(color='#C9A84C',width=1.8,dash='dot')))
        fig.add_trace(go.Scatter(x=dplot['fecha'],y=dplot['BAJO'],name='BAJO',line=dict(color='#2A6B42',width=1.5)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='DM Sans',color='#6B7A8D',size=10),margin=dict(l=0,r=0,t=10,b=0),height=200,
            legend=dict(orientation='h',y=-0.35,x=0,font=dict(size=9)),
            xaxis=dict(showgrid=False,tickformat='%d %b',tickfont=dict(size=9),color='#6B7A8D'),
            yaxis=dict(showgrid=True,gridcolor='rgba(0,0,0,0.06)',zeroline=False,tickfont=dict(size=9)))
        st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
    st.markdown('</div>',unsafe_allow_html=True)


# ── ACERCA ────────────────────────────────────────────────────────────────────
elif st.session_state.tab=="ACERCA":
    st.markdown('<div class="screen">',unsafe_allow_html=True)
    st.markdown("""
    <div style="padding-bottom:20px;border-bottom:1px solid #DDD8CE;margin-bottom:22px;">
        <div class="ahn">El<br><em style="font-weight:400;">Reducto</em></div>
        <div class="ahs">Inteligencia Minera · Perú</div>
    </div>
    <div class="slabel">Qué es</div>
    <div style="font-size:12.5px;color:#3A4A5A;line-height:1.75;margin-bottom:22px;">
        <strong style="color:#1B2A4A;font-weight:600;">El Reducto</strong> es un monitor de inteligencia ejecutiva
        especializado en el sector minero del Perú. Agrega, clasifica y analiza noticias en tiempo real.
    </div>
    <div class="slabel">Para qué sirve</div>
    <div class="fcard"><div class="fnum">01</div><div class="ftxt">Monitorear conflictos sociales y riesgos operativos en zonas mineras.</div></div>
    <div class="fcard"><div class="fnum">02</div><div class="ftxt">Clasificar noticias automáticamente por nivel de riesgo: ALTO, MEDIO o BAJO.</div></div>
    <div class="fcard"><div class="fnum">03</div><div class="ftxt">Analizar el impacto de cada noticia en empresas específicas con criterio de IA especializada.</div></div>
    <div class="fcard"><div class="fnum">04</div><div class="ftxt">Detectar anomalías y tendencias de escalada mediante análisis de series temporales.</div></div>
    <div style="height:22px;"></div>
    <div class="gold" style="margin-bottom:18px;"></div>
    <div class="bname">Bryan Perez Aquino</div>
    <div class="btxt">El Reducto fue diseñado y desarrollado por <strong style="color:#1B2A4A;">Bryan Perez Aquino</strong>
    como proyecto de portafolio profesional. Combina scraping de noticias en tiempo real, clasificación automática
    por nivel de riesgo mediante NLP, y análisis de impacto generado por inteligencia artificial especializada en
    minería peruana. Todas las opiniones y análisis que lees son generados por IA, no por un humano experto.</div>
    <div class="btxt">Construido con Python, Streamlit y modelos de lenguaje de gran escala (LLMs) como parte
    de una formación en Ciencia de Datos con IA.</div>
    <div class="bfoot">Lima, Perú · 2025</div>
    """,unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)
