"""
Módulo Fidelização — Análise de Churn e Retenção de Clientes
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import generate_mock_ifood_data, process_ifood_data

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Fidelização | DeliveryPro",
    page_icon="❤️",
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
.risk-card { border-radius: 10px; padding: 14px 18px; margin: 6px 0; display: flex; justify-content: space-between; align-items: center; }
.risk-high { background: rgba(248,113,113,0.08); border: 1px solid rgba(248,113,113,0.2); }
.risk-med  { background: rgba(245,158,11,0.07); border: 1px solid rgba(245,158,11,0.2); }
.risk-low  { background: rgba(52,211,153,0.07); border: 1px solid rgba(52,211,153,0.2); }
.client-name { font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700; color: #e8e8f0; }
.client-sub { font-size: 12px; color: #70708a; }
.badge { font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 4px; }
.badge-red    { background: rgba(248,113,113,0.2); color: #f87171; }
.badge-yellow { background: rgba(245,158,11,0.2);  color: #f59e0b; }
.badge-green  { background: rgba(52,211,153,0.2);  color: #34d399; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  DADOS
# ─────────────────────────────────────────────
if "df_main" not in st.session_state:
    df_raw = generate_mock_ifood_data(800)
    st.session_state["df_main"] = process_ifood_data(df_raw)

df = st.session_state["df_main"].copy()
df_ok = df[~df["is_cancelado"]].copy()

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:800;color:#e8e8f0;padding:8px 0;">
        ❤️ Fidelização
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.page_link("streamlit_app.py",         label="🏠  Visão Geral")
    st.page_link("pages/1_Operacao.py",      label="🚚  Operação")
    st.page_link("pages/2_Lucratividade.py", label="💰  Lucratividade")
    st.page_link("pages/3_Fidelizacao.py",   label="❤️  Fidelização")
    st.markdown("---")
    st.markdown("**🔍 Filtros**")
    dias_inativo = st.slider("Considerar inativo após (dias sem pedido)", 15, 90, 30)
    min_pedidos  = st.slider("Mínimo de pedidos históricos para análise", 1, 5, 2)

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:28px;">
    <div style="font-family:'Syne',sans-serif;font-size:30px;font-weight:800;color:#e8e8f0;line-height:1.2;">
        ❤️ Fidelização & Retenção
    </div>
    <div style="color:#60607a;font-size:15px;margin-top:6px;">
        Clientes que somem silenciosamente custam mais caro do que você imagina.
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  MÉTRICAS DE CLIENTE
# ─────────────────────────────────────────────
hoje = df_ok["Data do Pedido"].max()

cliente_stats = (
    df_ok.groupby("ID do Cliente")
    .agg(
        primeiro_pedido=("Data do Pedido", "min"),
        ultimo_pedido=("Data do Pedido", "max"),
        total_pedidos=("ID do Pedido", "count"),
        receita_total=("Valor Bruto", "sum"),
        ticket_medio=("Valor Bruto", "mean"),
    )
    .reset_index()
)

cliente_stats["dias_inativo"] = (hoje - cliente_stats["ultimo_pedido"]).dt.days
cliente_stats["lifetime_days"] = (cliente_stats["ultimo_pedido"] - cliente_stats["primeiro_pedido"]).dt.days

# Classificar risco de churn
def classificar_churn(row):
    if row["dias_inativo"] > dias_inativo * 2:
        return "🔴 Alto Risco"
    elif row["dias_inativo"] > dias_inativo:
        return "🟡 Atenção"
    else:
        return "🟢 Ativo"

cliente_stats["Status Churn"] = cliente_stats.apply(classificar_churn, axis=1)

# Filtrar por mínimo de pedidos
cliente_stats = cliente_stats[cliente_stats["total_pedidos"] >= min_pedidos]

n_total   = len(cliente_stats)
n_ativos  = len(cliente_stats[cliente_stats["Status Churn"] == "🟢 Ativo"])
n_atencao = len(cliente_stats[cliente_stats["Status Churn"] == "🟡 Atenção"])
n_risco   = len(cliente_stats[cliente_stats["Status Churn"] == "🔴 Alto Risco"])
receita_risco = cliente_stats[cliente_stats["Status Churn"] == "🔴 Alto Risco"]["receita_total"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Clientes Únicos Analisados", f"{n_total:,}".replace(",", "."))
c2.metric("Clientes Ativos", f"{n_ativos:,}".replace(",", "."), delta=f"{n_ativos/n_total*100:.0f}% do total")
c3.metric("Em Risco de Sumir", f"{n_risco:,}".replace(",", "."), delta=f"-R$ {receita_risco:,.0f}".replace(",", ".") + " em risco", delta_color="inverse")
c4.metric("Ticket Médio por Cliente", f"R$ {cliente_stats['ticket_medio'].mean():.2f}".replace(".", ","))

# ─────────────────────────────────────────────
#  FUNIL DE RETENÇÃO
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Funil de Saúde da Base de Clientes</div>', unsafe_allow_html=True)

col_funil, col_pizza = st.columns([3, 2])

with col_funil:
    funil_data = pd.DataFrame({
        "Status": ["🟢 Ativo (comprou recente)", "🟡 Em Atenção (30-60 dias)", "🔴 Alto Risco (60+ dias)"],
        "Qtd": [n_ativos, n_atencao, n_risco],
        "Cor": ["#34d399", "#f59e0b", "#f87171"],
    })

    fig_funil = go.Figure(go.Bar(
        x=funil_data["Qtd"],
        y=funil_data["Status"],
        orientation="h",
        marker=dict(color=funil_data["Cor"], opacity=0.85),
        text=funil_data["Qtd"].apply(lambda x: f"{x} clientes"),
        textposition="outside",
        hovertemplate="%{y}<br>%{x} clientes<extra></extra>",
    ))
    fig_funil.update_layout(
        height=220,
        margin=dict(l=0, r=80, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#1a1a28", color="#50507a"),
        yaxis=dict(showgrid=False, color="#9090a8"),
        font=dict(family="DM Sans", color="#9090a8"),
    )
    st.plotly_chart(fig_funil, use_container_width=True)

with col_pizza:
    fig_pie = go.Figure(go.Pie(
        values=[n_ativos, n_atencao, n_risco],
        labels=["Ativos", "Atenção", "Alto Risco"],
        marker=dict(colors=["#34d399", "#f59e0b", "#f87171"]),
        hole=0.55,
        textinfo="percent",
        textfont=dict(size=13, family="Syne"),
        hovertemplate="%{label}: %{value} clientes (%{percent})<extra></extra>",
    ))
    fig_pie.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        annotations=[dict(text=f"{n_total}<br><span style='font-size:10px'>clientes</span>",
                         x=0.5, y=0.5, font=dict(size=16, family="Syne", color="#e8e8f0"),
                         showarrow=False)],
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ─────────────────────────────────────────────
#  COHORT SIMPLIFICADO
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🔄 Retenção Mensal (Análise de Cohort)</div>', unsafe_allow_html=True)

df_ok_cohort = df_ok.copy()
df_ok_cohort["Mês Cohort"]  = df_ok_cohort.groupby("ID do Cliente")["Data do Pedido"].transform("min").dt.to_period("M")
df_ok_cohort["Mês Pedido"]  = df_ok_cohort["Data do Pedido"].dt.to_period("M")
df_ok_cohort["Período"]     = (df_ok_cohort["Mês Pedido"] - df_ok_cohort["Mês Cohort"]).apply(lambda x: x.n)

cohort_data = (
    df_ok_cohort.groupby(["Mês Cohort", "Período"])["ID do Cliente"]
    .nunique()
    .reset_index()
    .rename(columns={"ID do Cliente": "Clientes"})
)

cohort_pivot = cohort_data.pivot_table(index="Mês Cohort", columns="Período", values="Clientes")
cohort_base  = cohort_pivot[0]
cohort_pct   = cohort_pivot.div(cohort_base, axis=0) * 100

# Pegar últimos 6 meses cohort
cohort_pct = cohort_pct.tail(6)

# Heatmap
fig_cohort = go.Figure(go.Heatmap(
    z=cohort_pct.values,
    x=[f"Mês {i}" for i in cohort_pct.columns],
    y=[str(p) for p in cohort_pct.index],
    colorscale=[[0, "#1a0a0a"], [0.3, "#7c2d12"], [0.6, "#f59e0b"], [1, "#34d399"]],
    text=cohort_pct.applymap(lambda x: f"{x:.0f}%" if pd.notna(x) else "").values,
    texttemplate="%{text}",
    textfont=dict(size=11, family="DM Sans"),
    hovertemplate="Cohort: %{y}<br>%{x}<br>Retenção: %{z:.1f}%<extra></extra>",
    showscale=True,
    colorbar=dict(
        title="Retenção %",
        tickfont=dict(color="#9090a8"),
        titlefont=dict(color="#9090a8"),
    ),
))
fig_cohort.update_layout(
    height=280,
    margin=dict(l=0, r=0, t=8, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(color="#9090a8"),
    yaxis=dict(color="#9090a8"),
    font=dict(family="DM Sans", color="#9090a8"),
)
st.plotly_chart(fig_cohort, use_container_width=True)
st.markdown("""
<div style="font-size:12px;color:#40405a;margin-top:-8px;margin-bottom:8px;">
    Cada linha = grupo de clientes pelo mês da 1ª compra. Cada coluna = % que voltou naquele mês depois. 
    Verde = boa retenção.
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  LISTA DE CLIENTES PARA RECUPERAR
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🎯 Clientes Para Recuperar Agora</div>', unsafe_allow_html=True)

