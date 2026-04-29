"""
Hub de Soluções — Landing Page Principal
Consultoria de Dados para Restaurantes e Delivery
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from utils import generate_mock_ifood_data, process_ifood_data, get_kpis

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="DeliveryPro | Hub de Soluções",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CSS CUSTOMIZADO — Tema Dark Premium
# ─────────────────────────────────────────────

st.markdown("""
<style>
/* Importar fonte premium */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* Reset e base */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Fundo geral */
.stApp {
    background: #0a0a0f;
    color: #e8e8f0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111118 !important;
    border-right: 1px solid #1e1e2e;
}

/* Hero section */
.hero-container {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a0a2e 50%, #0f1a0a 100%);
    border: 1px solid #2a1a4a;
    border-radius: 16px;
    padding: 52px 48px;
    margin-bottom: 40px;
    position: relative;
    overflow: hidden;
}

.hero-container::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -10%;
    width: 50%;
    height: 200%;
    background: radial-gradient(ellipse, rgba(139, 92, 246, 0.08) 0%, transparent 70%);
    pointer-events: none;
}

.hero-container::after {
    content: '';
    position: absolute;
    bottom: -30%;
    right: 5%;
    width: 40%;
    height: 150%;
    background: radial-gradient(ellipse, rgba(34, 197, 94, 0.06) 0%, transparent 70%);
    pointer-events: none;
}

.hero-badge {
    display: inline-block;
    background: rgba(139, 92, 246, 0.15);
    border: 1px solid rgba(139, 92, 246, 0.4);
    color: #a78bfa;
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 6px 14px;
    border-radius: 20px;
    margin-bottom: 20px;
}

.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(32px, 4vw, 52px);
    font-weight: 800;
    line-height: 1.15;
    color: #f0f0ff;
    margin-bottom: 20px;
    position: relative;
}

