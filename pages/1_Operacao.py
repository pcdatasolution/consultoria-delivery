"""
Módulo Operação — Demo parcial / Premium completo
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (
    generate_mock_ifood_data, process_ifood_data, get_kpis,
    detectar_modo, inject_css, render_sidebar,
)

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Operação | DeliveryPro",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
render_sidebar(active="operacao")
acesso = detectar_modo()

# ── Dados ─────────────────────────────────────────────────────────────────────
if "df_main" not in st.session_state:
    st.session_state["df_main"] = process_ifood_data(generate_mock_ifood_data(800))

df    = st.session_state["df_main"]
df_ok = df[~df["is_cancelado"]].copy()
kpis  = get_kpis(df)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;
  color:#2f5f98;line-height:1.2;margin-bottom:6px;">
  🚚 Operação & Logística
</div>
<div style="color:#2f5f98;font-size:14px;margin-bottom:28px;">
  Diagnóstico completo — tempo por bairro, cancelamentos e horários críticos.
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SEÇÃO 1 — KPIs gerais (visível nos dois modos)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Números Gerais</div>', unsafe_allow_html=True)

tempo_medio  = df_ok["Tempo de Entrega (min)"].mean()
tx_cancel    = kpis["taxa_cancelamento"]
perda_cancel = kpis["perda_cancelamentos"]
total_pedidos = kpis["total_pedidos"]

df_ok_periodo = df[~df["is_cancelado"]]
dias_periodo  = (df_ok_periodo["Data do Pedido"].max() - df_ok_periodo["Data do Pedido"].min()).days + 1
semanas_periodo = dias_periodo / 7

pedidos_por_dia     = total_pedidos / dias_periodo if dias_periodo else 0
pedidos_por_semana  = total_pedidos / semanas_periodo if semanas_periodo else 0
perda_por_dia       = perda_cancel / dias_periodo if dias_periodo else 0

cancelados_por_semana = len(df[df["is_cancelado"]]) / semanas_periodo if semanas_periodo else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Pedidos Concluídos",
    f"{pedidos_por_semana:.0f}/sem",
    delta=f"Total no período: {total_pedidos:,}".replace(",", "."), delta_color="off")
c2.metric("Tempo Médio de Entrega", f"{tempo_medio:.0f} min",
    delta="⚠️ Acima de 45 min" if tempo_medio > 45 else "✅ Dentro da meta",
    delta_color="inverse" if tempo_medio > 45 else "normal")
c3.metric("Taxa de Cancelamento", f"{tx_cancel:.1f}%",
    delta=f"{cancelados_por_semana:.0f} cancelados/sem", delta_color="off")
c4.metric("Perda em Cancelamentos",
    f"R$ {perda_cancel / semanas_periodo:,.0f}".replace(",", ".")+"/sem",
    delta=f"Total no período: R$ {perda_cancel:,.0f}".replace(",", "."), delta_color="off")

# ─────────────────────────────────────────────────────────────────────────────
#  SEÇÃO 2 — Cancelamentos por dia da semana (visível nos dois modos)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📅 Cancelamentos por Dia da Semana</div>', unsafe_allow_html=True)

order_days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
label_days = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]

dia_stats = (
    df.groupby("Dia Semana")["is_cancelado"]
    .agg(total="count", cancelados="sum")
    .reindex(order_days)
    .reset_index()
)
dia_stats["entregues"] = dia_stats["total"] - dia_stats["cancelados"]
dia_stats["Label"]     = label_days
dia_stats["pct_label"] = (dia_stats["cancelados"] / dia_stats["total"] * 100).round(1)

fig_dias = go.Figure()
fig_dias.add_trace(go.Bar(
    name="Entregues",
    x=dia_stats["Label"],
    y=dia_stats["entregues"],
    marker_color="#005737",
    text=dia_stats["entregues"],
    textposition="inside",
    hovertemplate="%{x}<br>Entregues: %{y}<extra></extra>",
))
fig_dias.add_trace(go.Bar(
    name="Cancelados",
    x=dia_stats["Label"],
    y=dia_stats["cancelados"],
    marker_color="#940000",
    text=dia_stats["pct_label"].apply(lambda x: f"{x:.1f}%"),
    textposition="inside",
    hovertemplate="%{x}<br>Cancelados: %{y} (%{text})<extra></extra>",
))
# Anotações com total acima de cada barra
for _, row in dia_stats.iterrows():
    fig_dias.add_annotation(
        x=row["Label"], y=row["total"],
        text=str(int(row["total"])),
        showarrow=False,
        yshift=10,
        font=dict(size=11, color="#9090a8"),
    )
fig_dias.update_layout(
    barmode="stack",
    height=280,
    margin=dict(l=0, r=0, t=10, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False, color="#9090a8"),
    yaxis=dict(showgrid=True, gridcolor="#1a1a28", color="#50507a", title="Pedidos"),
    font=dict(family="DM Sans", color="#9090a8"),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02,
        xanchor="right", x=1, font=dict(size=11),
    ),
)

col_g, col_insight = st.columns([2, 1])

with col_g:
    st.plotly_chart(fig_dias, use_container_width=True)

with col_insight:
    pior = dia_stats.loc[dia_stats["pct_label"].idxmax()]
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="insight yellow">
      <div class="insight-title">⚠️ Dia mais crítico: {pior['Label']}</div>
      <div class="insight-text">
        {pior['pct_label']:.1f}% de cancelamentos — o pior da semana.
        Pode indicar sobrecarga operacional ou problema de estoque nesse dia.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Insight teaser específico para demo
    melhor = dia_stats.loc[dia_stats["pct_label"].idxmin()]
    st.markdown(f"""
    <div class="insight green">
      <div class="insight-title">✅ Melhor dia: {melhor['Label']}</div>
      <div class="insight-text">
        Apenas {melhor['pct_label']:.1f}% de cancelamentos.
        Entenda o que funciona aqui e replique nos dias críticos.
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SEÇÃO 3 — |  PREMIUM: conteúdo completo
# ─────────────────────────────────────────────────────────────────────────────

