"""
Módulo Operação — Análise de Performance de Entrega
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import generate_mock_ifood_data, process_ifood_data, COORDS_BAIRROS

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Operação | DeliveryPro",
    page_icon="🚚",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0a0a0f; color: #e8e8f0; }
[data-testid="stSidebar"] { background: #111118 !important; border-right: 1px solid #1e1e2e; }
[data-testid="metric-container"] { background: #111118 !important; border: 1px solid #1e1e2e !important; border-radius: 10px !important; padding: 16px !important; }
[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif !important; color: #34d399 !important; }
h1, h2, h3 { font-family: 'Syne', sans-serif !important; color: #e8e8f0 !important; }
.section-header { font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 700; color: #e8e8f0; margin: 28px 0 14px 0; padding-bottom: 10px; border-bottom: 1px solid #1e1e2e; }
.insight-box { background: #111118; border: 1px solid #1e1e2e; border-left: 3px solid #f59e0b; border-radius: 8px; padding: 16px 20px; margin: 12px 0; }
.insight-box.green { border-left-color: #34d399; }
.insight-box.red { border-left-color: #f87171; }
.insight-title { font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 700; color: #e8e8f0; margin-bottom: 4px; }
.insight-text { font-size: 13px; color: #70708a; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  DADOS
# ─────────────────────────────────────────────
if "df_main" not in st.session_state:
    df_raw = generate_mock_ifood_data(800)
    st.session_state["df_main"] = process_ifood_data(df_raw)

df = st.session_state["df_main"].copy()

# ─────────────────────────────────────────────
#  SIDEBAR — Filtros
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:800;color:#e8e8f0;padding:8px 0;">
        🚚 Operação
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.page_link("streamlit_app.py",         label="🏠  Visão Geral")
    st.page_link("pages/1_Operacao.py",      label="🚚  Operação")
    st.page_link("pages/2_Lucratividade.py", label="💰  Lucratividade")
    st.page_link("pages/3_Fidelizacao.py",   label="❤️  Fidelização")
    st.markdown("---")

    st.markdown("**🔍 Filtros**")

    min_date = df["Data do Pedido"].min().date()
    max_date = df["Data do Pedido"].max().date()
    date_range = st.date_input("Período", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    bairros_disp = sorted(df["Bairro"].dropna().unique().tolist())
    bairros_sel = st.multiselect("Bairros", bairros_disp, default=bairros_disp)

# Aplicar filtros
if len(date_range) == 2:
    df = df[(df["Data do Pedido"].dt.date >= date_range[0]) & (df["Data do Pedido"].dt.date <= date_range[1])]
if bairros_sel:
    df = df[df["Bairro"].isin(bairros_sel)]

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:28px;">
    <div style="font-family:'Syne',sans-serif;font-size:30px;font-weight:800;color:#e8e8f0;line-height:1.2;">
        🚚 Operação & Logística
    </div>
    <div style="color:#60607a;font-size:15px;margin-top:6px;">
        Descubra onde sua entrega perde tempo — e clientes.
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  KPIs
# ─────────────────────────────────────────────
df_ok = df[~df["is_cancelado"]]
df_cancel = df[df["is_cancelado"]]

tempo_medio  = df_ok["Tempo de Entrega (min)"].mean()
tempo_max    = df_ok["Tempo de Entrega (min)"].max()
tx_cancel    = len(df_cancel) / len(df) * 100 if len(df) > 0 else 0
perda_cancel = df_cancel["Valor Bruto"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Tempo Médio de Entrega", f"{tempo_medio:.0f} min")
c2.metric("Pior Entrega Registrada", f"{tempo_max:.0f} min")
c3.metric("Taxa de Cancelamento", f"{tx_cancel:.1f}%", delta="-2.1% vs antes", delta_color="inverse")
c4.metric("Perda em Cancelamentos", f"R$ {perda_cancel:,.0f}".replace(",", "."))

# ─────────────────────────────────────────────
#  TEMPO MÉDIO POR BAIRRO
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">📍 Tempo Médio de Entrega por Bairro</div>', unsafe_allow_html=True)

tempo_bairro = (
    df_ok.groupby("Bairro")["Tempo de Entrega (min)"]
    .agg(["mean", "count"])
    .reset_index()
    .rename(columns={"mean": "Tempo Médio (min)", "count": "Pedidos"})
    .sort_values("Tempo Médio (min)", ascending=True)
)

fig_tempo = go.Figure()
fig_tempo.add_trace(go.Bar(
    y=tempo_bairro["Bairro"],
    x=tempo_bairro["Tempo Médio (min)"],
    orientation="h",
    marker=dict(
        color=tempo_bairro["Tempo Médio (min)"],
        colorscale=[[0, "#34d399"], [0.5, "#f59e0b"], [1, "#f87171"]],
        showscale=False,
    ),
    text=tempo_bairro["Tempo Médio (min)"].apply(lambda x: f"{x:.0f} min"),
    textposition="outside",
    customdata=tempo_bairro["Pedidos"],
    hovertemplate="%{y}<br>Tempo médio: %{x:.0f} min<br>Pedidos: %{customdata}<extra></extra>",
))
fig_tempo.update_layout(
    height=380,
    margin=dict(l=0, r=60, t=8, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=True, gridcolor="#1a1a2e", color="#50507a", title="minutos"),
    yaxis=dict(showgrid=False, color="#9090a8"),
    font=dict(family="DM Sans", color="#9090a8"),
)
st.plotly_chart(fig_tempo, use_container_width=True)

# Insight automático
bairro_lento = tempo_bairro.iloc[-1]
bairro_rapido = tempo_bairro.iloc[0]
st.markdown(f"""
<div class="insight-box red">
    <div class="insight-title">⚠️ Atenção: {bairro_lento['Bairro']}</div>
    <div class="insight-text">Tempo médio de <strong>{bairro_lento['Tempo Médio (min)']:.0f} minutos</strong> — acima da meta de 45 min. 
    Avalie se a rota ou volume de pedidos nessa região precisa de ajuste operacional.</div>
