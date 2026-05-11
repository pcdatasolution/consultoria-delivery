"""
Módulo Lucratividade — Demo parcial / Premium completo
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (
    generate_mock_ifood_data, process_ifood_data, get_kpis,
    detectar_modo, inject_css, render_sidebar, render_lock_card,
    ITENS_CARDAPIO, MARGEM_PROXY,
)

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lucratividade | DeliveryPro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
render_sidebar(active="lucratividade")
acesso = detectar_modo()
modo   = acesso["modo"]

# ── Dados ─────────────────────────────────────────────────────────────────────
if "df_main" not in st.session_state:
    st.session_state["df_main"] = process_ifood_data(generate_mock_ifood_data(800))

df    = st.session_state["df_main"]
df_ok = df[~df["is_cancelado"]].copy()
kpis  = get_kpis(df)

# ── Calcular stats por item (necessário nos dois modos) ───────────────────────
item_stats = (
    df_ok.groupby("Nome do Item")
    .agg(
        vendas   =("Nome do Item", "count"),
        receita  =("Valor dos Itens", "sum"),
        comissao =("Comissão iFood", "sum"),
    )
    .reset_index()
)
item_stats["ticket"]  = item_stats["receita"] / item_stats["vendas"]
item_stats["margem"]  = item_stats["Nome do Item"].apply(
    lambda n: (ITENS_CARDAPIO[n]["preco"] - ITENS_CARDAPIO[n]["custo"]) / ITENS_CARDAPIO[n]["preco"]
    if n in ITENS_CARDAPIO else MARGEM_PROXY
)
item_stats["rec_liq"] = item_stats["receita"] - item_stats["comissao"]

med_v = item_stats["vendas"].median()
med_m = item_stats["margem"].median()

def classificar(row):
    alto_v = row["vendas"]  >= med_v
    alta_m = row["margem"]  >= med_m
    if   alto_v and alta_m:  return "⭐ Estrela"
    elif not alto_v and alta_m: return "💎 Potencial"
    elif alto_v and not alta_m: return "🐴 Cavalo de Batalha"
    else:                    return "❌ Problema"

item_stats["categoria"] = item_stats.apply(classificar, axis=1)

# ── Header ────────────────────────────────────────────────────────────────────
tag_html = f'<div class="{"tag-demo" if modo == "demo" else "tag-premium"}">{"Demo" if modo == "demo" else "Premium"}</div>'

st.markdown(f"""
{tag_html}
<div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;
  color:#e2e2f0;line-height:1.2;margin-bottom:6px;">
  💰 Lucratividade & Cardápio
</div>
<div style="color:#50507a;font-size:14px;margin-bottom:28px;">
  {"Visão geral de faturamento e volume. Análise de margem disponível no plano completo." if modo == "demo"
   else "Diagnóstico completo — margem por item, matriz de cardápio e plano de ação."}
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SEÇÃO 1 — KPIs (ambos os modos)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Números Gerais</div>', unsafe_allow_html=True)

receita_total = item_stats["receita"].sum()
receita_liq   = item_stats["rec_liq"].sum()
margem_media  = receita_liq / receita_total * 100 if receita_total else 0
comissao_tot  = item_stats["comissao"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Receita Total no Período",
    f"R$ {receita_total:,.0f}".replace(",","."))
c2.metric("Receita Líquida (após iFood)",
    f"R$ {receita_liq:,.0f}".replace(",","."))
c3.metric("Margem Líquida Média",
    f"{margem_media:.1f}%")
c4.metric("Comissão Total paga ao iFood",
    f"R$ {comissao_tot:,.0f}".replace(",","."),
    delta="Custo da plataforma", delta_color="off")

# ─────────────────────────────────────────────────────────────────────────────
#  SEÇÃO 2 — Receita por item (ambos os modos, mas demo esconde margem)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📦 Vendas por Item</div>', unsafe_allow_html=True)

top_itens = item_stats.sort_values("receita", ascending=True).tail(10)