# ── Tempo por bairro ──────────────────────────────────────────────────
st.markdown('<div class="section-header">📍 Tempo Médio de Entrega por Bairro</div>', unsafe_allow_html=True)

# Filtro de bairro na própria página
bairros_disp = sorted(df_ok["Bairro"].dropna().unique().tolist())
bairros_sel  = st.multiselect("Filtrar bairros", bairros_disp, default=bairros_disp, key="op_bairros")
df_filt = df_ok[df_ok["Bairro"].isin(bairros_sel)] if bairros_sel else df_ok

tempo_bairro = (
    df_filt.groupby("Bairro")["Tempo de Entrega (min)"]
    .agg(["mean", "count"])
    .reset_index()
    .rename(columns={"mean": "Tempo Médio (min)", "count": "Pedidos"})
    .sort_values("Tempo Médio (min)", ascending=True)
)

fig_tempo = go.Figure(go.Bar(
    y=tempo_bairro["Bairro"],
    x=tempo_bairro["Tempo Médio (min)"],
    orientation="h",
    marker=dict(
        color=tempo_bairro["Tempo Médio (min)"],
        colorscale=[[0,"#34d399"],[0.5,"#f59e0b"],[1,"#f87171"]],
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
    xaxis=dict(showgrid=True, gridcolor="#1a1a28", color="#50507a", title="minutos"),
    yaxis=dict(showgrid=False, color="#9090a8"),
    font=dict(family="DM Sans", color="#9090a8"),
)
st.plotly_chart(fig_tempo, use_container_width=True)

# Insights automáticos
bairro_lento  = tempo_bairro.iloc[-1]
bairro_rapido = tempo_bairro.iloc[0]

col_i1, col_i2 = st.columns(2)
with col_i1:
    st.markdown(f"""
    <div class="insight red">
        <div class="insight-title">⚠️ Atenção: {bairro_lento['Bairro']}</div>
        <div class="insight-text">
        Tempo médio de <strong>{bairro_lento['Tempo Médio (min)']:.0f} min</strong> — acima da meta de 45 min.
        Avalie reduzir o raio de entrega ou reforçar a equipe nessa região.
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_i2:
    st.markdown(f"""
    <div class="insight green">
        <div class="insight-title">✅ Melhor performance: {bairro_rapido['Bairro']}</div>
        <div class="insight-text">
        Tempo médio de <strong>{bairro_rapido['Tempo Médio (min)']:.0f} min</strong>.
        Entenda o que funciona aqui e replique na operação dos bairros lentos.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── PREMIUM — Mapa de cancelamentos ──────────────────────────────────
st.markdown('<div class="section-header">🗺️ Mapa de Cancelamentos por Região</div>', unsafe_allow_html=True)

cancel_bairro = (
    df.groupby("Bairro")
    .apply(lambda x: pd.Series({
        "Taxa Cancelamento (%)": x["is_cancelado"].mean() * 100,
        "Total Pedidos":         len(x),
        "Cancelamentos":         x["is_cancelado"].sum(),
        "lat":                   x["lat"].mean(),
        "lon":                   x["lon"].mean(),
    }))
    .reset_index()
)

print(cancel_bairro[["Bairro", "lat", "lon", "Total Pedidos", "Taxa Cancelamento (%)"]].to_string())

fig_map = px.scatter_mapbox(
    cancel_bairro,
    lat="lat", lon="lon",
    size="Total Pedidos",
    color="Taxa Cancelamento (%)",
    color_continuous_scale=["#34d399","#f59e0b","#f87171"],
    size_max=40,
    hover_name="Bairro",
    hover_data={
        "Taxa Cancelamento (%)": ":.1f",
        "Total Pedidos": True,
        "Cancelamentos": True,
        "lat": False, "lon": False,
    },
    mapbox_style="carto-positron",
    zoom=11,
    center={"lat": -23.028971, "lon": -45.560095},
)



fig_map.update_layout(
    height=400,
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    coloraxis_colorbar=dict(
        title=dict(
            text="% Cancel.",
            font=dict(color="#9090a8"),
        ),
        tickfont=dict(color="#9090a8"),
    ),
)
st.plotly_chart(fig_map, use_container_width=True)

# ── PREMIUM — Horários críticos ───────────────────────────────────────
st.markdown('<div class="section-header">🕐 Cancelamentos por Horário</div>', unsafe_allow_html=True)

cancel_hora = (
    df.groupby("Hora")["is_cancelado"]
    .agg(["mean","count"])
    .reset_index()
    .rename(columns={"mean":"Taxa","count":"Pedidos"})
)
cancel_hora["pct_label"] = (cancel_hora["Taxa"] * 100).round(1)

fig_hora = go.Figure(go.Bar(
    x=cancel_hora["Hora"],
    y=cancel_hora["pct_label"],
    marker=dict(
        color=cancel_hora["pct_label"],
        colorscale=[[0,"#34d399"],[0.5,"#f59e0b"],[1,"#f87171"]],
    ),
    text=cancel_hora["pct_label"].apply(lambda x: f"{x:.0f}%"),
    textposition="outside",
    customdata=cancel_hora["Pedidos"],
    hovertemplate="Hora %{x}h<br>Cancelamento: %{y:.1f}%<br>Pedidos: %{customdata}<extra></extra>",
))
fig_hora.update_layout(
    height=250,
    margin=dict(l=0, r=0, t=10, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False, color="#9090a8", title="hora do dia",
                tickmode="linear", dtick=2),
    yaxis=dict(showgrid=True, gridcolor="#1a1a28", color="#50507a", ticksuffix="%"),
    font=dict(family="DM Sans", color="#9090a8"),
)
st.plotly_chart(fig_hora, use_container_width=True)

hora_pico = cancel_hora.loc[cancel_hora["pct_label"].idxmax()]
st.markdown(f"""
<div class="insight yellow">
    <div class="insight-title">⚠️ Horário crítico: {hora_pico['Hora']:.0f}h</div>
    <div class="insight-text">
    Pico de cancelamentos às <strong>{hora_pico['Hora']:.0f}h</strong>
    com {hora_pico['pct_label']:.1f}% — maior taxa do dia.
    Reforce equipe ou reduza o raio de entrega nesse período.
    </div>
</div>
""", unsafe_allow_html=True)
