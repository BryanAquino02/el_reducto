

import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import plotly.express as px
import json

NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
GROQ_KEY = st.secrets["GROQ_KEY"]

st.set_page_config(
    page_title="Monitor de Conflictividad - IAMGOLD Perú",
    page_icon="⛏️",
    layout="wide"
)

st.title("⛏️ Monitor de Conflictividad Social")
st.subheader("Proyecto El Reducto — Cajamarca | IAMGOLD Perú")
st.markdown("---")

def groq_request(prompt, max_tokens=1000):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens
            },
            timeout=30
        )
        return response.json()['choices'][0]['message']['content']
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

@st.cache_data(ttl=86400)
def clasificar_noticias(titulos_json):
    titulos = json.loads(titulos_json)
    lista = "\n".join([f"{i+1}. {t}" for i, t in enumerate(titulos)])
    
    prompt = f"""Eres un analista de riesgo social para IAMGOLD Perú, empresa minera que opera 
el proyecto El Reducto en Cajamarca, Perú.

Clasifica cada noticia con exactamente uno de estos niveles:
- ALTO: conflicto social, protesta, paro, bloqueo, violencia, oposición activa a minería
- MEDIO: preocupación ambiental, minería ilegal, tensión social, demandas judiciales
- BAJO: noticia neutral, producción, inversión, desarrollo positivo

Responde SOLO con un JSON array en este formato exacto, sin explicaciones:
["ALTO","BAJO","MEDIO",...]

Noticias:
{lista}"""

    resultado = groq_request(prompt, max_tokens=500)
    try:
        clasificaciones = json.loads(resultado)
        return clasificaciones
    except:
        return ["BAJO"] * len(titulos)

# ---- OBTENER NOTICIAS ----
with st.spinner("📡 Obteniendo noticias recientes..."):
    df = obtener_noticias()

# ---- CLASIFICAR CON GROQ (1 sola llamada) ----
with st.spinner("🤖 Clasificando riesgo con IA..."):
    titulos_json = json.dumps(df['titulo'].tolist())
    clasificaciones = clasificar_noticias(titulos_json)
    
    if len(clasificaciones) == len(df):
        df['riesgo'] = clasificaciones
    else:
        df['riesgo'] = "BAJO"
    
    df['riesgo'] = df['riesgo'].map({
        'ALTO': '🔴 ALTO',
        'MEDIO': '🟡 MEDIO', 
        'BAJO': '🟢 BAJO'
    }).fillna('🟢 BAJO')

st.info(f"📰 {len(df)} noticias | Últimos 6 meses | Actualización: cada 24h")

# ---- METRICAS ----
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total", len(df))
col2.metric("🔴 Alto", len(df[df['riesgo']=='🔴 ALTO']))
col3.metric("🟡 Medio", len(df[df['riesgo']=='🟡 MEDIO']))
col4.metric("🟢 Bajo", len(df[df['riesgo']=='🟢 BAJO']))

st.markdown("---")

# ---- GRAFICOS ----
colores = {'🔴 ALTO': '#e74c3c', '🟡 MEDIO': '#f39c12', '🟢 BAJO': '#2ecc71'}
col1, col2 = st.columns(2)

with col1:
    conteo = df['riesgo'].value_counts().reset_index()
    conteo.columns = ['nivel', 'cantidad']
    fig1 = px.bar(conteo, x='nivel', y='cantidad', color='nivel',
        color_discrete_map=colores, title='Distribución de Riesgo', text='cantidad')
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

# ---- ALERTAS ALTO RIESGO ----
st.subheader("🚨 Alertas de Alto Riesgo")
df_alto = df[df['riesgo']=='🔴 ALTO'].sort_values('fecha', ascending=False)

if len(df_alto) == 0:
    st.success("No hay alertas de alto riesgo actualmente.")
else:
    for _, row in df_alto.iterrows():
        with st.expander(f"🔴 [{row['fecha']}] {row['titulo'][:80]}"):
            st.write(f"**Fuente:** {row['fuente']}")
            st.write(f"**Fecha:** {row['fecha']}")
            if st.button("🤖 Analizar impacto para IAMGOLD", key=f"btn_{row['titulo'][:20]}"):
                with st.spinner("Generando análisis..."):
                    explicacion = groq_request(f"""Eres un analista de riesgo social para IAMGOLD Perú, 
empresa minera canadiense que opera el proyecto de exploración El Reducto en Cajamarca.
Analiza en 2-3 oraciones por qué esta noticia representa un riesgo para IAMGOLD. Sé directo.
Noticia: {row['titulo']}
Fecha: {row['fecha']}
Fuente: {row['fuente']}
Responde SOLO con la explicación.""")
                    if explicacion:
                        st.warning(f"⚠️ {explicacion}")
            if row['url']:
                st.markdown(f"[🔗 Ver noticia completa]({row['url']})")

st.markdown("---")

# ---- TODAS LAS NOTICIAS ----
st.subheader("📋 Todas las Noticias")
filtro = st.selectbox("Filtrar por riesgo:", ["Todos", "🔴 ALTO", "🟡 MEDIO", "🟢 BAJO"])
df_mostrar = df[df['riesgo'] == filtro] if filtro != "Todos" else df
st.dataframe(
    df_mostrar[['fecha', 'riesgo', 'fuente', 'titulo']].reset_index(drop=True),
    use_container_width=True
)
