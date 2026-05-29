"""
DeliveryPro — Experimentos
Acompanhamento de experimentos baseados no Plano de Crescimento
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (
    generate_mock_ifood_data, process_ifood_data,
    gerar_plano_automatico, detectar_modo, inject_css, render_sidebar,
    salvar_experimento_sheets, encerrar_experimento_sheets,
    carregar_experimento_ativo_sheets,
)

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Experimentos | DeliveryPro",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
render_sidebar(active="experimentos")
acesso = detectar_modo()
sheets_id = acesso.get("sheets_id")

if "experimento_ativo" not in st.session_state and sheets_id:
    exp_recuperado = carregar_experimento_ativo_sheets(sheets_id)
    if exp_recuperado:
        st.session_state["experimento_ativo"] = exp_recuperado

# ── Dados ─────────────────────────────────────────────────────────────────────
if sheets_id and st.session_state.get("sheets_id_carregado") != sheets_id:
    from utils import carregar_pedidos_sheets, carregar_dados_cliente
    df_raw = carregar_pedidos_sheets(sheets_id)
    dados  = carregar_dados_cliente(sheets_id)
    st.session_state["df_main"]  = df_raw if df_raw is not None else process_ifood_data(generate_mock_ifood_data(800))
    st.session_state["config"]   = dados.get("config", {})
    st.session_state["cardapio"] = dados.get("cardapio", {})
    st.session_state["sheets_id_carregado"] = sheets_id
elif not sheets_id and "df_main" not in st.session_state:
    st.session_state["df_main"]  = process_ifood_data(generate_mock_ifood_data(800))
    st.session_state["config"]   = {}
    st.session_state["cardapio"] = {}

df       = st.session_state["df_main"]
config   = st.session_state.get("config", {})
cardapio = st.session_state.get("cardapio", {})
plano    = gerar_plano_automatico(df, config=config, cardapio=cardapio)
metricas = plano["metricas"]

# ── Helpers ───────────────────────────────────────────────────────────────────
CUPOM_PADRAO = 12.50

MAPEAMENTO_ACAO = {
    "💰 Lucratividade": "reajuste_preco",
    "📦 Produto":        "destaque_item",
    "🚚 Operação":       "ajuste_operacional",
    "❤️ Fidelização":    "campanha_reativacao",
    "🎫 Ticket Médio":   "criacao_combo",
}

METRICAS_POR_ACAO = {
    "reajuste_preco": {
        "primaria":   ("Margem de Contribuição do Item", "cancelamento"),
        "guardrails": [
            ("Volume de vendas do item",  "produtos"),
            ("Ticket médio geral",        "ticket_medio"),
            ("Taxa de cancelamento",      "cancelamento"),
        ],
    },
    "destaque_item": {
        "primaria":   ("Volume de Vendas do Item", "produtos"),
        "guardrails": [
            ("Ticket médio geral",        "ticket_medio"),
            ("Taxa de cancelamento",      "cancelamento"),
        ],
    },
    "ajuste_operacional": {
        "primaria":   ("Taxa de Cancelamento", "cancelamento"),
        "guardrails": [
            ("Tempo médio de entrega",    "tempo_entrega"),
            ("Ticket médio geral",        "ticket_medio"),
        ],
    },
    "campanha_reativacao": {
        "primaria":   ("Clientes Ativos %", "clientes_ativos_pct"),
        "guardrails": [
            ("Intervalo entre compras",   "intervalo_compras"),
            ("Ticket médio geral",        "ticket_medio"),
        ],
    },
    "criacao_combo": {
        "primaria":   ("Ticket Médio Geral", "ticket_medio"),
        "guardrails": [
            ("Taxa de cancelamento",      "cancelamento"),
            ("Clientes ativos %",         "clientes_ativos_pct"),
        ],
    },
}

def fmt_metrica(chave: str, dados: dict) -> tuple[str, str]:
    """Retorna (valor_atual_fmt, valor_alvo_fmt) para exibição."""
    if not dados or dados.get("atual") is None:
        return "—", "—"

    if chave == "ticket_medio":
        atual = f"R$ {dados['atual']:.2f}"
        alvo  = f"R$ {dados['pico']:.2f}" if dados.get("pico") else "—"
    elif chave == "cancelamento":
        atual = f"{dados['atual']:.1f}%"
        alvo  = f"{dados['meta']:.1f}%" if dados.get("meta") else "—"
    elif chave == "tempo_entrega":
        atual = f"{dados['atual']:.0f} min"
        alvo  = f"{dados['meta']:.0f} min" if dados.get("meta") else "—"
    elif chave == "intervalo_compras":
        atual = f"{dados['atual']:.0f} dias"
        alvo  = f"{dados['meta']:.0f} dias" if dados.get("meta") else "—"
    elif chave == "clientes_ativos_pct":
        atual = f"{dados['atual']:.1f}%"
        alvo  = f"{dados['pico']:.1f}%" if dados.get("pico") else "—"
    elif chave == "produtos":
        atual = "—"
        alvo  = "—"
    else:
        atual = str(dados.get("atual", "—"))
        alvo  = "—"

    return atual, alvo

def calcular_metrica_pos(chave: str, df_pos: pd.DataFrame, item: str = None) -> str:
    """Calcula a métrica atual só com pedidos após data_inicio."""
    ok = df_pos[~df_pos["is_cancelado"]]
    if len(ok) == 0:
        return "—"

    if chave == "ticket_medio":
        return f"R$ {ok['Valor Bruto'].mean():.2f}"
    elif chave == "cancelamento":
        total = len(df_pos)
        return f"{df_pos['is_cancelado'].sum() / total * 100:.1f}%" if total else "—"
    elif chave == "tempo_entrega" and "Tempo de Entrega (min)" in ok.columns:
        return f"{ok['Tempo de Entrega (min)'].mean():.0f} min"
    elif chave == "intervalo_compras":
        cli = ok.groupby("ID do Cliente").agg(
            primeiro=("Data do Pedido","min"),
            ultimo  =("Data do Pedido","max"),
            pedidos =("ID do Pedido",  "count"),
        ).reset_index()
        rec = cli[cli["pedidos"] > 1].copy()
        if len(rec) == 0:
            return "—"
        rec["intervalo"] = (rec["ultimo"] - rec["primeiro"]).dt.days / (rec["pedidos"] - 1)
        return f"{rec['intervalo'].median():.0f} dias"
    elif chave == "clientes_ativos_pct":
        dias_churn = int(config.get("churn", 30))
        hoje       = ok["Data do Pedido"].max()
        cli        = ok.groupby("ID do Cliente")["Data do Pedido"].max().reset_index()
        cli["dias"] = (hoje - cli["Data do Pedido"]).dt.days
        ativos     = (cli["dias"] <= dias_churn).sum()
        return f"{ativos / len(cli) * 100:.1f}%"
    elif chave == "produtos" and item:
        vol = ok[ok["Nome do Item"] == item].shape[0]
        return f"{vol} pedidos"
    return "—"

# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;
  color:#2f5f98;line-height:1.2;margin-bottom:6px;">
  ⚗️ Experimentos
</div>
<div style="color:#2f5f98;font-size:14px;margin-bottom:28px;">
  Teste uma ação do seu Plano de Crescimento e acompanhe o impacto em tempo real.
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  EXPERIMENTO ATIVO (lido do session_state / Sheets)
# ─────────────────────────────────────────────────────────────────────────────
exp_ativo = st.session_state.get("experimento_ativo", None)

# ─────────────────────────────────────────────────────────────────────────────
#  DESENHO DO EXPERIMENTO
# ─────────────────────────────────────────────────────────────────────────────
if exp_ativo is None:
    st.markdown('<div class="section-header">🧪 Desenho do Experimento</div>', unsafe_allow_html=True)

    # Lista suspensa com problemas do Plano
    opcoes = {
        f"#{i+1} · {p['titulo']} — R$ {p['impacto_r']:,.0f}": p
        for i, p in enumerate(plano["problemas"])
    }

    escolha = st.selectbox(
        "Selecione a ação do Plano que deseja testar:",
        options=["— Selecione —"] + list(opcoes.keys()),
        key="select_acao",
    )

    if escolha != "— Selecione —":
        prob     = opcoes[escolha]
        categoria = prob["categoria"]
        tipo_acao = MAPEAMENTO_ACAO.get(categoria, "ajuste_operacional")
        config_metricas = METRICAS_POR_ACAO[tipo_acao]

        label_primaria, chave_primaria = config_metricas["primaria"]
        dados_primaria = metricas.get(chave_primaria, {})

        # Se métrica primária é produto, pede qual item
        item_selecionado = None
        if chave_primaria == "produtos":
            itens_disponiveis = list(metricas.get("produtos", {}).keys())
            if itens_disponiveis:
                item_selecionado = st.selectbox(
                    "Qual item você vai trabalhar nesse experimento?",
                    options=itens_disponiveis,
                    key="select_item",
                )
                dados_primaria = metricas["produtos"].get(item_selecionado, {})

        atual_fmt, alvo_fmt = fmt_metrica(chave_primaria, dados_primaria)

        # Potencial de ganho
        impacto = prob["impacto_r"]
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#100a20,#0a1810);
          border:1px solid #221840;border-radius:16px;padding:28px 32px;margin:16px 0;">
          <div style="font-size:11px;color:#a78bfa;font-weight:600;
            text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
            💸 Potencial de Ganho
          </div>
          <div style="font-family:'Syne',sans-serif;font-size:36px;
            font-weight:800;color:#f59e0b;">
            R$ {impacto:,.0f}
          </div>
          <div style="font-size:12px;color:#606078;margin-top:8px;line-height:1.6;">
            {prob['raciocinio']}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Painel de métricas
        st.markdown('<div class="section-header">📊 Painel de Controle</div>', unsafe_allow_html=True)

        # Métrica primária
        st.markdown(f"""
        <div style="font-size:11px;color:#a78bfa;font-weight:600;
          text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
          Métrica Primária — {label_primaria}
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📍 Métrica Atual", atual_fmt)
        c2.metric("🎯 Alvo", alvo_fmt)
        c3.metric("⚗️ Métrica do Experimento", "—", "Aguardando início", delta_color="off")
        c4.metric("Δ Delta", "—", "Aguardando início", delta_color="off")

        # Guardrails
        st.markdown("""
        <div style="font-size:11px;color:#9090a8;font-weight:600;
          text-transform:uppercase;letter-spacing:1px;margin:16px 0 8px;">
          🛡️ Guardrails — Métricas de Alerta
        </div>
        """, unsafe_allow_html=True)

        gcols = st.columns(len(config_metricas["guardrails"]))
        for col, (label_g, chave_g) in zip(gcols, config_metricas["guardrails"]):
            dados_g = metricas.get(chave_g, {})
            atual_g, alvo_g = fmt_metrica(chave_g, dados_g)
            col.metric(label_g, atual_g, f"Alvo: {alvo_g}", delta_color="off")

        # Ações recomendadas
        st.markdown("""
        <div style="font-size:11px;color:#9090a8;font-weight:600;
          text-transform:uppercase;letter-spacing:1px;margin:20px 0 8px;">
          📋 Ações Recomendadas
        </div>
        """, unsafe_allow_html=True)
        for acao in prob["acoes"]:
            st.markdown(f"""
            <div style="background:#0f0f1e;border:1px solid #1c1c2e;
              border-radius:8px;padding:10px 14px;margin-bottom:6px;
              font-size:13px;color:#9090a8;line-height:1.5;">
              → {acao}
            </div>
            """, unsafe_allow_html=True)

        # Botão iniciar
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if st.button("🚀 Iniciar Experimento", type="primary", use_container_width=False):
            import uuid
            novo_exp = {
                "id":             str(uuid.uuid4())[:8],
                "problema":       prob,
                "tipo_acao":      tipo_acao,
                "chave_primaria": chave_primaria,
                "label_primaria": label_primaria,
                "guardrails":     config_metricas["guardrails"],
                "item":           item_selecionado,
                "data_inicio":    pd.Timestamp.now(),
                "baseline_atual": atual_fmt,
                "baseline_alvo":  alvo_fmt,
                "impacto":        impacto,
                "raciocinio":     prob["raciocinio"],
            }
            st.session_state["experimento_ativo"] = novo_exp
            if sheets_id:
                salvar_experimento_sheets(sheets_id, novo_exp)
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  EXPERIMENTO EM ANDAMENTO
# ─────────────────────────────────────────────────────────────────────────────
else:
    exp        = exp_ativo
    data_ini   = exp["data_inicio"]
    df_pos     = df[df["Data do Pedido"] >= data_ini].copy()
    ok_pos     = df_pos[~df_pos["is_cancelado"]]

    # dias reais com dados (não relógio)
    if len(df_pos) > 0:
        dias_exp = (df_pos["Data do Pedido"].max() - df_pos["Data do Pedido"].min()).days
        dias_exp = max(dias_exp, 1)
    else:
        dias_exp = 1

    chave_p    = exp["chave_primaria"]
    item_exp   = exp.get("item")
    metrica_pos = calcular_metrica_pos(chave_p, df_pos, item_exp)

    st.markdown(f"""
    <div style="background:rgba(52,211,153,0.05);border:1px solid rgba(52,211,153,0.2);
      border-radius:12px;padding:16px 24px;margin-bottom:20px;
      display:flex;align-items:center;gap:16px;">
      <div style="font-size:28px;">🟡</div>
      <div>
        <div style="font-family:'Syne',sans-serif;font-size:15px;
          font-weight:700;color:#2f5f98;">Experimento em andamento</div>
        <div style="font-size:13px;color:#50507a;margin-top:2px;">
          Iniciado em {data_ini.strftime('%d/%m/%Y às %H:%M')} · {dias_exp} dia(s) decorrido(s)
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Calcula ganho realizado direto do df_pos ──────────────────────────
    ganho_periodo   = None
    ganho_mensal    = None
    raciocinio_real = ""

    try:
        if len(ok_pos) > 0 and dias_exp > 0:
            chave_p_calc = exp["chave_primaria"]

            # baseline numérico
            val_base = float(
                exp["baseline_atual"].replace("R$","").replace("%","")
                .replace(" min","").replace(" dias","")
                .replace(" pedidos","").replace(",",".").strip()
            )

            if chave_p_calc == "ticket_medio":
                ticket_pos  = ok_pos.groupby("ID do Pedido")["Valor Bruto"].sum()
                ticket_med  = ticket_pos.mean()
                delta_tk    = ticket_med - val_base
                if delta_tk > 0:
                    n_pedidos_pos   = len(ticket_pos)
                    ganho_periodo   = delta_tk * n_pedidos_pos
                    pedidos_mes     = n_pedidos_pos / dias_exp * 30
                    ganho_mensal    = delta_tk * pedidos_mes
                    raciocinio_real = (
                        f"Ticket subiu R$ {delta_tk:.2f} (de R$ {val_base:.2f} → R$ {ticket_med:.2f}) "
                        f"× {n_pedidos_pos} pedidos no período = R$ {ganho_periodo:.0f} acumulado. "
                        f"Projeção: R$ {ganho_mensal:.0f}/mês."
                    )

            elif chave_p_calc == "cancelamento":
                cancel_pos  = df_pos["is_cancelado"].sum() / len(df_pos) * 100
                delta_ca    = val_base - cancel_pos          # positivo = melhorou
                if delta_ca > 0:
                    ticket_med      = ok_pos.groupby("ID do Pedido")["Valor Bruto"].sum().mean()
                    pedidos_evit    = len(df_pos) * (delta_ca / 100)
                    ganho_periodo   = pedidos_evit * ticket_med
                    pedidos_mes     = len(df_pos) / dias_exp * 30
                    ganho_mensal    = pedidos_mes * (delta_ca / 100) * ticket_med
                    raciocinio_real = (
                        f"Cancelamento caiu {delta_ca:.1f}pp (de {val_base:.1f}% → {cancel_pos:.1f}%) "
                        f"× {pedidos_evit:.0f} pedidos evitados × R$ {ticket_med:.0f} ticket "
                        f"= R$ {ganho_periodo:.0f} no período. Projeção: R$ {ganho_mensal:.0f}/mês."
                    )

            elif chave_p_calc == "clientes_ativos_pct":
                dias_churn_cfg = int(config.get("churn", 30))
                hoje_pos       = ok_pos["Data do Pedido"].max()
                cli_pos        = ok_pos.groupby("ID do Cliente")["Data do Pedido"].max().reset_index()
                cli_pos["dias_sem_compra"] = (hoje_pos - cli_pos["Data do Pedido"]).dt.days
                pct_ativos_pos = (cli_pos["dias_sem_compra"] <= dias_churn_cfg).sum() / len(cli_pos) * 100
                delta_at       = pct_ativos_pos - val_base   # positivo = melhorou
                if delta_at > 0:
                    ticket_med      = ok_pos.groupby("ID do Pedido")["Valor Bruto"].sum().mean()
                    clientes_extras = len(cli_pos) * (delta_at / 100)
                    ganho_periodo   = clientes_extras * ticket_med
                    ganho_mensal    = ganho_periodo / dias_exp * 30
                    raciocinio_real = (
                        f"Base ativa subiu {delta_at:.1f}pp (de {val_base:.1f}% → {pct_ativos_pos:.1f}%) "
                        f"= ~{clientes_extras:.0f} clientes reativados × R$ {ticket_med:.0f} ticket "
                        f"= R$ {ganho_periodo:.0f} no período. Projeção: R$ {ganho_mensal:.0f}/mês."
                    )

            elif chave_p_calc == "produtos" and item_exp:
                vol_pos       = ok_pos[ok_pos["Nome do Item"] == item_exp].shape[0]
                vol_base      = val_base   # baseline em pedidos
                delta_vol     = vol_pos - vol_base
                if delta_vol > 0:
                    dados_item    = metricas.get("produtos", {}).get(item_exp, {})
                    margem_r      = dados_item.get("margem_r", 0)
                    ganho_periodo = delta_vol * margem_r
                    ganho_mensal  = (vol_pos / dias_exp * 30 - vol_base * 4) * margem_r
                    raciocinio_real = (
                        f"{item_exp}: {delta_vol:.0f} pedidos a mais no período "
                        f"× R$ {margem_r:.2f} margem = R$ {ganho_periodo:.0f} acumulado. "
                        f"Projeção: R$ {max(ganho_mensal,0):.0f}/mês."
                    )
    except Exception:
        pass

    # ── Renderiza cards ───────────────────────────────────────────────────
    if ganho_periodo and ganho_periodo > 0:
        col_pot, col_gan = st.columns(2)
        with col_pot:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#100a20,#0a1810);
              border:1px solid #221840;border-radius:16px;padding:28px 32px;margin-bottom:20px;">
              <div style="font-size:11px;color:#a78bfa;font-weight:600;
                text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
                💸 Potencial de Ganho
              </div>
              <div style="font-family:'Syne',sans-serif;font-size:36px;
                font-weight:800;color:#f59e0b;">
                R$ {exp['impacto']:,.0f}
              </div>
              <div style="font-size:12px;color:#606078;margin-top:8px;line-height:1.6;">
                {exp['raciocinio']}
              </div>
            </div>
            """, unsafe_allow_html=True)
        with col_gan:
            pct_capturado = min(ganho_periodo / exp['impacto'] * 100, 999) if exp['impacto'] > 0 else 0
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#0a1f10,#0d1a0a);
              border:1px solid #1a3a20;border-radius:16px;padding:28px 32px;margin-bottom:20px;">
              <div style="font-size:11px;color:#4ade80;font-weight:600;
                text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
                ✅ Ganho Realizado — {dias_exp} dia(s)
              </div>
              <div style="font-family:'Syne',sans-serif;font-size:36px;
                font-weight:800;color:#4ade80;">
                R$ {ganho_periodo:,.0f}
              </div>
              <div style="font-size:13px;color:#86efac;margin-top:6px;font-weight:600;">
                Projeção mensal: R$ {ganho_mensal:,.0f} &nbsp;·&nbsp; {pct_capturado:.0f}% do potencial
              </div>
              <div style="font-size:12px;color:#2d5a35;margin-top:8px;line-height:1.6;">
                {raciocinio_real}
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#100a20,#0a1810);
          border:1px solid #221840;border-radius:16px;padding:28px 32px;margin-bottom:20px;">
          <div style="font-size:11px;color:#a78bfa;font-weight:600;
            text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
            💸 Potencial de Ganho
          </div>
          <div style="font-family:'Syne',sans-serif;font-size:36px;
            font-weight:800;color:#f59e0b;">
            R$ {exp['impacto']:,.0f}
          </div>
          <div style="font-size:12px;color:#606078;margin-top:8px;line-height:1.6;">
            {exp['raciocinio']}
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Painel principal
    st.markdown(f"""
    <div style="font-size:11px;color:#a78bfa;font-weight:600;
      text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
      Métrica Primária — {exp['label_primaria']}
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📍 Métrica Atual", exp["baseline_atual"])
    c2.metric("🎯 Alvo", exp["baseline_alvo"])
    c3.metric("⚗️ Métrica do Experimento", metrica_pos)
    # Delta: tenta calcular numericamente
    try:
        val_exp  = float(metrica_pos.replace("R$","").replace("%","")
                         .replace(" min","").replace(" dias","")
                         .replace(" pedidos","").replace(",",".").strip())
        val_base = float(exp["baseline_atual"].replace("R$","").replace("%","")
                         .replace(" min","").replace(" dias","")
                         .replace(" pedidos","").replace(",",".").strip())
        delta_val = val_exp - val_base
        delta_fmt = f"+{delta_val:.2f}" if delta_val >= 0 else f"{delta_val:.2f}"
        delta_color = "normal"
    except:
        delta_fmt  = "—"
        delta_color = "off"
    c4.metric("Δ Delta", delta_fmt, f"{dias_exp} dia(s)", delta_color=delta_color)

    # Guardrails pós
    st.markdown("""
    <div style="font-size:11px;color:#9090a8;font-weight:600;
      text-transform:uppercase;letter-spacing:1px;margin:16px 0 8px;">
      🛡️ Guardrails
    </div>
    """, unsafe_allow_html=True)

    gcols = st.columns(len(exp["guardrails"]))
    for col, (label_g, chave_g) in zip(gcols, exp["guardrails"]):
        val_pos = calcular_metrica_pos(chave_g, df_pos, item_exp)
        dados_g = metricas.get(chave_g, {})
        _, alvo_g = fmt_metrica(chave_g, dados_g)
        col.metric(label_g, val_pos, f"Alvo: {alvo_g}", delta_color="off")

    # Ações
    st.markdown("""
    <div style="font-size:11px;color:#9090a8;font-weight:600;
      text-transform:uppercase;letter-spacing:1px;margin:20px 0 8px;">
      📋 Ações Implementadas
    </div>
    """, unsafe_allow_html=True)
    for acao in exp["problema"]["acoes"]:
        st.markdown(f"""
        <div style="background:#0f0f1e;border:1px solid #1c1c2e;
          border-radius:8px;padding:10px 14px;margin-bottom:6px;
          font-size:13px;color:#9090a8;line-height:1.5;">
          ✓ {acao}
        </div>
        """, unsafe_allow_html=True)

    # Encerrar
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    col_enc, _ = st.columns([1, 3])
    with col_enc:
        if st.button("🏁 Encerrar Experimento", type="secondary", use_container_width=True):
            if sheets_id:
                encerrar_experimento_sheets(sheets_id)
            st.session_state["experimento_ativo"] = None
            st.rerun()