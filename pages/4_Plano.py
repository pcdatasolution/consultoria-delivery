"""
Módulo Plano de Crescimento — Exclusivo Premium
Resumo executivo com problemas rankeados por impacto + plano de ação automático
"""

import streamlit as st
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (
    generate_mock_ifood_data, process_ifood_data, get_kpis,
    detectar_modo, inject_css, render_sidebar, render_lock_card,
    gerar_plano_automatico, calcular_choque, CONFIANCA
)

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Plano de Crescimento | DeliveryPro",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
render_sidebar(active="plano")
acesso = detectar_modo()
modo   = acesso["modo"]

# ── Dados ─────────────────────────────────────────────────────────────────────
if "df_main" not in st.session_state:
    st.session_state["df_main"] = process_ifood_data(generate_mock_ifood_data(800))

df = st.session_state["df_main"]

# ─────────────────────────────────────────────────────────────────────────────
#  BLOQUEIO TOTAL PARA MODO DEMO
# ─────────────────────────────────────────────────────────────────────────────
if modo == "demo":
    st.markdown("""
    <div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;
      color:#2f5f98;line-height:1.2;margin-bottom:6px;">
      🧠 Plano de Crescimento
    </div>
    <div style="color:#2f5f98;font-size:14px;margin-bottom:32px;">
      Resumo executivo com os problemas rankeados por impacto financeiro e o plano de ação priorizado.
    </div>
    """, unsafe_allow_html=True)

    # Preview do que existe, completamente borrado
    st.markdown('<div style="opacity:0.12;filter:blur(5px);pointer-events:none;user-select:none;">', unsafe_allow_html=True)

    # Gera o plano real mas só mostra borrado
    plano = gerar_plano_automatico(df)
    choque = calcular_choque(df)

    for i, p in enumerate(plano["problemas"][:3]):
        st.markdown(f"""
        <div class="plano-card">
          <div class="plano-cat">{p['categoria']} · Problema #{i+1}</div>
          <div class="plano-title">{p['titulo']}</div>
          <div class="plano-desc">{p['descricao']}</div>
          <div class="plano-impacto">💸 Impacto estimado: R$ {p['impacto_r']:,.0f}</div>
          {''.join(f'<div class="plano-acao">→ {a}</div>' for a in p['acoes'])}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Lock card por cima
    render_lock_card(
        titulo="Plano de Crescimento Completo",
        itens_bloqueados=[
            "Resumo executivo com impacto total em R$/mês",
            "Problemas rankeados por prioridade e impacto financeiro",
            "Plano de ação item a item com próximos passos claros",
            "Observações personalizadas do consultor",
        ],
    )
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
#  MODO PREMIUM — conteúdo completo
# ─────────────────────────────────────────────────────────────────────────────
kpis   = get_kpis(df)
choque = calcular_choque(df)
plano  = gerar_plano_automatico(df)
nome_cliente = acesso.get("cliente", "")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="tag-premium">Premium</div>
<div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;
  color:#2f5f98;line-height:1.2;margin-bottom:6px;">
  🧠 Plano de Crescimento
  {f'<span style="font-size:16px;font-weight:400;color:#50507a;"> — {nome_cliente}</span>' if nome_cliente and nome_cliente != "Master" else ""}
</div>
<div style="color:#2f5f98;font-size:14px;margin-bottom:28px;">
  Diagnóstico financeiro completo com ações priorizadas por impacto.
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  RESUMO EXECUTIVO — impacto total
# ─────────────────────────────────────────────────────────────────────────────
low_fmt  = f"R$ {plano['impacto_mensal_low']:,.0f}".replace(",",".")
high_fmt = f"R$ {plano['impacto_mensal_high']:,.0f}".replace(",",".")
n_prob   = plano["n_problemas"]

st.markdown(f"""
<div style="
  background: linear-gradient(135deg, #100a20, #0a1810);
  border: 1px solid #221840;
  border-radius: 16px;
  padding: 36px 40px;
  margin-bottom: 28px;
  position: relative;
  overflow: hidden;
">
  <div style="position:absolute;top:-40%;right:-5%;width:40%;height:180%;
    background:radial-gradient(ellipse,rgba(245,158,11,.06) 0%,transparent 70%);
    pointer-events:none;"></div>

  <div style="font-family:'Syne',sans-serif;font-size:13px;font-weight:600;
    color:#FFFFFF;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:16px;">
    📋 Resumo Executivo
  </div>

  <div style="display:flex;gap:48px;flex-wrap:wrap;align-items:flex-end;">
    <div>
      <div style="font-size:13px;color:#FFFFFF;margin-bottom:4px;">Potencial de ganho mensal</div>
      <div style="font-family:'Syne',sans-serif;font-size:38px;font-weight:800;color:#f59e0b;line-height:1;">
        {low_fmt} – {high_fmt}
      </div>
      <div style="font-size:12px;color:#FFFFFF;margin-top:6px;">
        * Estimativa baseada nos dados reais com metodologia de proxy financeiro
      </div>
    </div>
    <div style="display:flex;gap:32px;flex-wrap:wrap;">
      <div>
        <div style="font-size:12px;color:#FFFFFF;margin-bottom:18px;">Problemas identificados</div>
        <div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:700;color:#e2e2f0;">{n_prob}</div>
      </div>
      <div>
        <div style="font-size:12px;color:#FFFFFF;margin-bottom:18px;">Faturamento no período</div>
        <div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:700;color:#e2e2f0;">
          R$ {kpis['faturamento']:,.0f}
        </div>
      </div>
      <div>
        <div style="font-size:12px;color:#FFFFFF;margin-bottom:18px;">Margem líquida atual</div>
        <div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:700;
          color:{'#34d399' if kpis['receita_liquida']/kpis['faturamento']*100 > 70 else '#f59e0b'};">
          {kpis['receita_liquida']/kpis['faturamento']*100:.1f}%
        </div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  GRÁFICO — impacto por problema
# ─────────────────────────────────────────────────────────────────────────────
if plano["problemas"]:
    st.markdown('<div class="section-header">📊 Impacto Estimado por Problema</div>', unsafe_allow_html=True)

    titulos  = [p["titulo"][:55] + "…" if len(p["titulo"]) > 55 else p["titulo"]
                for p in plano["problemas"]]
    impactos = [p["impacto_r"] for p in plano["problemas"]]
    cores    = ["#f87171" if p["prioridade"] == 1 else "#f59e0b"
                for p in plano["problemas"]]

    fig_imp = go.Figure(go.Bar(
        y=titulos[::-1],
        x=impactos[::-1],
        orientation="h",
        marker=dict(color=cores[::-1], opacity=0.85),
        text=[f"R$ {v:,.0f}".replace(",",".") for v in impactos[::-1]],
        textposition="outside",
        hovertemplate="%{y}<br>Impacto: R$ %{x:,.0f}<extra></extra>",
    ))
    fig_imp.update_layout(
        height=max(200, len(titulos) * 60),
        margin=dict(l=0, r=120, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#1a1a28", color="#50507a",
                   tickprefix="R$ ", tickformat=",.0f"),
        yaxis=dict(showgrid=False, color="#9090a8"),
        font=dict(family="DM Sans", color="#9090a8"),
    )
    st.plotly_chart(fig_imp, use_container_width=True)

    st.markdown("""
    <div style="font-size:11px;color:#30303e;margin-top:-8px;margin-bottom:8px;">
      🔴 Alta prioridade &nbsp;·&nbsp; 🟡 Média prioridade
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  PLANO DE AÇÃO — cards por problema
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🛠️ Plano de Ação Priorizado</div>', unsafe_allow_html=True)

for i, prob in enumerate(plano["problemas"]):
    prioridade_cor   = "#f87171" if prob["prioridade"] == 1 else "#f59e0b"
    prioridade_label = "Alta prioridade" if prob["prioridade"] == 1 else "Média prioridade"

    # Badge de confiança
    conf     = CONFIANCA.get(prob.get("confianca", "media"))
    conf_html = f"""
    <span style="background:{conf['bg']};border:1px solid {conf['borda']};
      color:{conf['cor']};font-size:11px;font-weight:600;
      padding:3px 8px;border-radius:4px;margin-left:8px;">
      {conf['badge']}
    </span>"""

    # Raciocínio (o "de onde veio esse número")
    raciocinio = prob.get("raciocinio", "")
    raciocinio_html = f"""
    <div style="background:rgba(255,255,255,0.03);border:1px solid #1c1c2e;
      border-radius:6px;padding:10px 14px;margin:10px 0 12px;
      font-size:12px;color:#606078;line-height:1.6;">
      <span style="color:#404058;font-weight:600;font-size:11px;
        text-transform:uppercase;letter-spacing:0.8px;">Como calculamos → </span>
      {raciocinio}
    </div>""" if raciocinio else ""

    acoes_html = "".join(
        f'<div class="plano-acao" style="margin-top:6px;padding-top:6px;">→ {a}</div>'
        for a in prob["acoes"]
    )

    st.markdown(f"""
    <div class="plano-card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
          <div class="plano-cat" style="margin-bottom:0;">{prob['categoria']}</div>
          {conf_html}
        </div>
        <div style="font-size:11px;font-weight:600;color:{prioridade_cor};
          background:rgba(255,255,255,0.04);padding:3px 8px;border-radius:4px;
          border:1px solid {prioridade_cor}33;white-space:nowrap;">
          #{i+1} · {prioridade_label}
        </div>
      </div>
      <div class="plano-title">{prob['titulo']}</div>
      <div class="plano-desc">{prob['descricao']}</div>
      {raciocinio_html}
      <div class="plano-impacto">
        💸 Impacto estimado: R$ {prob['impacto_r']:,.0f}
      </div>
      {acoes_html}
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  OBSERVAÇÕES PERSONALIZADAS DO ESPECIALISTA
# ─────────────────────────────────────────────────────────────────────────────
ajuste = st.session_state.get("ajuste_manual", "")

if ajuste:
    st.markdown('<div class="section-header">🔎 Observações do Especialista</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="insight purple">
      <div class="insight-title">Análise personalizada para {nome_cliente or "este negócio"}</div>
      <div class="insight-text">{ajuste}</div>
    </div>
    """, unsafe_allow_html=True)

elif acesso.get("is_master"):
    st.markdown('<div class="section-header">🔎 Observações do Especialista</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="insight yellow">
      <div class="insight-title">✏️ Nenhuma observação adicionada ainda</div>
      <div class="insight-text">
        Use o campo <strong>"Observações personalizadas"</strong> na barra lateral
        para adicionar contexto específico deste cliente antes de enviar o link.
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  PRÓXIMOS PASSOS — CTA final
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🚀 Próximos Passos</div>', unsafe_allow_html=True)

st.markdown("""
<div style="
  background:#0f0f1e;border:1px solid #1c1c2e;
  border-radius:12px;padding:28px 28px;
">
  <div style="font-family:'Syne',sans-serif;font-size:16px;font-weight:700;
    color:#e2e2f0;margin-bottom:16px;">
    Como tirar esse plano do papel:
  </div>

  <div style="display:flex;flex-direction:column;gap:12px;">
    <div style="display:flex;gap:14px;align-items:flex-start;">
      <div style="background:rgba(167,139,250,0.15);border:1px solid rgba(167,139,250,0.3);
        border-radius:6px;padding:4px 10px;font-family:'Syne',sans-serif;
        font-size:13px;font-weight:700;color:#a78bfa;flex-shrink:0;">1</div>
      <div style="font-size:14px;color:#9090a8;line-height:1.5;">
        <strong style="color:#e2e2f0;">Comece pelo problema de maior impacto.</strong>
        Não tente resolver tudo de uma vez. Um ajuste bem feito já muda o resultado do mês.
      </div>
    </div>
    <div style="display:flex;gap:14px;align-items:flex-start;">
      <div style="background:rgba(167,139,250,0.15);border:1px solid rgba(167,139,250,0.3);
        border-radius:6px;padding:4px 10px;font-family:'Syne',sans-serif;
        font-size:13px;font-weight:700;color:#a78bfa;flex-shrink:0;">2</div>
      <div style="font-size:14px;color:#9090a8;line-height:1.5;">
        <strong style="color:#e2e2f0;">Execute uma ação por semana.</strong>
        Ajuste o preço de um item, crie um combo, ou dispare uma campanha para inativos.
        Pequenas ações consistentes acumulam resultado.
      </div>
    </div>
    <div style="display:flex;gap:14px;align-items:flex-start;">
      <div style="background:rgba(167,139,250,0.15);border:1px solid rgba(167,139,250,0.3);
        border-radius:6px;padding:4px 10px;font-family:'Syne',sans-serif;
        font-size:13px;font-weight:700;color:#a78bfa;flex-shrink:0;">3</div>
      <div style="font-size:14px;color:#9090a8;line-height:1.5;">
        <strong style="color:#e2e2f0;">Monitore o resultado em 30 dias.</strong>
        Suba o próximo relatório do iFood aqui para ver se os números melhoraram
        e qual é o próximo problema a atacar.
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# Rodapé
st.markdown("""
<div style="text-align:center;padding:32px 0 8px;color:#252535;font-size:12px;">
  DeliveryPro Hub · Consultoria de Dados para Restaurantes
</div>
""", unsafe_allow_html=True)