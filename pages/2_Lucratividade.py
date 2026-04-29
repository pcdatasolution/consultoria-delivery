"""
Módulo Lucratividade — Engenharia de Cardápio e Margens
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import generate_mock_ifood_data, process_ifood_data, ITENS_CARDAPIO

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Lucratividade | DeliveryPro",
    page_icon="💰",
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
.quadrant-label { font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700; padding: 6px 12px; border-radius: 6px; display: inline-block; margin-bottom: 6px; }
.card-estrela { background: rgba(52,211,153,0.1); border: 1px solid rgba(52,211,153,0.3); border-radius: 10px; padding: 16px; margin: 8px 0; }
.card-problema { background: rgba(248,113,113,0.08); border: 1px solid rgba(248,113,113,0.25); border-radius: 10px; padding: 16px; margin: 8px 0; }
.card-cavalo { background: rgba(167,139,250,0.08); border: 1px solid rgba(167,139,250,0.25); border-radius: 10px; padding: 16px; margin: 8px 0; }
.card-item-title { font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 700; color: #e8e8f0; }
.card-item-sub { font-size: 12px; color: #70708a; margin-top: 3px; }
.vazamento-box { background: linear-gradient(135deg, rgba(248,113,113,0.08), rgba(245,158,11,0.06)); border: 1px solid rgba(248,113,113,0.2); border-radius: 12px; padding: 24px; margin: 16px 0; }
.vazamento-title { font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 800; color: #f87171; margin-bottom: 6px; }
.vazamento-value { font-family: 'Syne', sans-serif; font-size: 36px; font-weight: 800; color: #f59e0b; }
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
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:800;color:#e8e8f0;padding:8px 0;">
        💰 Lucratividade
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

    # Taxa de custo padrão (editável)
    custo_pct = st.slider(
        "Custo médio do produto (% do preço)",
        min_value=20, max_value=60, value=38,
        help="Percentual de custo dos ingredientes sobre o preço de venda"
    )

if len(date_range) == 2:
    df = df[(df["Data do Pedido"].dt.date >= date_range[0]) & (df["Data do Pedido"].dt.date <= date_range[1])]

df_ok = df[~df["is_cancelado"]].copy()

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:28px;">
    <div style="font-family:'Syne',sans-serif;font-size:30px;font-weight:800;color:#e8e8f0;line-height:1.2;">
        💰 Engenharia de Cardápio
    </div>
    <div style="color:#60607a;font-size:15px;margin-top:6px;">
        Saiba exatamente quais pratos constroem — ou destroem — sua margem.
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  CALCULAR MÉTRICAS POR ITEM
# ─────────────────────────────────────────────

item_stats = (
    df_ok.groupby("Nome do Item")
    .agg(
        Vendas=("Nome do Item", "count"),
        Receita=("Valor dos Itens", "sum"),
        Receita_Media=("Valor dos Itens", "mean"),
        Comissao=("Comissão iFood", "sum"),
    )
    .reset_index()
)

# Enriquecer com custo estimado
def get_margem(item_name, receita_media, custo_percentual):
    if item_name in ITENS_CARDAPIO:
        custo = ITENS_CARDAPIO[item_name]["custo"]
        preco = ITENS_CARDAPIO[item_name]["preco"]
        margem_bruta = (preco - custo) / preco * 100
    else:
        margem_bruta = 100 - custo_percentual
    return margem_bruta

item_stats["Margem Bruta (%)"] = item_stats.apply(
    lambda r: get_margem(r["Nome do Item"], r["Receita_Media"], custo_pct), axis=1
)
item_stats["Receita Líquida"] = item_stats["Receita"] - item_stats["Comissao"]
item_stats["Margem Líquida (%)"] = (item_stats["Receita Líquida"] / item_stats["Receita"] * 100).round(1)

# Percentis para classificação
mediana_vendas = item_stats["Vendas"].median()
mediana_margem = item_stats["Margem Bruta (%)"].median()

def classificar(row):
    alto_volume = row["Vendas"] >= mediana_vendas
    alta_margem = row["Margem Bruta (%)"] >= mediana_margem
    if alto_volume and alta_margem:
        return "⭐ Estrela"
    elif not alto_volume and alta_margem:
        return "💎 Potencial"
    elif alto_volume and not alta_margem:
        return "🐴 Cavalo de Batalha"
    else:
        return "❌ Problema"

item_stats["Categoria"] = item_stats.apply(classificar, axis=1)

# ─────────────────────────────────────────────
#  KPIs
# ─────────────────────────────────────────────
receita_total  = item_stats["Receita"].sum()
receita_liq    = item_stats["Receita Líquida"].sum()
margem_media   = (receita_liq / receita_total * 100) if receita_total else 0
comissao_total = item_stats["Comissao"].sum()

# "Vazamento": receita perdida em itens classificados como Problema (baixa margem, baixo volume)
items_problema = item_stats[item_stats["Categoria"] == "❌ Problema"]
vazamento = items_problema["Receita"].sum() * (1 - items_problema["Margem Bruta (%)"].mean() / 100)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Receita Total no Período", f"R$ {receita_total:,.0f}".replace(",", "."))
c2.metric("Receita Líquida (após iFood)", f"R$ {receita_liq:,.0f}".replace(",", "."))
c3.metric("Margem Líquida Média", f"{margem_media:.1f}%")
c4.metric("Comissão Total Paga ao iFood", f"R$ {comissao_total:,.0f}".replace(",", "."))

# ─────────────────────────────────────────────
#  MATRIZ DE ENGENHARIA DE CARDÁPIO
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🎯 Matriz de Cardápio — Volume vs. Margem</div>', unsafe_allow_html=True)

COLOR_MAP = {
    "⭐ Estrela":            "#34d399",
    "💎 Potencial":          "#a78bfa",
    "🐴 Cavalo de Batalha":  "#f59e0b",
    "❌ Problema":           "#f87171",
}

fig_matrix = go.Figure()

for cat, color in COLOR_MAP.items():
    subset = item_stats[item_stats["Categoria"] == cat]
    if len(subset) == 0:
        continue
    fig_matrix.add_trace(go.Scatter(
        x=subset["Vendas"],
        y=subset["Margem Bruta (%)"],
        mode="markers+text",
        name=cat,
        marker=dict(
            size=subset["Receita"] / subset["Receita"].max() * 42 + 14,
            color=color,
            opacity=0.85,
            line=dict(width=1, color="rgba(0,0,0,0.3)"),
        ),
        text=subset["Nome do Item"].str.replace("Pizza ", "🍕 ").str.replace("Hamburger ", "🍔 "),
        textposition="top center",
        textfont=dict(size=10, color="#c0c0d8"),
        customdata=subset[["Receita", "Receita Líquida", "Margem Líquida (%)"]].values,
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Vendas: %{x}<br>"
            "Margem Bruta: %{y:.1f}%<br>"
            "Receita: R$ %{customdata[0]:,.0f}<br>"
            "Rec. Líquida: R$ %{customdata[1]:,.0f}<br>"
            "Margem Líquida: %{customdata[2]:.1f}%<extra></extra>"
        ),
    ))

# Linhas de referência (medianas)
fig_matrix.add_vline(x=mediana_vendas, line_dash="dot", line_color="#2a2a4a", line_width=1.5)
fig_matrix.add_hline(y=mediana_margem, line_dash="dot", line_color="#2a2a4a", line_width=1.5)

# Anotações dos quadrantes
fig_matrix.add_annotation(x=item_stats["Vendas"].max()*0.9, y=item_stats["Margem Bruta (%)"].max()*0.97,
    text="⭐ ESTRELAS", font=dict(color="#34d399", size=11, family="Syne"), showarrow=False)
fig_matrix.add_annotation(x=item_stats["Vendas"].max()*0.07, y=item_stats["Margem Bruta (%)"].max()*0.97,
    text="💎 POTENCIAL", font=dict(color="#a78bfa", size=11, family="Syne"), showarrow=False)
fig_matrix.add_annotation(x=item_stats["Vendas"].max()*0.9, y=item_stats["Margem Bruta (%)"].min()*1.1,
    text="🐴 CAVALOS", font=dict(color="#f59e0b", size=11, family="Syne"), showarrow=False)
fig_matrix.add_annotation(x=item_stats["Vendas"].max()*0.07, y=item_stats["Margem Bruta (%)"].min()*1.1,
    text="❌ PROBLEMA", font=dict(color="#f87171", size=11, family="Syne"), showarrow=False)

fig_matrix.update_layout(
    height=480,
    margin=dict(l=0, r=0, t=8, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0d0d18",
    xaxis=dict(title="Volume de Vendas (pedidos)", showgrid=True, gridcolor="#1a1a28", color="#70708a"),
    yaxis=dict(title="Margem Bruta (%)", showgrid=True, gridcolor="#1a1a28", color="#70708a"),
    legend=dict(
        bgcolor="rgba(17,17,24,0.9)", bordercolor="#2a2a4a", borderwidth=1,
        font=dict(color="#9090a8", size=11)
    ),
    font=dict(family="DM Sans"),
    hovermode="closest",
)
st.plotly_chart(fig_matrix, use_container_width=True)

st.markdown("""
<div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:-8px;margin-bottom:20px;">
    <span style="font-size:12px;color:#60607a;">⭐ <span style="color:#34d399;">Estrelas</span>: alto volume + alta margem — promova mais</span>
    <span style="font-size:12px;color:#60607a;">💎 <span style="color:#a78bfa;">Potencial</span>: boa margem, mas pouco pedido — divulgue</span>
    <span style="font-size:12px;color:#60607a;">🐴 <span style="color:#f59e0b;">Cavalos</span>: muito vendido, margem baixa — revise preço</span>
    <span style="font-size:12px;color:#60607a;">❌ <span style="color:#f87171;">Problema</span>: baixo volume e margem ruim — considere remover</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  VAZAMENTO DE LUCRO
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🚨 Vazamento de Lucro</div>', unsafe_allow_html=True)

