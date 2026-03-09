
import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from transformers import MarianMTModel, MarianTokenizer, pipeline
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import plotly.express as px
import time

NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
GROQ_KEY = st.secrets["GROQ_KEY"]

st.set_page_config(
    page_title="Monitor de Conflictividad Social - IAMGOLD Perú",
    page_icon="⛏️",
    layout="wide"
)

st.title("⛏️ Monitor de Conflictividad Social")
st.subheader("Proyecto El Reducto — Cajamarca | IAMGOLD Perú")
st.markdown("---")

@st.cache_resource
def cargar_modelos():
    tok = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-es-en")
    mod = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-es-en")
    clf = pipeline("zero-shot-classification", model="cross-encoder/nli-MiniLM2-L6-H768")
    return tok, mod, clf

with st.spinner("Cargando modelos de IA..."):
    tok, mod, clf = cargar_modelos()

def traducir(texto):
    try:
        tokens = tok([texto[:200]], return_tensors="pt", padding=True)
        translated = mod.generate(**tokens)
        return tok.decode(translated[0], skip_special_tokens=True)
    except:
        return texto

etiquetas = [
    "social conflict, protest, strike, violence, opposition to mining",
    "environmental concern, illegal mining, contamination, community resistance",
    "neutral news, production, investment, positive mining development"
]

def clasificar(titulo):
    traduccion = traducir(titulo)
    resultado = clf(traduccion, etiquetas)
    top = resultado['labels'][0]
    if "social conflict" in top:
        return "🔴 ALTO"
    elif "environmental" in top:
        return "🟡 MEDIO"
    else:
        return "🟢 BAJO"

def explicar_alerta(titulo, fecha, fuente):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        }
        prompt = f"""Eres un analista de riesgo social para IAMGOLD Perú, empresa minera canadiense 
que opera el proyecto de exploración El Reducto en Cajamarca.
Analiza esta noticia y explica en 2-3 oraciones por qué representa un riesgo 
para IAMGOLD. Sé directo y específico.
Noticia: {titulo}
Fecha: {fecha}
Fuente: {fuente}
Responde SOLO con la explicación, sin títulos ni formato."""
        response = requests.post(url, headers=headers, json={
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200
        })
        return response.json()['choices'][0]['message']['content']
    except:
        return "No se pudo generar explicación."

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
        "IAMGOLD+Peru"
    ]
    todos = []
    for q in queries:
        try:
            url = f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=PE&ceid=PE:es-419"
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'xml')
            for item in soup.find_all('item'):
                titulo = item.find('title').get_text(strip=True) if item.find('title') else ""
                pub_date = item.find('pubDate').get_text(strip=True) if item.find('pubDate') else ""
                fuente = item.find('source').get_text(strip=True) if item.find('source') else "Google News"
                link = item.find('link').get_text(strip=True) if item.find('link') else ""
                try:
                    fecha_dt = parsedate_to_datetime(pub_date).replace(tzinfo=None)
                    if fecha_dt < fecha_limite:
                        continue
                    fecha_str = fecha_dt.strftime('%Y-%m-%d')
                except:
                    continue
                if titulo:
                    todos.append({"titulo": titulo, "fuente": fuente, "fecha": fecha_str, "url": link})
        except:
            continue
    df = pd.DataFrame(todos).drop_duplicates(subset='titulo').reset_index(drop=True)
    return df.sort_values('fecha', ascending=False).reset_index(drop=True)

with st.spinner("Obteniendo noticias recientes..."):
    df = obtener_noticias()

st.info(f"📰 {len(df)} noticias analizadas | Período: últimos 6 meses | Actualización: cada 24h")

with st.spinner("Analizando riesgo con IA..."):
    df['riesgo'] = df['titulo'].apply(clasificar)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Noticias", len(df))
col2.metric("🔴 Alto Riesgo", len(df[df['riesgo']=='🔴 ALTO']))
col3.metric("🟡 Medio Riesgo", len(df[df['riesgo']=='🟡 MEDIO']))
col4.metric("🟢 Bajo Riesgo", len(df[df['riesgo']=='🟢 BAJO']))

st.markdown("---")

colores = {'🔴 ALTO': '#e74c3c', '🟡 MEDIO': '#f39c12', '🟢 BAJO': '#2ecc71'}
col1, col2 = st.columns(2)

with col1:
    conteo = df['riesgo'].value_counts().reset_index()
    conteo.columns = ['nivel', 'cantidad']
    fig1 = px.bar(conteo, x='nivel', y='cantidad', color='nivel',
        color_discrete_map=colores, title='Distribucion de Riesgo', text='cantidad')
    fig1.update_layout(showlegend=False, plot_bgcolor='white')
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    df['mes'] = pd.to_datetime(df['fecha']).dt.to_period('M').astype(str)
    tendencia = df.groupby(['mes', 'riesgo']).size().reset_index(name='cantidad')
    fig2 = px.line(tendencia, x='mes', y='cantidad', color='riesgo',
        color_discrete_map=colores, title='Tendencia por Mes', markers=True)
    fig2.update_layout(plot_bgcolor='white')
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

st.subheader("🚨 Alertas de Alto Riesgo")
df_alto = df[df['riesgo']=='🔴 ALTO'].sort_values('fecha', ascending=False)

for _, row in df_alto.iterrows():
    with st.expander(f"🔴 [{row['fecha']}] {row['titulo'][:80]}"):
        st.write(f"**Fuente:** {row['fuente']}")
        st.write(f"**Fecha:** {row['fecha']}")
        if st.button(f"Generar análisis IA", key=row['titulo'][:30]):
            with st.spinner("Analizando con IA..."):
                explicacion = explicar_alerta(row['titulo'], row['fecha'], row['fuente'])
                st.warning(f"🤖 **Análisis IA:** {explicacion}")
        if row['url']:
            st.markdown(f"[Ver noticia completa]({row['url']})")

st.markdown("---")

st.subheader("📋 Todas las Noticias")
filtro = st.selectbox("Filtrar por riesgo:", ["Todos", "🔴 ALTO", "🟡 MEDIO", "🟢 BAJO"])
if filtro != "Todos":
    df_mostrar = df[df['riesgo'] == filtro]
else:
    df_mostrar = df
st.dataframe(df_mostrar[['fecha', 'riesgo', 'fuente', 'titulo']].reset_index(drop=True), use_container_width=True)
