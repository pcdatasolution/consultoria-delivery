"""
DeliveryPro — Página Inicial / Landing
Choque de realidade + upload + navegação
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from utils import (
    carregar_pedidos_sheets, generate_mock_ifood_data, gerar_plano_automatico, process_ifood_data, get_kpis,
    calcular_choque, detectar_modo, inject_css, render_sidebar, carregar_dados_cliente
)

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="DeliveryPro | Hub de Soluções",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
render_sidebar(active="home")
acesso = detectar_modo()

# ── Carregar / inicializar dados ──────────────────────────────────────────────
if "df_main" not in st.session_state:
    sheets_id = acesso.get("sheets_id")
    df_sheets = carregar_pedidos_sheets(sheets_id) if sheets_id else None

    if df_sheets is not None:
        st.session_state["df_main"] = df_sheets
        st.session_state["is_mock"] = False
        dados_cliente = carregar_dados_cliente(sheets_id)
        st.session_state["config"]   = dados_cliente.get("config", {})
        st.session_state["cardapio"] = dados_cliente.get("cardapio", {})
    else:
        st.session_state["df_main"] = process_ifood_data(generate_mock_ifood_data(800))
        st.session_state["is_mock"] = True
        st.session_state["config"] = {}

config   = st.session_state.get("config", {})
cardapio = st.session_state.get("cardapio", {})
dias_churn = config.get("churn", 30)

df     = st.session_state["df_main"]
kpis   = get_kpis(df)
choque = calcular_choque(df, dias_churn=dias_churn)
plano  = gerar_plano_automatico(df, config=config, cardapio=cardapio)




# ─────────────────────────────────────────────────────────────────────────────
#  CHOQUE DE REALIDADE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Syne',Inter;font-size:28px;font-weight:700;
  color:#2f5f98;margin:32px 0 6px;">
  ⚡ Diagnóstico Rápido
</div>
<div style="font-size:13px;color:#2f5f98;margin-bottom:16px;">
  Baseado nos seus dados — estimativas calculadas com metodologia financeira.
</div>
""", unsafe_allow_html=True)

perda_low_fmt  = f"R$ {plano['impacto_mensal_low']:,.0f}".replace(",", ".")
perda_high_fmt = f"R$ {plano['impacto_mensal_high']:,.0f}".replace(",", ".")
n_itens   = choque["n_itens_problema"]
pct_churn = choque["pct_churn"]