col_v, col_r = st.columns([1, 2])

with col_v:
    st.markdown(f"""
    <div class="vazamento-box">
        <div class="vazamento-title">💸 Dinheiro Perdido</div>
        <div style="font-size:13px;color:#80807a;margin-bottom:12px;">
            Estimativa de receita que poderia ser margem — mas foi para custo alto
        </div>
        <div class="vazamento-value">R$ {vazamento:,.0f}".replace(",",".")</div>
        <div style="font-size:12px;color:#60607a;margin-top:8px;">
            Nos itens de baixa performance no período
        </div>
        <div style="margin-top:16px;padding-top:16px;border-top:1px solid rgba(248,113,113,0.15);">
            <div style="font-size:13px;color:#9090a8;line-height:1.6;">
                Se você ajustar o preço ou custo dos itens <strong style="color:#f87171;">Problema</strong>,
                essa quantia pode virar lucro real no seu bolso.
            </div>
        </div>
    </div>
    """.replace('".replace(",",".")', ''), unsafe_allow_html=True)

    # Corrigindo o display
    st.markdown(f"""
    <div style="background:rgba(248,113,113,0.06);border:1px solid rgba(248,113,113,0.2);border-radius:10px;padding:20px;margin-top:8px;">
        <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:#f59e0b;">
            R$ {vazamento:,.0f}
        </div>
        <div style="font-size:12px;color:#60607a;margin-top:4px;">estimativa de lucro não realizado</div>
    </div>
    """, unsafe_allow_html=True)