.hero-title span {
    background: linear-gradient(135deg, #a78bfa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-subtitle {
    font-size: 17px;
    font-weight: 300;
    color: #9090a8;
    line-height: 1.7;
    max-width: 580px;
    margin-bottom: 32px;
}

.hero-stats {
    display: flex;
    gap: 32px;
    flex-wrap: wrap;
}

.hero-stat {
    display: flex;
    flex-direction: column;
}

.hero-stat-value {
    font-family: 'Syne', sans-serif;
    font-size: 26px;
    font-weight: 700;
    color: #34d399;
}

.hero-stat-label {
    font-size: 12px;
    color: #606078;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Pilar cards */
.pillar-card {
    background: #111118;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 28px 24px;
    height: 100%;
    transition: border-color 0.2s;
    position: relative;
}

.pillar-card:hover {
    border-color: #3a2a5e;
}

.pillar-icon {
    font-size: 32px;
    margin-bottom: 12px;
    display: block;
}

.pillar-title {
    font-family: 'Syne', sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: #e8e8f0;
    margin-bottom: 8px;
}

.pillar-desc {
    font-size: 14px;
    color: #70708a;
    line-height: 1.6;
    margin-bottom: 14px;
}

.pillar-benefit {
    font-size: 13px;
    color: #34d399;
    font-weight: 500;
}

/* Seção de problema */
.problem-section {
    background: #0d0d16;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 36px 32px;
    margin: 32px 0;
}

.problem-title {
    font-family: 'Syne', sans-serif;
    font-size: 24px;
    font-weight: 700;
    color: #e8e8f0;
    margin-bottom: 8px;
}

.problem-subtitle {
    color: #70708a;
    font-size: 15px;
    margin-bottom: 24px;
}

.pain-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid #1a1a28;
}

.pain-item:last-child {
    border-bottom: none;
}

.pain-icon {
    font-size: 20px;
    flex-shrink: 0;
    margin-top: 1px;
}

.pain-text {
    font-size: 15px;
    color: #9090a8;
    line-height: 1.5;
}

.pain-text strong {
    color: #e8e8f0;
}

/* CTA Section */
.cta-section {
    background: linear-gradient(135deg, #1a0a2e, #0a1a0f);
    border: 1px solid #2a1a4a;
    border-radius: 16px;
    padding: 40px 36px;
    text-align: center;
    margin: 32px 0;
}

.cta-title {
    font-family: 'Syne', sans-serif;
    font-size: 28px;
    font-weight: 800;
    color: #f0f0ff;
    margin-bottom: 12px;
}

.cta-subtitle {
    color: #70708a;
    font-size: 16px;
    margin-bottom: 28px;
}

.wpp-button {
    display: inline-block;
    background: #25d366;
    color: #000 !important;
    font-family: 'Syne', sans-serif;
    font-size: 15px;
    font-weight: 700;
    padding: 14px 32px;
    border-radius: 8px;
    text-decoration: none !important;
    letter-spacing: 0.3px;
    transition: background 0.2s, transform 0.1s;
}

.wpp-button:hover {
    background: #20b85a;
    transform: translateY(-1px);
}

/* Upload box */
.upload-section {
    background: #0d0d16;
    border: 1px dashed #2a2a4a;
    border-radius: 12px;
    padding: 32px;
    margin: 24px 0;
    text-align: center;
}

.upload-title {
    font-family: 'Syne', sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: #e8e8f0;
    margin-bottom: 8px;
}

.upload-subtitle {
    color: #60607a;
    font-size: 14px;
    margin-bottom: 20px;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #111118 !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 10px !important;
    padding: 16px !important;
}

[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    color: #34d399 !important;
}

/* Section headers */
.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: #e8e8f0;
    margin: 32px 0 16px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid #1e1e2e;
}

/* Sidebar nav */
[data-testid="stSidebarNav"] a {
    color: #9090a8 !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stSidebarNav"] a:hover,
[data-testid="stSidebarNav"] a[aria-selected="true"] {
    color: #a78bfa !important;
    background: rgba(139, 92, 246, 0.08) !important;
}

/* Streamlit defaults override */
div[data-testid="stMarkdownContainer"] p {
    color: #9090a8;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    color: #e8e8f0 !important;
}

.stSelectbox label, .stDateInput label, .stMultiSelect label {
    color: #9090a8 !important;
    font-size: 13px !important;
}

/* Plotly chart container */
.js-plotly-plot {
    border-radius: 8px;
    overflow: hidden;
}

/* Divider */
hr {
    border-color: #1e1e2e !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding: 16px 0 8px;">
        <div style="font-family:'Syne',sans-serif; font-size:20px; font-weight:800; color:#e8e8f0;">
            🍕 DeliveryPro
        </div>
        <div style="font-size:12px; color:#50507a; letter-spacing:1px; text-transform:uppercase; margin-top:2px;">
            Hub de Soluções
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:11px; color:#50507a; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">
        Navegação
    </div>
    """, unsafe_allow_html=True)

    st.page_link("streamlit_app.py",      label="🏠  Visão Geral",     )
    st.page_link("pages/1_Operacao.py",   label="🚚  Operação",        )
    st.page_link("pages/2_Lucratividade.py", label="💰  Lucratividade",)
    st.page_link("pages/3_Fidelizacao.py",label="❤️  Fidelização",    )

    st.markdown("---")
    st.markdown("""
    <div style="font-size:12px; color:#50507a; line-height:1.6; padding:8px 0;">
        Dados gerados com <strong style="color:#a78bfa;">simulação iFood</strong>.<br>
        Suba seu CSV real para análise personalizada.
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  CARREGAR DADOS
# ─────────────────────────────────────────────

if "df_main" not in st.session_state:
    df_raw = generate_mock_ifood_data(800)
    st.session_state["df_main"] = process_ifood_data(df_raw)
    st.session_state["is_mock"] = True

df = st.session_state["df_main"]
kpis = get_kpis(df)


# ─────────────────────────────────────────────
#  HERO SECTION
# ─────────────────────────────────────────────

st.markdown("""
<div class="hero-container">
    <div class="hero-badge">📊 Consultoria de Dados para Delivery</div>
    <h1 class="hero-title">
        Transforme os dados do seu<br>
        Delivery em <span>Lucro Real.</span>
    </h1>
    <p class="hero-subtitle">
        Chega de abrir planilha e não saber o que fazer. Em menos de 5 minutos,
        você entende onde está perdendo dinheiro — e como recuperar.
    </p>
    <div class="hero-stats">
        <div class="hero-stat">
            <span class="hero-stat-value">+23%</span>
            <span class="hero-stat-label">Aumento médio de margem</span>
        </div>
        <div class="hero-stat">
            <span class="hero-stat-value">-18%</span>
            <span class="hero-stat-label">Redução em cancelamentos</span>
        </div>
        <div class="hero-stat">
            <span class="hero-stat-value">+31%</span>
            <span class="hero-stat-label">Retenção de clientes</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  UPLOAD DE ARQUIVO
# ─────────────────────────────────────────────

st.markdown("""
<div class="upload-title" style="font-family:'Syne',sans-serif;font-size:20px;font-weight:700;color:#e8e8f0;margin-bottom:4px;">
    📂 Diagnóstico Instantâneo
</div>
<div class="upload-subtitle" style="color:#60607a;font-size:14px;margin-bottom:12px;">
    Suba o CSV do seu Portal do Parceiro iFood e veja a análise em segundos.
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    label="Arraste ou clique para selecionar o relatório (.csv)",
    type=["csv"],
    help="Exporte pelo Portal do Parceiro iFood > Relatórios > Pedidos",
    label_visibility="visible",
)

if uploaded_file:
    try:
        df_upload = pd.read_csv(uploaded_file, sep=None, engine="python")
        df_processed = process_ifood_data(df_upload)
        st.session_state["df_main"] = df_processed
        st.session_state["is_mock"] = False
        df = df_processed
        kpis = get_kpis(df)
        st.success(f"✅ Arquivo carregado! **{len(df):,} pedidos** encontrados. Navegue pelos módulos no menu lateral.")
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}. Verifique se é um CSV válido do iFood.")
else:
    if st.session_state.get("is_mock"):
        st.info("👆 Nenhum arquivo enviado ainda. Exibindo **dados de demonstração** com 800 pedidos simulados.")


# ─────────────────────────────────────────────
#  KPIs PRINCIPAIS
# ─────────────────────────────────────────────

st.markdown('<div class="section-header">📈 Visão Geral do Período</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Faturamento Bruto",
        f"R$ {kpis['faturamento']:,.0f}".replace(",", "."),
        delta="+12% vs mês anterior",
    )
with c2:
    st.metric(
        "Receita Líquida (após taxas)",
        f"R$ {kpis['receita_liquida']:,.0f}".replace(",", "."),
        delta="+8% vs mês anterior",
    )
with c3:
    st.metric(
        "Ticket Médio",
        f"R$ {kpis['ticket_medio']:.2f}".replace(".", ","),
        delta="+R$ 3,40",
    )
with c4:
    st.metric(
        "Taxa de Cancelamento",
        f"{kpis['taxa_cancelamento']:.1f}%",
        delta="-2.1%",
        delta_color="inverse",
    )

st.markdown("<br>", unsafe_allow_html=True)
c5, c6, c7, c8 = st.columns(4)
with c5:
    st.metric("Total de Pedidos", f"{kpis['total_pedidos']:,}".replace(",", "."))
with c6:
    st.metric(
        "Comissão paga ao iFood",
        f"R$ {kpis['comissao_total']:,.0f}".replace(",", "."),
        delta="Custo da plataforma",
        delta_color="off",
    )
with c7:
    st.metric(
        "Perda em Cancelamentos",
        f"R$ {kpis['perda_cancelamentos']:,.0f}".replace(",", "."),
        delta="Recuperável",
        delta_color="off",
    )
with c8:
    margem = (kpis['receita_liquida'] / kpis['faturamento'] * 100) if kpis['faturamento'] else 0
    st.metric("Margem Líquida", f"{margem:.1f}%")


# ─────────────────────────────────────────────
#  MINI GRÁFICO — Faturamento por semana
# ─────────────────────────────────────────────

st.markdown('<div class="section-header">📅 Faturamento nas Últimas Semanas</div>', unsafe_allow_html=True)

df_concluidos = df[~df["is_cancelado"]].copy()
df_concluidos["Semana"] = df_concluidos["Data do Pedido"].dt.to_period("W").dt.start_time
fat_semanal = df_concluidos.groupby("Semana")["Valor Bruto"].sum().reset_index()
fat_semanal = fat_semanal.tail(12)

fig_fat = go.Figure()
fig_fat.add_trace(go.Scatter(
    x=fat_semanal["Semana"],
    y=fat_semanal["Valor Bruto"],
    fill="tozeroy",
    mode="lines+markers",
    line=dict(color="#a78bfa", width=2.5),
    fillcolor="rgba(139,92,246,0.08)",
    marker=dict(color="#a78bfa", size=6),
    hovertemplate="Semana: %{x|%d/%m}<br>Faturamento: R$ %{y:,.2f}<extra></extra>",
))
fig_fat.update_layout(
    height=240,
    margin=dict(l=0, r=0, t=8, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False, color="#50507a", tickformat="%d/%m"),
    yaxis=dict(showgrid=True, gridcolor="#1a1a2e", color="#50507a",
               tickprefix="R$ ", tickformat=",.0f"),
    font=dict(family="DM Sans", color="#9090a8"),
    hovermode="x unified",
)
st.plotly_chart(fig_fat, use_container_width=True)


# ─────────────────────────────────────────────
#  SEÇÃO: PROBLEMA QUE RESOLVEMOS
# ─────────────────────────────────────────────

st.markdown('<div class="section-header">🔍 O Problema que Resolvemos</div>', unsafe_allow_html=True)

st.markdown("""
<div class="problem-section">
    <p class="problem-title">Todo dono de delivery vive esse caos:</p>
    <p class="problem-subtitle">Dados existem. Decisão não acontece. Dinheiro some.</p>
    <div class="pain-item">
        <span class="pain-icon">😤</span>
        <span class="pain-text"><strong>Relatórios do iFood viram planilha e ficam lá.</strong> Você exporta, abre, fecha. Não sabe o que fazer com os números.</span>
    </div>
    <div class="pain-item">
        <span class="pain-icon">🍕</span>
        <span class="pain-text"><strong>Tem prato no cardápio que vende bem, mas te deixa no prejuízo.</strong> Você trabalha mais para ganhar menos e não sabe qual é.</span>
    </div>
    <div class="pain-item">
        <span class="pain-icon">🚚</span>
        <span class="pain-text"><strong>Clientes somem e você não sabe por quê.</strong> A taxa de cancelamento cresce, mas você só descobre quando já perdeu o mês.</span>
    </div>
    <div class="pain-item">
        <span class="pain-icon">💸</span>
        <span class="pain-text"><strong>A comissão do iFood come sua margem.</strong> Mas sem um número claro, fica difícil saber quanto sobra de verdade para o seu bolso.</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  3 PILARES
# ─────────────────────────────────────────────

st.markdown('<div class="section-header">🏛️ Os 3 Pilares do Crescimento</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="pillar-card">
        <span class="pillar-icon">🚚</span>
        <div class="pillar-title">Operação Eficiente</div>
        <p class="pillar-desc">
            Identifique os bairros com mais cancelamentos e os horários de pico que afundam seu tempo médio de entrega.
            Veja onde sua operação perde dinheiro no mapa.
        </p>
        <div class="pillar-benefit">→ Redução de até 18% nos cancelamentos</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_Operacao.py", label="Ver Análise de Operação →")

with col2:
    st.markdown("""
    <div class="pillar-card">
        <span class="pillar-icon">💰</span>
        <div class="pillar-title">Lucro no Cardápio</div>
        <p class="pillar-desc">
            Descubra quais pratos são heróis e quais são vilões da sua margem.
            Matriz visual que mostra onde ajustar preço ou cortar item.
        </p>
        <div class="pillar-benefit">→ Aumento médio de 23% na margem líquida</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Lucratividade.py", label="Ver Engenharia de Cardápio →")

with col3:
    st.markdown("""
    <div class="pillar-card">
        <span class="pillar-icon">❤️</span>
        <div class="pillar-title">Clientes Fiéis</div>
        <p class="pillar-desc">
            Saiba quais clientes estão sumindo antes que seja tarde.
            Lista pronta para ação de recuperação com cupom ou contato direto.
        </p>
        <div class="pillar-benefit">→ +31% de retenção com ações simples</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_Fidelizacao.py", label="Ver Análise de Clientes →")


# ─────────────────────────────────────────────
#  CTA WHATSAPP
# ─────────────────────────────────────────────

st.markdown("""
<div class="cta-section">
    <div class="cta-title">Pronto para parar de perder dinheiro?</div>
    <p class="cta-subtitle">
        Agende uma sessão de diagnóstico gratuita de 30 minutos.<br>
        Analisamos seu relatório juntos e saímos com um plano de ação.
    </p>
    <a href="https://wa.me/5511999999999?text=Olá!%20Quero%20um%20diagnóstico%20gratuito%20do%20meu%20delivery." 
       class="wpp-button" target="_blank">
        💬  Falar no WhatsApp — É Grátis
    </a>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; padding: 24px 0 8px; color:#35354a; font-size:12px;">
    DeliveryPro Hub © 2025 — Consultoria de Dados para Restaurantes
</div>
""", unsafe_allow_html=True)