st.markdown(f"""
<div class="choque-grid">
  <div class="choque-item">
    <div class="choque-icon">💸</div>
    <div class="choque-value">{perda_low_fmt} – {perda_high_fmt}</div>
    <div class="choque-label">por mês em potencial não realizado<br>
      <span style="color:#000000;font-size:11px;">margem perdida + clientes inativos + cancelamentos</span>
    </div>
  </div>
  <div class="choque-item">
    <div class="choque-icon">⚠️</div>
    <div class="choque-value">{n_itens} {'item' if n_itens == 1 else 'itens'}</div>
    <div class="choque-label">com alta venda e baixa margem<br>
      <span style="color:#000000;font-size:11px;">você trabalha mais para ganhar menos</span>
    </div>
  </div>
  <div class="choque-item">
    <div class="choque-icon">📉</div>
    <div class="choque-value">{pct_churn:.0f}%</div>
    <div class="choque-label">dos clientes não voltaram a pedir<br>
      <span style="color:#000000;font-size:11px;">{choque['n_inativos']} clientes inativos há mais de 30 dias</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="font-size:11px;color:#30303e;margin-top:-4px;margin-bottom:8px;font-style:italic;">
  * Estimativas baseadas nos seus dados com metodologia de proxy financeiro. Valores reais podem variar.
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  OVERVIEW KPIs
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Visão Geral do Período</div>', unsafe_allow_html=True)

# ── Período analisado ──
df_ok_periodo = df[~df["is_cancelado"]]
data_inicial  = df_ok_periodo["Data do Pedido"].min()
data_final    = df_ok_periodo["Data do Pedido"].max()
dias_periodo  = (data_final - data_inicial).days + 1

data_corte    = pd.Timestamp.now() - pd.Timedelta(days=dias_churn)
clientes_em_risco = (
    df_ok_periodo.groupby("ID do Cliente")["Data do Pedido"].max()
    .lt(data_corte)
    .sum()
)

p1, p2, p3, p4 = st.columns(4)
p1.metric("Data Inicial",  data_inicial.strftime("%d/%m/%Y"))
p2.metric("Data Final",    data_final.strftime("%d/%m/%Y"))
p3.metric("Período",       f"{dias_periodo} dias")
p4.metric("Clientes em Risco", int(clientes_em_risco),
    delta=f"sem comprar há +{dias_churn} dias", delta_color="inverse")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── KPIs principais ──
c1, c2, c3, c4 = st.columns(4)
c1.metric("Faturamento Bruto",
    f"R$ {kpis['faturamento']:,.0f}".replace(",","."))
c2.metric("Receita Líquida (após taxas iFood)",
    f"R$ {kpis['receita_liquida']:,.0f}".replace(",","."))
c3.metric("Ticket Médio",
    f"R$ {kpis['ticket_medio']:.2f}".replace(".",","))
c4.metric("Taxa de Cancelamento",
    f"{kpis['taxa_cancelamento']:.1f}%",
    delta=f"Perda de R$ {kpis['perda_cancelamentos']:,.0f}".replace(",","."),
    delta_color="inverse")

# ─────────────────────────────────────────────────────────────────────────────
#  GRÁFICO — Faturamento semanal
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📅 Faturamento nas Últimas Semanas</div>', unsafe_allow_html=True)

df_ok = df[~df["is_cancelado"]].copy()
df_ok["Semana"] = df_ok["Data do Pedido"].dt.to_period("W").dt.start_time
fat_semanal = df_ok.groupby("Semana")["Valor Bruto"].sum().reset_index().tail(12)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=fat_semanal["Semana"],
    y=fat_semanal["Valor Bruto"],
    fill="tozeroy",
    mode="lines+markers",
    line=dict(color="#a78bfa", width=2.5),
    fillcolor="rgba(139,92,246,0.08)",
    marker=dict(color="#a78bfa", size=6),
    hovertemplate="Semana: %{x|%d/%m}<br>Faturamento: R$ %{y:,.2f}<extra></extra>",
))
fig.update_layout(
    height=230,
    margin=dict(l=0, r=0, t=8, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False, color="#50507a", tickformat="%d/%m"),
    yaxis=dict(showgrid=True, gridcolor="#1a1a2e", color="#50507a",
               tickprefix="R$ ", tickformat=",.0f"),
    font=dict(family="DM Sans", color="#9090a8"),
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
#  BUBBLE — Pedidos por hora × dia da semana
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🕐 Horarios de pico durante a semana</div>', unsafe_allow_html=True)

dias_ordem = ["Domingo", "Sábado", "Sexta", "Quinta", "Quarta", "Terça", "Segunda"]
dias_map   = {0:"Segunda",1:"Terça",2:"Quarta",3:"Quinta",4:"Sexta",5:"Sábado",6:"Domingo"}

df_heat = df_ok.copy()
df_heat["DiaSemana"] = df_heat["Data do Pedido"].dt.dayofweek.map(dias_map)

if df_heat["Hora"].dtype == object:
    df_heat["Hora"] = pd.to_datetime(df_heat["Hora"], format="mixed", errors="coerce").dt.hour
df_heat = df_heat.dropna(subset=["Hora"])
df_heat["Hora"] = df_heat["Hora"].astype(int)

bubble = (
    df_heat.groupby(["DiaSemana", "Hora"])
    .size()
    .reset_index(name="Pedidos")
)

fig_bubble = go.Figure(go.Scatter(
    x=bubble["Hora"],
    y=bubble["DiaSemana"],
    mode="markers",
    marker=dict(
        size=bubble["Pedidos"],
        sizemode="area",
        sizeref=2. * bubble["Pedidos"].max() / (40**2),
        sizemin=4,
        color=bubble["Pedidos"],
        colorscale="Purples",
        showscale=False,
    ),
    hovertemplate="%{y} — %{x}h<br>Pedidos: %{marker.size:.0f}<extra></extra>",
    text=bubble["Pedidos"],
))

fig_bubble.update_layout(
    height=280,
    margin=dict(l=0, r=0, t=8, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#9090a8"),
    xaxis=dict(
        showgrid=False, color="#50507a",
        tickmode="array",
        tickvals=sorted(bubble["Hora"].unique()),
        ticktext=[f"{h}h" for h in sorted(bubble["Hora"].unique())],
    ),
    yaxis=dict(
        showgrid=False, color="#50507a",
        categoryorder="array", categoryarray=dias_ordem,
    ),
    hovermode="closest",
)
st.plotly_chart(fig_bubble, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
#  TOP 5 ITENS + TOP 3 BAIRROS
# ─────────────────────────────────────────────────────────────────────────────
col_itens, col_bairros = st.columns([3, 2])

with col_itens:
    st.markdown('<div class="section-header">🏆 Top 5 Itens Mais Vendidos</div>', unsafe_allow_html=True)

    top5 = (
        df_ok.groupby("Nome do Item")["Valor Bruto"]
        .agg(Pedidos="count", Faturamento="sum")
        .sort_values("Pedidos", ascending=False)
        .head(5)
        .reset_index()
    )
    top5["Faturamento"] = top5["Faturamento"].apply(
        lambda x: f"R$ {x:,.0f}".replace(",", ".")
    )

    fig_top5 = go.Figure(go.Bar(
        x=top5["Pedidos"],
        y=top5["Nome do Item"],
        orientation="h",
        marker_color="#a78bfa",
        text=top5["Pedidos"],
        textposition="outside",
        hovertemplate="%{y}<br>Pedidos: %{x}<extra></extra>",
    ))
    fig_top5.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#9090a8"),
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False, autorange="reversed"),
    )
    st.plotly_chart(fig_top5, use_container_width=True)

with col_bairros:
    st.markdown('<div class="section-header">📍 Top 3 Bairros</div>', unsafe_allow_html=True)

    top3_bairros = (
        df_ok.groupby("Bairro")
        .size()
        .reset_index(name="Pedidos")
        .sort_values("Pedidos", ascending=False)
        .head(3)
        .reset_index(drop=True)
    )
    top3_bairros.index += 1
    top3_bairros.columns = ["Bairro", "Pedidos"]

    st.dataframe(
        top3_bairros,
        use_container_width=True,
        hide_index=False,
    )

# ─────────────────────────────────────────────────────────────────────────────
#  OS 3 PILARES (navegação para demos)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🔍 Explore os Módulos</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background:#0f0f1e;border:1px solid #1c1c2e;border-radius:12px;padding:22px 20px;height:100%;">
      <div style="font-size:28px;margin-bottom:8px;">🚚</div>
      <div style="font-family:'Syne',Inter;font-size:16px;font-weight:700;
        color:#FFFFFF;margin-bottom:8px;">Operação</div>
      <p style="font-size:13px;color:#FFFFFF;line-height:1.6;margin-bottom:14px;">
        Veja onde sua operação perde tempo e aumenta cancelamentos.
        Diagnóstico completo por bairro e horário.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_Operacao.py", label="→ Ver Operação")

with col2:
    st.markdown("""
    <div style="background:#0f0f1e;border:1px solid #1c1c2e;border-radius:12px;padding:22px 20px;height:100%;">
      <div style="font-size:28px;margin-bottom:8px;">💰</div>
      <div style="font-family:'Syne',Inter;font-size:16px;font-weight:700;
        color:#FFFFFF;margin-bottom:8px;">Lucratividade</div>
      <p style="font-size:13px;color:#FFFFFF;line-height:1.6;margin-bottom:14px;">
        Descubra quais pratos constroem — ou destroem — sua margem.
        Matriz completa + plano de ação por item.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Lucratividade.py", label="→ Ver Lucratividade")

with col3:
    st.markdown("""
    <div style="background:#0f0f1e;border:1px solid #1c1c2e;border-radius:12px;padding:22px 20px;height:100%;">
      <div style="font-size:28px;margin-bottom:8px;">❤️</div>
      <div style="font-family:'Syne',Inter;font-size:16px;font-weight:700;
        color:#FFFFFF;margin-bottom:8px;">Fidelização</div>
      <p style="font-size:13px;color:#FFFFFF;line-height:1.6;margin-bottom:14px;">
        Entenda por que seus clientes somem e como trazê-los de volta.
        Cohort completo + lista de clientes para recuperar.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_Fidelizacao.py", label="→ Ver Fidelização")

# ─────────────────────────────────────────────────────────────────────────────
#  CTA — bloquear ou mostrar status premium
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)



# rodapé
st.markdown("""
<div style="text-align:center;padding:32px 0 8px;color:#252535;font-size:12px;">
  DeliveryPro Hub · Consultoria de Dados para Restaurantes
</div>
""", unsafe_allow_html=True)