with col_r:
    # Barras de receita por item, coloridas por categoria
    item_sorted = item_stats.sort_values("Receita", ascending=True).tail(10)
    colors = [COLOR_MAP.get(c, "#9090a8") for c in item_sorted["Categoria"]]

    fig_receita = go.Figure(go.Bar(
        y=item_sorted["Nome do Item"],
        x=item_sorted["Receita"],
        orientation="h",
        marker=dict(color=colors, opacity=0.85),
        text=item_sorted["Categoria"],
        textposition="outside",
        textfont=dict(size=10),
        customdata=item_sorted[["Margem Bruta (%)", "Receita Líquida"]].values,
        hovertemplate="%{y}<br>Receita: R$ %{x:,.0f}<br>Margem: %{customdata[0]:.1f}%<br>Líquida: R$ %{customdata[1]:,.0f}<extra></extra>",
    ))
    fig_receita.update_layout(
        height=360,
        margin=dict(l=0, r=100, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#1a1a28", color="#50507a", tickprefix="R$ "),
        yaxis=dict(showgrid=False, color="#9090a8"),
        font=dict(family="DM Sans", color="#9090a8"),
        title=dict(text="Top 10 Itens por Receita", font=dict(family="Syne", color="#e8e8f0", size=14), x=0),
    )
    st.plotly_chart(fig_receita, use_container_width=True)

# ─────────────────────────────────────────────
#  TABELA DE AÇÃO
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Plano de Ação por Item</div>', unsafe_allow_html=True)

def recomendar(row):
    if row["Categoria"] == "⭐ Estrela":
        return "✅ Destaque no cardápio e stories"
    elif row["Categoria"] == "💎 Potencial":
        return "📣 Promova com foto e descrição nova"
    elif row["Categoria"] == "🐴 Cavalo de Batalha":
        return "💡 Revise preço ou reduza custo de insumo"
    else:
        return "🗑️ Avalie retirar ou reformular"

item_stats["Recomendação"] = item_stats.apply(recomendar, axis=1)

tabela = item_stats[[
    "Nome do Item", "Categoria", "Vendas",
    "Margem Bruta (%)", "Receita", "Recomendação"
]].sort_values("Receita", ascending=False).copy()

tabela["Receita"] = tabela["Receita"].apply(lambda x: f"R$ {x:,.0f}".replace(",", "."))
tabela["Margem Bruta (%)"] = tabela["Margem Bruta (%)"].apply(lambda x: f"{x:.0f}%")
tabela.columns = ["Item", "Quadrante", "Vendas", "Margem Bruta", "Receita Total", "Ação Recomendada"]

st.dataframe(
    tabela,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Item":            st.column_config.TextColumn(width="medium"),
        "Quadrante":       st.column_config.TextColumn(width="medium"),
        "Vendas":          st.column_config.NumberColumn(width="small"),
        "Margem Bruta":    st.column_config.TextColumn(width="small"),
        "Receita Total":   st.column_config.TextColumn(width="medium"),
        "Ação Recomendada":st.column_config.TextColumn(width="large"),
    }
)
