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
    generate_mock_ifood_data, process_ifood_data, get_kpis,
    calcular_choque, detectar_modo, inject_css, render_sidebar,
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
    st.session_state["df_main"]  = process_ifood_data(generate_mock_ifood_data(800))
    st.session_state["is_mock"]  = True

df     = st.session_state["df_main"]
kpis   = get_kpis(df)
choque = calcular_choque(df)

# ─────────────────────────────────────────────────────────────────────────────
#  HERO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
    background: linear-gradient(135deg, #0c0c1a 0%, #160a28 55%, #0a160c 100%);
    border: 1px solid #221840;
    border-radius: 16px;
    padding: 52px 48px 44px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
">
  <!-- glow decorativo -->
  <div style="position:absolute;top:-60%;left:-5%;width:45%;height:200%;
    background:radial-gradient(ellipse,rgba(139,92,246,.07) 0%,transparent 70%);
    pointer-events:none;"></div>
  <div style="position:absolute;bottom:-40%;right:0;width:40%;height:180%;
    background:radial-gradient(ellipse,rgba(34,197,94,.05) 0%,transparent 70%);
    pointer-events:none;"></div>

  <div style="display:inline-block;background:rgba(139,92,246,.12);
    border:1px solid rgba(139,92,246,.35);color:#a78bfa;
    font-size:11px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;
    padding:5px 13px;border-radius:20px;margin-bottom:20px;">
    📊 Consultoria de Dados para Delivery
  </div>

  <h1 style="font-family:'Syne',Inter;font-size:clamp(28px,3.8vw,50px);
    font-weight:800;line-height:1.15;color:#f0f0ff;margin-bottom:18px;">
    Descubra onde seu delivery<br>
    está <span style="background:linear-gradient(135deg,#a78bfa,#34d399);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
      background-clip:text;">perdendo dinheiro</span> — em segundos.
  </h1>

  <p style="font-size:17px;font-weight:300;color:#8080a0;line-height:1.7;
    max-width:560px;margin-bottom:0;">
    Suba o relatório do iFood e receba um diagnóstico financeiro
    com os problemas rankeados por impacto — e o que fazer em cada um.
  </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Syne',Inter;font-size:17px;font-weight:700;
  color:#e2e2f0;margin-bottom:4px;">
  📂 Suba seu relatório
</div>
<div style="font-size:13px;color:#50507a;margin-bottom:12px;">
  Exporte pelo Portal do Parceiro iFood → Relatórios → Pedidos → CSV
</div>
""", unsafe_allow_html=True)

col_up, col_btn = st.columns([3, 1])

with col_up:
    arquivo = st.file_uploader(
        label="Arraste o CSV aqui ou clique para selecionar",
        type=["csv"],
        label_visibility="collapsed",
    )

with col_btn:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("🎲 Testar com dados simulados", use_container_width=True):
        st.session_state["df_main"] = process_ifood_data(generate_mock_ifood_data(800))
        st.session_state["is_mock"] = True
        st.rerun()

# Processar upload real
if arquivo:
    try:
        df_up = pd.read_csv(arquivo, sep=None, engine="python")
        df_up = process_ifood_data(df_up)
        st.session_state["df_main"] = df_up
        st.session_state["is_mock"] = False
        df     = df_up
        kpis   = get_kpis(df)
        choque = calcular_choque(df)
        st.success(f"✅ {len(df):,} pedidos carregados. Diagnóstico atualizado abaixo.")
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
else:
    if st.session_state.get("is_mock"):
        st.caption("👆 Exibindo **dados de demonstração** — 800 pedidos simulados no formato iFood.")

# ─────────────────────────────────────────────────────────────────────────────
#  CHOQUE DE REALIDADE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Syne',Inter;font-size:17px;font-weight:700;
  color:#e2e2f0;margin:32px 0 6px;">
  ⚡ Diagnóstico Rápido
</div>
<div style="font-size:13px;color:#50507a;margin-bottom:16px;">
  Baseado nos seus dados — estimativas calculadas com metodologia financeira.
</div>
""", unsafe_allow_html=True)

perda_low_fmt  = f"R$ {choque['perda_low']:,.0f}".replace(",", ".")
perda_high_fmt = f"R$ {choque['perda_high']:,.0f}".replace(",", ".")
n_itens = choque["n_itens_problema"]
pct_churn = choque["pct_churn"]

