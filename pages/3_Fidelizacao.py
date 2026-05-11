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
n_recorrentes = len(clientes[clientes["pedidos"] > 1])
pct_retorno   = n_recorrentes / n_total * 100 if n_total else 0
pct_ativos   = n_ativos / n_total * 100 if n_total else 0
pct_churn   = n_inativos / n_total * 100 if n_total else 0
intervalo   = clientes["intervalo_medio"].median()
ticket_med  = df_ok["Valor Bruto"].mean()

# ── Header ────────────────────────────────────────────────────────────────────
tag_html = f'<div class="{"tag-demo" if modo == "demo" else "tag-premium"}">{"Demo" if modo == "demo" else "Premium"}</div>'

st.markdown(f"""
{tag_html}
<div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;
  color:#2f5f98;line-height:1.2;margin-bottom:6px;">
  ❤️ Fidelização & Retenção
</div>
<div style="color:#2f5f98;font-size:14px;margin-bottom:28px;">
  {"Taxa de retorno e comportamento geral dos clientes. Análise completa disponível no plano completo." if modo == "demo"
   else "Diagnóstico completo — cohort, churn e lista de clientes para recuperar agora."}
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SEÇÃO 1 — KPIs (ambos os modos)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Saúde da Base de Clientes</div>', unsafe_allow_html=True)

ltv = clientes["receita"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Clientes Únicos",       f"{n_total:,}".replace(",","."))
c2.metric("Clientes Ativos (30d)", f"{n_ativos:,}".replace(",","."),
    delta=f"{pct_ativos:.0f}% da base", delta_color="off")
c3.metric("Clientes Recorrentes",  f"{pct_retorno:.1f}%",
    delta=f"{n_recorrentes} clientes", delta_color="off")
c4.metric("Intervalo Médio entre Pedidos", f"{intervalo:.0f} dias")
c5.metric("LTV Médio por Cliente", f"R$ {ltv:,.0f}".replace(",","."))

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

# ── PREMIUM: Distribuição de Frequência ──────────────────────────────
    st.markdown('<div class="section-header">🍩 Distribuição de Frequência</div>', unsafe_allow_html=True)

    clientes["segmento"] = pd.cut(
        clientes["pedidos"],
        bins=[0, 1, 4, float("inf")],
        labels=["🆕 Novos (1 pedido)", "🔄 Recorrentes (2–4)", "⭐ Fiéis (5+)"],
    )
    seg_counts = clientes["segmento"].value_counts().reindex(
        ["🆕 Novos (1 pedido)", "🔄 Recorrentes (2–4)", "⭐ Fiéis (5+)"]
    )

    col_pizza, col_seg_insight = st.columns([2, 1])

    with col_pizza:
        fig_seg = go.Figure(go.Bar(
            x=seg_counts.index.tolist(),
            y=seg_counts.values.tolist(),
            marker=dict(color=["#a78bfa", "#34d399", "#f59e0b"], opacity=0.85),
            text=[f"{v} ({v/n_total*100:.0f}%)" for v in seg_counts.values],
            textposition="outside",
            hovertemplate="%{x}<br>%{y} clientes<extra></extra>",
        ))
        fig_seg.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=10, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, color="#9090a8"),
            yaxis=dict(showgrid=True, gridcolor="#1a1a28", color="#50507a", title="Clientes"),
            font=dict(family="DM Sans", color="#9090a8"),
        )
        st.plotly_chart(fig_seg, use_container_width=True)

    with col_seg_insight:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        pct_fieis = seg_counts.get("⭐ Fiéis (5+)", 0) / n_total * 100 if n_total else 0
        pct_novos = seg_counts.get("🆕 Novos (1 pedido)", 0) / n_total * 100 if n_total else 0
        st.markdown(f"""
        <div class="insight yellow">
          <div class="insight-title">⭐ Fiéis representam {pct_fieis:.0f}% da base</div>
          <div class="insight-text">
            Clientes VIP compram com frequência e têm ticket maior.
            Priorize ações para migrar recorrentes para esse grupo.
          </div>
        </div>
        <div class="insight purple" style="margin-top:10px;">
          <div class="insight-title">🆕 {pct_novos:.0f}% compraram só uma vez</div>
          <div class="insight-text">
            Alta concentração de novos indica dificuldade de retenção.
            Um cupom de segunda compra pode converter boa parte desse grupo.
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── PREMIUM: Ranking de Clientes Fiéis ───────────────────────────────
    st.markdown('<div class="section-header">🏆 Ranking de Clientes Fiéis</div>', unsafe_allow_html=True)

    top_clientes = (
        clientes.sort_values("receita", ascending=False)
        .head(20)
        .copy()
    )
    top_clientes["ticket_medio"]   = top_clientes["receita"] / top_clientes["pedidos"]
    top_clientes["ultimo_pedido"]  = top_clientes["dias_inativo"].apply(lambda x: f"há {int(x)} dias")
    top_clientes["Total Gasto"]    = top_clientes["receita"].apply(lambda x: f"R$ {x:,.0f}".replace(",","."))
    top_clientes["Ticket Médio"]   = top_clientes["ticket_medio"].apply(lambda x: f"R$ {x:.2f}".replace(".",","))
    top_clientes["Qtd Pedidos"]    = top_clientes["pedidos"].astype(int)
    top_clientes["Último Pedido"]  = top_clientes["ultimo_pedido"]
    
    tabela_top = top_clientes[["ID do Cliente","Total Gasto","Qtd Pedidos","Ticket Médio","Último Pedido","dias_inativo"]].copy()
    tabela_top.columns = ["ID Cliente","Total Gasto","Qtd Pedidos","Ticket Médio","Último Pedido","dias_inativo"]

    st.dataframe(
        tabela_top,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID Cliente":    st.column_config.TextColumn(width="medium"),
            "Total Gasto":   st.column_config.TextColumn(width="medium"),
            "Qtd Pedidos":   st.column_config.NumberColumn(width="small"),
            "Ticket Médio":  st.column_config.TextColumn(width="medium"),
            "Último Pedido": st.column_config.TextColumn(
                width="medium",
                help="Quanto mais vermelho, mais tempo sem comprar",
            ),
            "dias_inativo":  st.column_config.ProgressColumn(
                label="Inatividade",
                width="medium",
                min_value=0,
                max_value=int(top_clientes["dias_inativo"].max()),
                format="%d dias",
            ),
        },
    )

    # Ajuste manual master
    ajuste = st.session_state.get("ajuste_manual", "")
    if ajuste and acesso.get("is_master"):
        st.markdown(f"""
        <div class="insight purple" style="margin-top:16px;">
          <div class="insight-title">🔎 Observações do Especialista</div>
          <div class="insight-text">{ajuste}</div>
        </div>
        """, unsafe_allow_html=True)