</div>
<div class="insight-box green">
    <div class="insight-title">✅ Melhor performance: {bairro_rapido['Bairro']}</div>
    <div class="insight-text">Tempo médio de apenas <strong>{bairro_rapido['Tempo Médio (min)']:.0f} minutos</strong>. 
    Entenda o que funciona bem aqui e replique nos outros bairros.</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  MAPA DE CALOR DE CANCELAMENTOS
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🗺️ Mapa de Calor — Cancelamentos por Região</div>', unsafe_allow_html=True)

cancel_bairro = (
    df.groupby("Bairro")
    .apply(lambda x: pd.Series({
        "Taxa Cancelamento (%)": x["is_cancelado"].mean() * 100,
        "Total Pedidos": len(x),
        "Cancelamentos": x["is_cancelado"].sum(),
        "lat": x["lat"].mean(),
        "lon": x["lon"].mean(),
    }))
    .reset_index()
)

fig_map = px.scatter_mapbox(
    cancel_bairro,
    lat="lat", lon="lon",
    size="Taxa Cancelamento (%)",
    color="Taxa Cancelamento (%)",
    color_continuous_scale=["#34d399", "#f59e0b", "#f87171"],
    size_max=30,
    hover_name="Bairro",
    hover_data={
        "Taxa Cancelamento (%)": ":.1f",
        "Total Pedidos": True,
        "Cancelamentos": True,
        "lat": False, "lon": False,
    },
    mapbox_style="carto-darkmatter",
    zoom=11,
    center={"lat": -23.5505, "lon": -46.6333},
)
fig_map.update_layout(
    height=420,
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    coloraxis_showscale=True,
    coloraxis_colorbar=dict(
        title="% Cancel.", tickfont=dict(color="#9090a8"), titlefont=dict(color="#9090a8")
    ),
)
st.plotly_chart(fig_map, use_container_width=True)

# ─────────────────────────────────────────────
#  CANCELAMENTOS POR DIA DA SEMANA
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">📅 Cancelamentos por Dia da Semana</div>', unsafe_allow_html=True)

order_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
label_days = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

cancel_dia = df.groupby("Dia Semana")["is_cancelado"].mean().reindex(order_days).reset_index()
cancel_dia.columns = ["Dia", "Taxa"]
cancel_dia["Dia Label"] = label_days
cancel_dia["Taxa %"] = (cancel_dia["Taxa"] * 100).round(1)

fig_dia = go.Figure(go.Bar(
    x=cancel_dia["Dia Label"],
    y=cancel_dia["Taxa %"],
    marker=dict(
        color=cancel_dia["Taxa %"],
        colorscale=[[0, "#34d399"], [0.5, "#f59e0b"], [1, "#f87171"]],
    ),
    text=cancel_dia["Taxa %"].apply(lambda x: f"{x:.1f}%"),
    textposition="outside",
    hovertemplate="%{x}: %{y:.1f}% de cancelamento<extra></extra>",
))
fig_dia.update_layout(
    height=280,
    margin=dict(l=0, r=0, t=8, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False, color="#9090a8"),
    yaxis=dict(showgrid=True, gridcolor="#1a1a2e", color="#50507a", ticksuffix="%"),
    font=dict(family="DM Sans", color="#9090a8"),
)

col_g, col_i = st.columns([2, 1])
with col_g:
    st.plotly_chart(fig_dia, use_container_width=True)
with col_i:
    pior_dia = cancel_dia.loc[cancel_dia["Taxa %"].idxmax()]
    melhor_dia = cancel_dia.loc[cancel_dia["Taxa %"].idxmin()]
    st.markdown(f"""
    <div style="padding-top:24px;">
        <div class="insight-box red">
            <div class="insight-title">⚠️ Dia crítico: {pior_dia['Dia Label']}</div>
            <div class="insight-text">{pior_dia['Taxa %']:.1f}% de cancelamentos. Reforce a operação e verifique tempo de preparo nesse dia.</div>
        </div>
        <div class="insight-box green">
            <div class="insight-title">🏆 Melhor dia: {melhor_dia['Dia Label']}</div>
            <div class="insight-text">Apenas {melhor_dia['Taxa %']:.1f}% de cancelamentos. Boa performance — mantenha o padrão.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