fig_itens = go.Figure(go.Bar(
    y=top_itens["Nome do Item"],
    x=top_itens["receita"],
    orientation="h",
    marker=dict(color="#a78bfa", opacity=0.85),
    text=top_itens["receita"].apply(lambda x: f"R$ {x:,.0f}".replace(",",".")),
    textposition="outside",
    customdata=top_itens["vendas"],
    hovertemplate="%{y}<br>Receita: R$ %{x:,.0f}<br>Pedidos: %{customdata}<extra></extra>",
))
fig_itens.update_layout(
    height=340,
    margin=dict(l=0, r=100, t=8, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=True, gridcolor="#1a1a28", color="#50507a", tickprefix="R$ "),
    yaxis=dict(showgrid=False, color="#9090a8"),
    font=dict(family="DM Sans", color="#9090a8"),
)
st.plotly_chart(fig_itens, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SEÇÃO 3 — Teaser de problema (ambos os modos, profundidade diferente)
# ─────────────────────────────────────────────────────────────────────────────
cavalos    = item_stats[item_stats["categoria"] == "🐴 Cavalo de Batalha"]
problemas  = item_stats[item_stats["categoria"] == "❌ Problema"]
n_risco    = len(cavalos) + len(problemas)

if modo == "demo":
    # Mostra o número do problema, mas não revela quais itens são
    st.markdown(f"""
    <div class="insight red">
      <div class="insight-title">🔥 {n_risco} {'item identificado' if n_risco == 1 else 'itens identificados'} com ineficiência de margem</div>
      <div class="insight-text">
        Esses produtos representam uma parte relevante do seu volume de vendas,
        mas a margem estimada está abaixo da média — você trabalha mais para ganhar menos neles.
        <br><br>
        <span style="color:#404058;font-size:12px;">
          🔒 Para ver quais são, quanto estão custando e o que ajustar,
          acesse o diagnóstico completo.
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # Premium: mostra breakdown real
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class="insight red">
          <div class="insight-title">🐴 {len(cavalos)} item(ns) — alto volume, margem baixa</div>
          <div class="insight-text">
            {', '.join(cavalos['Nome do Item'].head(3).tolist())}.
            Vendem bem mas comprimem sua margem. Candidatos a revisão de preço.
          </div>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        potenciais = item_stats[item_stats["categoria"] == "💎 Potencial"]
        st.markdown(f"""
        <div class="insight purple">
          <div class="insight-title">💎 {len(potenciais)} item(ns) — boa margem, pouca visibilidade</div>
          <div class="insight-text">
            {', '.join(potenciais['Nome do Item'].head(3).tolist())}.
            Margem acima da média mas baixo volume. Oportunidade não explorada.
          </div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SEÇÃO 4 — DEMO: lock  |  PREMIUM: matriz completa + vazamento + plano
# ─────────────────────────────────────────────────────────────────────────────

if modo == "demo":
    st.markdown('<div class="section-header">🎯 Matriz de Cardápio</div>', unsafe_allow_html=True)

    # Scatter borrado
    st.markdown('<div style="opacity:0.15;filter:blur(4px);pointer-events:none;">', unsafe_allow_html=True)

    COLOR_MAP = {
        "⭐ Estrela":           "#34d399",
        "💎 Potencial":         "#a78bfa",
        "🐴 Cavalo de Batalha": "#f59e0b",
        "❌ Problema":          "#f87171",
    }
    fig_blur = go.Figure()
    for cat, cor in COLOR_MAP.items():
        sub = item_stats[item_stats["categoria"] == cat]
        if len(sub) == 0:
            continue
        fig_blur.add_trace(go.Scatter(
            x=sub["vendas"], y=sub["margem"] * 100,
            mode="markers+text",
            marker=dict(size=sub["receita"] / sub["receita"].max() * 40 + 12, color=cor, opacity=0.85),
            text=sub["Nome do Item"],
            textposition="top center",
            textfont=dict(size=9, color="#c0c0d8"),
        ))
    fig_blur.update_layout(
        height=340,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0d0d18",
        xaxis=dict(color="#70708a"), yaxis=dict(color="#70708a"),
        showlegend=False,
        font=dict(family="DM Sans"),
    )
    st.plotly_chart(fig_blur, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    render_lock_card(
        titulo="Engenharia de Cardápio Completa",
        itens_bloqueados=[
            "Margem estimada real por item",
            "Matriz Estrela / Potencial / Cavalo / Problema",
            "Estimativa de vazamento de lucro mensal",
            "Plano de ação item a item (ajustar preço, criar combo, remover)",
        ],
    )

else:
    # ── PREMIUM: Matriz interativa ────────────────────────────────────────
    st.markdown('<div class="section-header">🎯 Matriz de Engenharia de Cardápio</div>', unsafe_allow_html=True)

    COLOR_MAP = {
        "⭐ Estrela":           "#34d399",
        "💎 Potencial":         "#a78bfa",
        "🐴 Cavalo de Batalha": "#f59e0b",
        "❌ Problema":          "#f87171",
    }

    fig_matrix = go.Figure()
    for cat, cor in COLOR_MAP.items():
        sub = item_stats[item_stats["categoria"] == cat]
        if len(sub) == 0:
            continue
        fig_matrix.add_trace(go.Scatter(
            x=sub["vendas"],
            y=sub["margem"] * 100,
            mode="markers+text",
            name=cat,
            marker=dict(
                size=sub["receita"] / item_stats["receita"].max() * 42 + 14,
                color=cor,
                opacity=0.85,
                line=dict(width=1, color="rgba(0,0,0,0.3)"),
            ),
            text=sub["Nome do Item"],
            textposition="top center",
            textfont=dict(size=10, color="#c0c0d8"),
            customdata=sub[["receita","rec_liq","margem"]].values,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Vendas: %{x}<br>"
                "Margem Bruta: %{y:.1f}%<br>"
                "Receita: R$ %{customdata[0]:,.0f}<br>"
                "Rec. Líquida: R$ %{customdata[1]:,.0f}<extra></extra>"
            ),
        ))

    # Linhas de mediana
    fig_matrix.add_vline(x=med_v, line_dash="dot", line_color="#2a2a4a", line_width=1.5)
    fig_matrix.add_hline(y=med_m * 100, line_dash="dot", line_color="#2a2a4a", line_width=1.5)

    # Labels de quadrante
    x_max = item_stats["vendas"].max()
    y_max = item_stats["margem"].max() * 100
    y_min = item_stats["margem"].min() * 100

    for txt, x_pos, y_pos, cor in [
        ("⭐ ESTRELAS",  x_max * 0.88, y_max * 0.97, "#34d399"),
        ("💎 POTENCIAL", x_max * 0.05, y_max * 0.97, "#a78bfa"),
        ("🐴 CAVALOS",   x_max * 0.88, y_min * 1.10, "#f59e0b"),
        ("❌ PROBLEMA",  x_max * 0.05, y_min * 1.10, "#f87171"),
    ]:
        fig_matrix.add_annotation(
            x=x_pos, y=y_pos, text=txt,
            font=dict(color=cor, size=11, family="Syne"),
            showarrow=False,
        )

    fig_matrix.update_layout(
        height=460,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0d0d18",
        xaxis=dict(title="Volume de Vendas (pedidos)", showgrid=True,
                   gridcolor="#1a1a28", color="#70708a"),
        yaxis=dict(title="Margem Bruta (%)", showgrid=True,
                   gridcolor="#1a1a28", color="#70708a"),
        legend=dict(bgcolor="rgba(17,17,24,0.9)", bordercolor="#2a2a4a",
                    borderwidth=1, font=dict(color="#9090a8", size=11)),
        font=dict(family="DM Sans"),
        hovermode="closest",
    )
    st.plotly_chart(fig_matrix, use_container_width=True)

    st.markdown("""
    <div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:-8px;margin-bottom:8px;">
      <span style="font-size:12px;color:#505068;">⭐ <span style="color:#34d399;">Estrelas</span>: alto volume + boa margem — promova mais</span>
      <span style="font-size:12px;color:#505068;">💎 <span style="color:#a78bfa;">Potencial</span>: margem boa, volume baixo — divulgue</span>
      <span style="font-size:12px;color:#505068;">🐴 <span style="color:#f59e0b;">Cavalos</span>: muito pedido, margem baixa — revise preço</span>
      <span style="font-size:12px;color:#505068;">❌ <span style="color:#f87171;">Problema</span>: pouco volume e margem ruim — avalie remover</span>
    </div>
    """, unsafe_allow_html=True)

    # ── PREMIUM: Vazamento de lucro ───────────────────────────────────────
    st.markdown('<div class="section-header">🚨 Vazamento de Lucro</div>', unsafe_allow_html=True)

    itens_problema_cat = item_stats[item_stats["categoria"].isin(["🐴 Cavalo de Batalha","❌ Problema"])]
    vazamento = (itens_problema_cat["receita"] * (med_m - itens_problema_cat["margem"])).sum()
    vazamento = max(vazamento, 0)

    col_v, col_tabela = st.columns([1, 2])

    with col_v:
        st.markdown(f"""
        <div style="background:rgba(248,113,113,0.06);border:1px solid rgba(248,113,113,0.18);
          border-radius:12px;padding:24px 20px;text-align:center;">
          <div style="font-size:13px;color:#80607a;margin-bottom:8px;text-transform:uppercase;
            letter-spacing:1px;font-weight:600;">Estimativa de Lucro Não Realizado</div>
          <div style="font-family:'Syne',sans-serif;font-size:34px;font-weight:800;color:#f59e0b;">
            R$ {vazamento:,.0f}
          </div>
          <div style="font-size:12px;color:#404058;margin-top:6px;">no período analisado</div>
          <div style="margin-top:16px;padding-top:14px;border-top:1px solid rgba(248,113,113,0.12);
            font-size:13px;color:#70708a;line-height:1.6;text-align:left;">
            Dinheiro que poderia ser lucro, mas foi absorvido por custo alto
            nos itens de baixa eficiência. Ajustar preço ou custo converte
            diretamente em margem.
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_tabela:
        # ── PREMIUM: Plano de ação por item ──────────────────────────────
        def recomendar(row):
            m = row["margem"] * 100
            if row["categoria"] == "⭐ Estrela":
                return "✅ Destaque no cardápio — não mexa no preço"
            elif row["categoria"] == "💎 Potencial":
                return "📣 Nova foto + descrição no app para aumentar visibilidade"
            elif row["categoria"] == "🐴 Cavalo de Batalha":
                if m < 25:
                    return "💡 Aumentar preço 8–12% ou renegociar insumo"
                else:
                    return "💡 Criar versão premium para elevar ticket médio"
            else:
                return "🗑️ Avaliar remoção ou reformulação completa"

        item_stats["Ação"] = item_stats.apply(recomendar, axis=1)

        tabela = item_stats[["Nome do Item","categoria","vendas","margem","receita","Ação"]].copy()
        tabela = tabela.sort_values("receita", ascending=False)
        tabela["margem"]  = tabela["margem"].apply(lambda x: f"{x*100:.0f}%")
        tabela["receita"] = tabela["receita"].apply(lambda x: f"R$ {x:,.0f}".replace(",","."))
        tabela.columns    = ["Item","Quadrante","Vendas","Margem","Receita","Ação Recomendada"]

        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Item":            st.column_config.TextColumn(width="medium"),
                "Quadrante":       st.column_config.TextColumn(width="medium"),
                "Vendas":          st.column_config.NumberColumn(width="small"),
                "Margem":          st.column_config.TextColumn(width="small"),
                "Receita":         st.column_config.TextColumn(width="medium"),
                "Ação Recomendada":st.column_config.TextColumn(width="large"),
            },
        )

    # Ajuste manual do master (só aparece se is_master e tiver texto)
    ajuste = st.session_state.get("ajuste_manual", "")
    if ajuste and acesso.get("is_master"):
        st.markdown(f"""
        <div class="insight purple" style="margin-top:16px;">
          <div class="insight-title">🔎 Observações do Especialista</div>
          <div class="insight-text">{ajuste}</div>
        </div>
        """, unsafe_allow_html=True)