st.markdown(f"""
<div class="choque-grid">
  <div class="choque-item">
    <div class="choque-icon">💸</div>
    <div class="choque-value">{perda_low_fmt} – {perda_high_fmt}</div>
    <div class="choque-label">por mês em potencial não realizado<br>
      <span style="color:#404058;font-size:11px;">margem perdida + clientes inativos + cancelamentos</span>
    </div>
  </div>
  <div class="choque-item">
    <div class="choque-icon">⚠️</div>
    <div class="choque-value">{n_itens} {'item' if n_itens == 1 else 'itens'}</div>
    <div class="choque-label">com alta venda e baixa margem<br>
      <span style="color:#404058;font-size:11px;">você trabalha mais para ganhar menos</span>
    </div>
  </div>
  <div class="choque-item">
    <div class="choque-icon">📉</div>
    <div class="choque-value">{pct_churn:.0f}%</div>
    <div class="choque-label">dos clientes não voltaram a pedir<br>
      <span style="color:#404058;font-size:11px;">{choque['n_inativos']} clientes inativos há mais de 30 dias</span>
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
#  OS 3 PILARES (navegação para demos)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🔍 Explore os Módulos</div>', unsafe_allow_html=True)

modo = acesso["modo"]

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div style="background:#0f0f1e;border:1px solid #1c1c2e;border-radius:12px;padding:22px 20px;height:100%;">
      <div class="{'tag-demo' if modo=='demo' else 'tag-premium'}">
        {'Demo' if modo=='demo' else 'Premium'}
      </div>
      <div style="font-size:28px;margin-bottom:8px;">🚚</div>
      <div style="font-family:'Syne',Inter;font-size:16px;font-weight:700;
        color:#e2e2f0;margin-bottom:8px;">Operação</div>
      <p style="font-size:13px;color:#60607a;line-height:1.6;margin-bottom:14px;">
        Veja onde sua operação perde tempo e aumenta cancelamentos.
        {'Diagnóstico parcial disponível.' if modo=='demo' else 'Diagnóstico completo por bairro e horário.'}
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_Operacao.py", label="→ Ver Operação")

with col2:
    st.markdown(f"""
    <div style="background:#0f0f1e;border:1px solid #1c1c2e;border-radius:12px;padding:22px 20px;height:100%;">
      <div class="{'tag-demo' if modo=='demo' else 'tag-premium'}">
        {'Demo' if modo=='demo' else 'Premium'}
      </div>
      <div style="font-size:28px;margin-bottom:8px;">💰</div>
      <div style="font-family:'Syne',Inter;font-size:16px;font-weight:700;
        color:#e2e2f0;margin-bottom:8px;">Lucratividade</div>
      <p style="font-size:13px;color:#60607a;line-height:1.6;margin-bottom:14px;">
        Descubra quais pratos constroem — ou destroem — sua margem.
        {'Visão geral com teaser de problemas.' if modo=='demo' else 'Matriz completa + plano de ação por item.'}
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Lucratividade.py", label="→ Ver Lucratividade")

with col3:
    st.markdown(f"""
    <div style="background:#0f0f1e;border:1px solid #1c1c2e;border-radius:12px;padding:22px 20px;height:100%;">
      <div class="{'tag-demo' if modo=='demo' else 'tag-premium'}">
        {'Demo' if modo=='demo' else 'Premium'}
      </div>
      <div style="font-size:28px;margin-bottom:8px;">❤️</div>
      <div style="font-family:'Syne',Inter;font-size:16px;font-weight:700;
        color:#e2e2f0;margin-bottom:8px;">Fidelização</div>
      <p style="font-size:13px;color:#60607a;line-height:1.6;margin-bottom:14px;">
        Entenda por que seus clientes somem e como trazê-los de volta.
        {'Taxa de retorno e tempo médio.' if modo=='demo' else 'Cohort completo + lista de clientes para recuperar.'}
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_Fidelizacao.py", label="→ Ver Fidelização")

# ─────────────────────────────────────────────────────────────────────────────
#  CTA — bloquear ou mostrar status premium
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

if modo == "demo":
    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#110a1e,#0a110e);
        border:1px solid #221840;border-radius:16px;
        padding:38px 36px;text-align:center;margin-top:16px;">
      <div style="font-size:36px;margin-bottom:12px;">🔒</div>
      <div style="font-family:'Syne',Inter;font-size:24px;font-weight:800;
        color:#f0f0ff;margin-bottom:8px;">
        Quer ver o diagnóstico completo?
      </div>
      <p style="font-size:15px;color:#60607a;margin-bottom:6px;">
        Margem real por item · Plano de ação priorizado · Lista de clientes para recuperar
      </p>
      <p style="font-size:13px;color:#40404e;margin-bottom:28px;">
        Tudo em uma sessão de 30 minutos. Sem enrolação.
      </p>
      <a href="https://wa.me/5511999999999?text=Ol%C3%A1!%20Quero%20ver%20o%20diagn%C3%B3stico%20completo%20do%20meu%20delivery."
         style="display:inline-block;background:#25d366;color:#000;
           font-family:'Syne',Inter;font-size:15px;font-weight:700;
           padding:14px 32px;border-radius:8px;text-decoration:none;"
         target="_blank">
        💬 Falar no WhatsApp — É Gratuito
      </a>
    </div>
    """, unsafe_allow_html=True)
else:
    nome = acesso["cliente"]
    st.markdown(f"""
    <div style="
        background:rgba(52,211,153,0.05);
        border:1px solid rgba(52,211,153,0.15);border-radius:12px;
        padding:22px 26px;margin-top:16px;display:flex;
        align-items:center;gap:16px;">
      <div style="font-size:32px;">✅</div>
      <div>
        <div style="font-family:'Syne',Inter;font-size:16px;font-weight:700;color:#e2e2f0;">
          Acesso Premium ativo — {nome}
        </div>
        <div style="font-size:13px;color:#50507a;margin-top:4px;">
          Todos os módulos desbloqueados. Use o menu lateral para navegar.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# rodapé
st.markdown("""
<div style="text-align:center;padding:32px 0 8px;color:#252535;font-size:12px;">
  DeliveryPro Hub · Consultoria de Dados para Restaurantes
</div>
""", unsafe_allow_html=True)
