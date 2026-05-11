"""
Módulo Fidelização — Demo parcial / Premium completo
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (
    generate_mock_ifood_data, process_ifood_data,
    detectar_modo, inject_css, render_sidebar, render_lock_card,
)

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fidelização | DeliveryPro",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
render_sidebar(active="fidelizacao")
acesso = detectar_modo()
modo   = acesso["modo"]

# ── Dados ─────────────────────────────────────────────────────────────────────
if "df_main" not in st.session_state:
    st.session_state["df_main"] = process_ifood_data(generate_mock_ifood_data(800))

df    = st.session_state["df_main"]
df_ok = df[~df["is_cancelado"]].copy()

# ── Métricas de clientes (base para ambos os modos) ───────────────────────────
hoje = df_ok["Data do Pedido"].max()

clientes = (
    df_ok.groupby("ID do Cliente")
    .agg(
        primeiro =("Data do Pedido", "min"),
        ultimo   =("Data do Pedido", "max"),
        pedidos  =("ID do Pedido",   "count"),
        receita  =("Valor Bruto",    "sum"),
    )
    .reset_index()
)
clientes["dias_inativo"]   = (hoje - clientes["ultimo"]).dt.days
clientes["intervalo_medio"] = (
    (clientes["ultimo"] - clientes["primeiro"]).dt.days
    / clientes["pedidos"].clip(lower=1)
)

n_total    = len(clientes)
n_inativos = len(clientes[clientes["dias_inativo"] > 30])
n_ativos   = n_total - n_inativos
pct_retorno = n_ativos / n_total * 100 if n_total else 0
pct_churn   = n_inativos / n_total * 100 if n_total else 0
intervalo   = clientes["intervalo_medio"].median()
ticket_med  = df_ok["Valor Bruto"].mean()

# ── Header ────────────────────────────────────────────────────────────────────
tag_html = f'<div class="{"tag-demo" if modo == "demo" else "tag-premium"}">{"Demo" if modo == "demo" else "Premium"}</div>'

st.markdown(f"""
{tag_html}
<div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;
  color:#e2e2f0;line-height:1.2;margin-bottom:6px;">
  ❤️ Fidelização & Retenção
</div>
<div style="color:#50507a;font-size:14px;margin-bottom:28px;">
  {"Taxa de retorno e comportamento geral dos clientes. Análise completa disponível no plano completo." if modo == "demo"
   else "Diagnóstico completo — cohort, churn e lista de clientes para recuperar agora."}
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SEÇÃO 1 — KPIs (ambos os modos)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Saúde da Base de Clientes</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Clientes Únicos",       f"{n_total:,}".replace(",","."))
c2.metric("Clientes Ativos (30d)", f"{n_ativos:,}".replace(",","."),
    delta=f"{pct_retorno:.0f}% da base", delta_color="off")
c3.metric("Taxa de Retorno",       f"{pct_retorno:.1f}%")
c4.metric("Intervalo Médio entre Pedidos", f"{intervalo:.0f} dias")

# ─────────────────────────────────────────────────────────────────────────────
#  SEÇÃO 2 — Funil de retenção (ambos os modos)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📉 Funil de Retenção</div>', unsafe_allow_html=True)

col_funil, col_insight = st.columns([3, 2])