clientes_risco = (
    cliente_stats[cliente_stats["Status Churn"] != "🟢 Ativo"]
    .sort_values("receita_total", ascending=False)
    .head(20)
    .copy()
)

st.markdown(f"""
<div style="background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.15);border-radius:10px;padding:16px 20px;margin-bottom:16px;">
    <div style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:#f59e0b;margin-bottom:4px;">
        💡 Ação Recomendada
    </div>
    <div style="font-size:13px;color:#9090a8;line-height:1.6;">
        Esses <strong style="color:#e8e8f0;">{len(clientes_risco)} clientes</strong> somem há mais de {dias_inativo} dias, mas têm histórico de compra.
        Um cupom de R$ 10 ou uma mensagem personalizada pode trazer de volta até 30% deles.
        Priorize os de maior receita histórica (topo da lista).
    </div>
</div>
""", unsafe_allow_html=True)

col_a, col_b = st.columns(2)

for i, (_, row) in enumerate(clientes_risco.iterrows()):
    risco_class = "risk-high" if "Alto" in row["Status Churn"] else "risk-med"
    badge_class = "badge-red" if "Alto" in row["Status Churn"] else "badge-yellow"
    badge_text  = f"{'Inativo há ' + str(row['dias_inativo']) + ' dias'}"
    col = col_a if i % 2 == 0 else col_b

    with col:
        st.markdown(f"""
        <div class="risk-card {risco_class}">
            <div>
                <div class="client-name">{row['ID do Cliente']}</div>
                <div class="client-sub">
                    {row['total_pedidos']} pedidos · 
                    R$ {row['receita_total']:,.0f} gerado
                </div>
            </div>
            <div>
                <span class="badge {badge_class}">{badge_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  EVOLUÇÃO DE NOVOS CLIENTES
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">📈 Novos Clientes por Mês</div>', unsafe_allow_html=True)

primeiros = (
    df_ok.groupby("ID do Cliente")["Data do Pedido"]
    .min()
    .reset_index()
    .rename(columns={"Data do Pedido": "Primeiro Pedido"})
)
primeiros["Mês"] = primeiros["Primeiro Pedido"].dt.to_period("M").dt.start_time
novos_mes = primeiros.groupby("Mês").size().reset_index(name="Novos Clientes")
novos_mes = novos_mes.tail(6)

fig_novos = go.Figure()
fig_novos.add_trace(go.Bar(
    x=novos_mes["Mês"],
    y=novos_mes["Novos Clientes"],
    marker=dict(color="#a78bfa", opacity=0.8),
    text=novos_mes["Novos Clientes"],
    textposition="outside",
    hovertemplate="%{x|%b/%Y}: %{y} novos clientes<extra></extra>",
))
fig_novos.update_layout(
    height=250,
    margin=dict(l=0, r=0, t=8, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False, color="#9090a8", tickformat="%b/%y"),
    yaxis=dict(showgrid=True, gridcolor="#1a1a28", color="#50507a"),
    font=dict(family="DM Sans", color="#9090a8"),
)
st.plotly_chart(fig_novos, use_container_width=True)