with col_funil:
    fig_funil = go.Figure(go.Bar(
        x=[n_ativos, n_inativos],
        y=["🟢 Compraram recentemente", "🔴 Não voltam há +30 dias"],
        orientation="h",
        marker=dict(color=["#34d399", "#f87171"], opacity=0.85),
        text=[f"{n_ativos} clientes ({pct_retorno:.0f}%)",
              f"{n_inativos} clientes ({pct_churn:.0f}%)"],
        textposition="outside",
        hovertemplate="%{y}: %{x} clientes<extra></extra>",
    ))
    fig_funil.update_layout(
        height=200,
        margin=dict(l=0, r=120, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#1a1a28", color="#50507a"),
        yaxis=dict(showgrid=False, color="#9090a8"),
        font=dict(family="DM Sans", color="#9090a8"),
    )
    st.plotly_chart(fig_funil, use_container_width=True)

with col_insight:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if pct_churn > 50:
        nivel = "red"
        titulo = f"⚠️ Mais da metade dos clientes não voltou"
    elif pct_churn > 35:
        nivel = "yellow"
        titulo = f"⚠️ Retenção abaixo do ideal"
    else:
        nivel = "green"
        titulo = f"✅ Retenção dentro do esperado"

    st.markdown(f"""
    <div class="insight {nivel}">
      <div class="insight-title">{titulo}</div>
      <div class="insight-text">
        <strong>{pct_churn:.0f}%</strong> dos seus clientes estão inativos há mais de 30 dias.
        Trazer um cliente de volta custa <strong>5x menos</strong> do que conquistar um novo.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Teaser: impacto financeiro dos inativos
    perda_estimada = n_inativos * 0.25 * ticket_med
    st.markdown(f"""
    <div class="insight yellow">
      <div class="insight-title">💸 Potencial de recuperação</div>
      <div class="insight-text">
        Se <strong>25%</strong> dos clientes inativos voltarem a pedir,
        isso representa aproximadamente
        <strong>R$ {perda_estimada:,.0f}</strong> em receita adicional.
        {"🔒 Ver lista completa no plano completo." if modo == "demo" else ""}
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SEÇÃO 3 — DEMO: teaser + lock  |  PREMIUM: cohort + lista
# ─────────────────────────────────────────────────────────────────────────────

if modo == "demo":
    st.markdown('<div class="section-header">🔄 Análise de Retenção por Período</div>', unsafe_allow_html=True)

    # Cohort borrado
    st.markdown('<div style="opacity:0.15;filter:blur(4px);pointer-events:none;">', unsafe_allow_html=True)

    df_ok_c = df_ok.copy()
    df_ok_c["Mês Cohort"] = df_ok_c.groupby("ID do Cliente")["Data do Pedido"].transform("min").dt.to_period("M")
    df_ok_c["Mês Pedido"] = df_ok_c["Data do Pedido"].dt.to_period("M")
    df_ok_c["Período"]    = (df_ok_c["Mês Pedido"] - df_ok_c["Mês Cohort"]).apply(lambda x: x.n)

    cohort_data = (
        df_ok_c.groupby(["Mês Cohort","Período"])["ID do Cliente"]
        .nunique().reset_index()
    )
    cohort_pivot = cohort_data.pivot_table(index="Mês Cohort", columns="Período", values="ID do Cliente")
    cohort_pct   = (cohort_pivot.div(cohort_pivot[0], axis=0) * 100).tail(5)

    fig_blur = go.Figure(go.Heatmap(
        z=cohort_pct.values,
        x=[f"Mês {i}" for i in cohort_pct.columns],
        y=[str(p) for p in cohort_pct.index],
        colorscale=[[0,"#1a0a0a"],[0.4,"#7c2d12"],[0.7,"#f59e0b"],[1,"#34d399"]],
        showscale=False,
    ))
    fig_blur.update_layout(
        height=240,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_blur, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    render_lock_card(
        titulo="Análise Completa de Fidelização",
        itens_bloqueados=[
            "Cohort real de retenção mês a mês",
            "Segmentação de clientes por risco de churn",
            "Lista completa de clientes inativos para recuperar",
            "Sugestão de campanha e segmentação por valor",
        ],
    )

else:
    # ── PREMIUM: Cohort completo ──────────────────────────────────────────
    st.markdown('<div class="section-header">🔄 Retenção Mensal (Cohort)</div>', unsafe_allow_html=True)

    df_ok_c = df_ok.copy()
    df_ok_c["Mês Cohort"] = df_ok_c.groupby("ID do Cliente")["Data do Pedido"].transform("min").dt.to_period("M")
    df_ok_c["Mês Pedido"] = df_ok_c["Data do Pedido"].dt.to_period("M")
    df_ok_c["Período"]    = (df_ok_c["Mês Pedido"] - df_ok_c["Mês Cohort"]).apply(lambda x: x.n)

    cohort_data = (
        df_ok_c.groupby(["Mês Cohort","Período"])["ID do Cliente"]
        .nunique().reset_index()
    )
    cohort_pivot = cohort_data.pivot_table(index="Mês Cohort", columns="Período", values="ID do Cliente")
    cohort_pct   = (cohort_pivot.div(cohort_pivot[0], axis=0) * 100).tail(6)

    fig_cohort = go.Figure(go.Heatmap(
        z=cohort_pct.values,
        x=[f"Mês {i}" for i in cohort_pct.columns],
        y=[str(p) for p in cohort_pct.index],
        colorscale=[[0,"#1a0a0a"],[0.3,"#7c2d12"],[0.6,"#f59e0b"],[1,"#34d399"]],
        text=cohort_pct.map(
            lambda x: f"{x:.0f}%" if pd.notna(x) else ""
        ).values,
        texttemplate="%{text}",
        textfont=dict(size=11, family="DM Sans"),
        hovertemplate="Cohort: %{y}<br>%{x}<br>Retenção: %{z:.1f}%<extra></extra>",
        showscale=True,
        colorbar=dict(
            title=dict(
                text="Retenção %",
                font=dict(color="#9090a8"),
            ),
            tickfont=dict(color="#9090a8"),
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
    <div style="font-size:12px;color:#35354a;margin-top:-8px;margin-bottom:20px;">
      Cada linha = grupo de clientes pelo mês da 1ª compra.
      Cada coluna = % que voltou naquele mês seguinte. Verde = boa retenção.
    </div>
    """, unsafe_allow_html=True)

    # ── PREMIUM: Lista de clientes para recuperar ─────────────────────────
    st.markdown('<div class="section-header">🎯 Clientes Para Recuperar Agora</div>', unsafe_allow_html=True)

    # Classificar por risco
    def risco(dias):
        if dias > 60:  return "🔴 Alto Risco"
        elif dias > 30: return "🟡 Atenção"
        else:           return "🟢 Ativo"

    clientes["risco"] = clientes["dias_inativo"].apply(risco)

    inativos_lista = (
        clientes[clientes["risco"] != "🟢 Ativo"]
        .sort_values("receita", ascending=False)
        .head(20)
    )

    st.markdown(f"""
    <div class="insight yellow" style="margin-bottom:16px;">
      <div class="insight-title">💡 Como usar essa lista</div>
      <div class="insight-text">
        {len(inativos_lista)} clientes com maior valor histórico que pararam de pedir.
        Priorize os de <span style="color:#f87171;">Alto Risco</span> com ticket acima da média.
        Um cupom de R$ 10–15 enviado via iFood pode trazer ~25% de volta.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Filtro rápido
    filtro_risco = st.radio(
        "Filtrar por risco",
        ["Todos", "🔴 Alto Risco", "🟡 Atenção"],
        horizontal=True,
        key="filtro_risco_fid",
    )
    if filtro_risco != "Todos":
        inativos_lista = inativos_lista[inativos_lista["risco"] == filtro_risco]

    # Cards em duas colunas
    col_a, col_b = st.columns(2)
    for i, (_, row) in enumerate(inativos_lista.iterrows()):
        col = col_a if i % 2 == 0 else col_b

        bg   = "rgba(248,113,113,0.07)" if "Alto" in row["risco"] else "rgba(245,158,11,0.06)"
        bord = "rgba(248,113,113,0.2)"  if "Alto" in row["risco"] else "rgba(245,158,11,0.18)"
        badge_bg  = "rgba(248,113,113,0.2)"  if "Alto" in row["risco"] else "rgba(245,158,11,0.2)"
        badge_cor = "#f87171" if "Alto" in row["risco"] else "#f59e0b"

        with col:
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {bord};border-radius:10px;
              padding:14px 16px;margin:5px 0;display:flex;
              justify-content:space-between;align-items:center;">
              <div>
                <div style="font-family:'Syne',sans-serif;font-size:13px;
                  font-weight:700;color:#e2e2f0;">{row['ID do Cliente']}</div>
                <div style="font-size:12px;color:#60607a;margin-top:2px;">
                  {int(row['pedidos'])} pedidos · R$ {row['receita']:,.0f} histórico
                </div>
              </div>
              <div style="background:{badge_bg};color:{badge_cor};
                font-size:11px;font-weight:600;padding:3px 8px;
                border-radius:4px;white-space:nowrap;">
                {int(row['dias_inativo'])} dias sem pedir
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── PREMIUM: Novos clientes por mês ──────────────────────────────────
    st.markdown('<div class="section-header">📈 Novos Clientes por Mês</div>', unsafe_allow_html=True)

    primeiros = (
        df_ok.groupby("ID do Cliente")["Data do Pedido"]
        .min().reset_index()
        .rename(columns={"Data do Pedido": "Primeiro Pedido"})
    )
    primeiros["Mês"] = primeiros["Primeiro Pedido"].dt.to_period("M").dt.start_time
    novos_mes = primeiros.groupby("Mês").size().reset_index(name="Novos").tail(6)

    fig_novos = go.Figure(go.Bar(
        x=novos_mes["Mês"],
        y=novos_mes["Novos"],
        marker=dict(color="#a78bfa", opacity=0.8),
        text=novos_mes["Novos"],
        textposition="outside",
        hovertemplate="%{x|%b/%Y}: %{y} novos clientes<extra></extra>",
    ))
    fig_novos.update_layout(
        height=240,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, color="#9090a8", tickformat="%b/%y"),
        yaxis=dict(showgrid=True, gridcolor="#1a1a28", color="#50507a"),
        font=dict(family="DM Sans", color="#9090a8"),
    )
    st.plotly_chart(fig_novos, use_container_width=True)

    # Ajuste manual master
    ajuste = st.session_state.get("ajuste_manual", "")
    if ajuste and acesso.get("is_master"):
        st.markdown(f"""
        <div class="insight purple" style="margin-top:16px;">
          <div class="insight-title">🔎 Observações do Especialista</div>
          <div class="insight-text">{ajuste}</div>
        </div>
        """, unsafe_allow_html=True)
