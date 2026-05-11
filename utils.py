"""
Utilitários — Hub de Soluções iFood
Inclui: mock data, processamento CSV, gate de acesso, métricas de choque, gerador de plano.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import streamlit as st

# ─────────────────────────────────────────────
#  CONTROLE DE ACESSO
# ─────────────────────────────────────────────

SENHA_MASTER = "master2025"

CLIENTES_PREMIUM = {
    "burger123":  "Burguer do João",
    "pizza456":   "Pizzaria Bella Napoli",
    "frango789":  "Frango Assado do Zé",
    "demo_full":  "Demo Interna",
}

def detectar_modo() -> dict:
    params = st.query_params
    acesso = params.get("acesso", "")

    # Se veio via query param, persiste no session_state
    if acesso == SENHA_MASTER:
        st.session_state["senha_digitada"] = acesso
        return {"modo": "premium", "cliente": "Master", "is_master": True}
    if acesso in CLIENTES_PREMIUM:
        st.session_state["senha_digitada"] = acesso
        return {"modo": "premium", "cliente": CLIENTES_PREMIUM[acesso], "is_master": False}

    # Nas páginas seguintes, lê do session_state
    senha_s = st.session_state.get("senha_digitada", "")
    if senha_s == SENHA_MASTER:
        return {"modo": "premium", "cliente": "Master", "is_master": True}
    if senha_s in CLIENTES_PREMIUM:
        return {"modo": "premium", "cliente": CLIENTES_PREMIUM[senha_s], "is_master": False}

    return {"modo": "demo", "cliente": None, "is_master": False}


# ─────────────────────────────────────────────
#  CSS GLOBAL (compartilhado entre páginas)
# ─────────────────────────────────────────────

CSS_GLOBAL = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&display=swap');

html, body, [class*="css"]          { font-family: 'DM Sans', Inter; }
.stApp                               { background: #08080f; color: #e2e2f0; }
[data-testid="stSidebar"]            { background: #0e0e18 !important; border-right: 1px solid #1c1c2e; }
[data-testid="metric-container"]     { background: #111120 !important; border: 1px solid #1e1e32 !important; border-radius: 10px !important; padding: 16px !important; }
[data-testid="stMetricValue"]        { font-family: 'Syne', Inter !important; color: #34d399 !important; }
[data-testid="stMetricDeltaIcon--up"]   { color: #34d399 !important; }
[data-testid="stMetricDeltaIcon--down"] { color: #f87171 !important; }
h1, h2, h3                           { font-family: 'Syne', Inter !important; color: #e2e2f0 !important; }

.section-header {
    font-family: 'Syne', Inter;
    font-size: 18px; font-weight: 700; color: #e2e2f0;
    margin: 28px 0 14px; padding-bottom: 10px;
    border-bottom: 1px solid #1c1c2e;
}

/* ── page links sidebar ── */
[data-testid="stSidebar"] a,
[data-testid="stSidebar"] a p,
[data-testid="stSidebar"] a span,
[data-testid="stSidebar"] [data-testid="stPageLink"] a,
[data-testid="stSidebar"] [data-testid="stPageLink"] p,
[data-testid="stSidebar"] [data-testid="stPageLink"] span {
    color: #e2e2f0 !important;
    text-decoration: none !important;
}

[data-testid="stSidebar"] a:hover,
[data-testid="stSidebar"] a:hover p,
[data-testid="stSidebar"] a:hover span,
[data-testid="stSidebar"] [data-testid="stPageLink"]:hover a,
[data-testid="stSidebar"] [data-testid="stPageLink"]:hover p,
[data-testid="stSidebar"] [data-testid="stPageLink"]:hover span {
    color: #a78bfa !important;
}

/* ── lock / premium ── */
.lock-card {
    background: linear-gradient(135deg, #0f0f1e, #160f2a);
    border: 1px solid #2a1a4e;
    border-radius: 12px;
    padding: 28px 24px;
    text-align: center;
    margin: 20px 0;
}
.lock-icon  { font-size: 36px; margin-bottom: 10px; }
.lock-title { font-family:'Syne',Inter; font-size:18px; font-weight:700; color:#e2e2f0; margin-bottom:6px; }
.lock-sub   { font-size:14px; color:#60607a; line-height:1.6; margin-bottom:18px; }
.lock-items { list-style:none; padding:0; margin:0 0 20px; text-align:left; display:inline-block; }
.lock-items li { font-size:13px; color:#9090a8; padding:4px 0; }
.lock-items li::before { content:"🔒 "; }
.wpp-btn {
    display:inline-block; background:#25d366; color:#000 !important;
    font-family:'Syne',Inter; font-size:14px; font-weight:700;
    padding:12px 28px; border-radius:8px; text-decoration:none !important;
}

/* ── insight boxes ── */
.insight { background:#111120; border:1px solid #1e1e32; border-radius:8px; padding:14px 18px; margin:10px 0; }
.insight.yellow { border-left:3px solid #f59e0b; }
.insight.red    { border-left:3px solid #f87171; }
.insight.green  { border-left:3px solid #34d399; }
.insight.purple { border-left:3px solid #a78bfa; }
.insight-title  { font-family:'Syne',Inter; font-size:13px; font-weight:700; color:#e2e2f0; margin-bottom:3px; }
.insight-text   { font-size:13px; color:#70708a; line-height:1.5; }

/* ── teaser blur ── */
.blur-wrap { position:relative; border-radius:10px; overflow:hidden; }
.blur-wrap .blur-content { filter:blur(5px) brightness(0.6); pointer-events:none; user-select:none; }
.blur-wrap .blur-overlay {
    position:absolute; inset:0; display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    background:rgba(8,8,15,0.55); backdrop-filter:blur(2px);
    font-family:'Syne',Inter; text-align:center; padding:16px;
}
.blur-overlay span { font-size:28px; margin-bottom:8px; }
.blur-overlay p    { font-size:14px; color:#c0c0d8; margin:0; }

/* ── plano card ── */
.plano-card {
    background:#0f0f1e; border:1px solid #1e1e32; border-radius:12px;
    padding:20px 22px; margin:12px 0;
}
.plano-cat   { font-size:12px; color:#a78bfa; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px; }
.plano-title { font-family:'Syne',Inter; font-size:16px; font-weight:700; color:#e2e2f0; margin-bottom:6px; }
.plano-desc  { font-size:13px; color:#70708a; line-height:1.6; margin-bottom:12px; }
.plano-impacto { font-size:13px; color:#f59e0b; font-weight:500; margin-bottom:10px; }
.plano-acao  { font-size:13px; color:#9090a8; padding:4px 0; border-top:1px solid #1c1c2e; }

/* ── choque numbers ── */
.choque-grid { display:flex; gap:16px; flex-wrap:wrap; margin:20px 0; }
.choque-item {
    flex:1; min-width:200px;
    background:#0f0f1e; border:1px solid #1e1e32; border-radius:12px;
    padding:20px 18px;
}
.choque-icon  { font-size:26px; margin-bottom:8px; }
.choque-value { font-family:'Syne',Inter; font-size:28px; font-weight:800; color:#f59e0b; line-height:1.1; }
.choque-label { font-size:12px; color:#60607a; margin-top:4px; line-height:1.4; }

/* misc */
.tag-demo    { display:inline-block; background:rgba(52,211,153,0.12); border:1px solid rgba(52,211,153,0.3); color:#34d399; font-size:11px; font-weight:600; letter-spacing:1px; text-transform:uppercase; padding:3px 10px; border-radius:20px; margin-bottom:12px; }
.tag-premium { display:inline-block; background:rgba(245,158,11,0.12); border:1px solid rgba(245,158,11,0.3); color:#f59e0b; font-size:11px; font-weight:600; letter-spacing:1px; text-transform:uppercase; padding:3px 10px; border-radius:20px; margin-bottom:12px; }
</style>
"""

def inject_css():
    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)


def render_sidebar(active: str = "home"):
    """Sidebar padrão com navegação + gate de acesso."""
    acesso = detectar_modo()

    with st.sidebar:
        st.markdown("""
        <div style="padding:14px 0 6px;">
            <div style="font-family:'Syne',Inter;font-size:19px;font-weight:800;color:#e2e2f0;">🍕 DeliveryPro</div>
            <div style="font-size:11px;color:#40405a;letter-spacing:1.2px;text-transform:uppercase;margin-top:2px;">Hub de Soluções</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")

        st.page_link("streamlit_app.py",         label="🏠  Visão Geral")
        st.page_link("pages/1_Operacao.py",      label="🚚  Operação")
        st.page_link("pages/2_Lucratividade.py", label="💰  Lucratividade")
        st.page_link("pages/3_Fidelizacao.py",   label="❤️  Fidelização")

        if acesso["modo"] == "premium":
            st.page_link("pages/4_Plano.py", label="🧠  Plano de Crescimento")
        else:
            st.markdown("""
            <div style="padding:6px 12px;margin:2px 0;border-radius:6px;background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.15);">
                <span style="font-size:13px;color:#50504a;">🔒  Plano de Crescimento</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")

        # Badge de modo
        if acesso["modo"] == "premium":
            nome = acesso["cliente"]
            st.markdown(f"""
            <div style="background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.2);border-radius:8px;padding:10px 12px;">
                <div style="font-size:11px;color:#34d399;font-weight:600;text-transform:uppercase;letter-spacing:1px;">✅ Acesso Premium</div>
                <div style="font-size:13px;color:#9090a8;margin-top:2px;">{nome}</div>
            </div>""", unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Sair", use_container_width=True, key="btn_sair"):
                st.session_state["senha_digitada"] = ""
                st.query_params.clear()
                st.rerun()
        else:
            st.markdown("""
            <div style="background:rgba(17,17,32,0.6);border:1px solid #1e1e32;border-radius:8px;padding:10px 12px;">
                <div style="font-size:11px;color:#f59e0b;font-weight:600;text-transform:uppercase;letter-spacing:1px;">🔓 Modo Demo</div>
                <div style="font-size:12px;color:#50507a;margin-top:4px;line-height:1.5;">Diagnóstico completo bloqueado</div>
            </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            senha_input = st.text_input("Código de acesso", type="password", placeholder="Digite seu código", key="senha_input_sidebar")
        if st.button("Acessar", use_container_width=True, key="btn_acessar"):
            if senha_input:
                if senha_input == SENHA_MASTER or senha_input in CLIENTES_PREMIUM:
                    st.session_state["senha_digitada"] = senha_input
                    st.rerun()
                else:
                    st.error("Acesso negado.")

        # Painel master (oculto — só aparece se is_master)
        if acesso["is_master"]:
            st.markdown("---")
            st.markdown("""
            <div style="font-size:11px;color:#a78bfa;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                🔧 Painel Master
            </div>""", unsafe_allow_html=True)
            ajuste = st.text_area(
                "Observações personalizadas para este cliente",
                key="ajuste_manual_master",
                height=120,
                placeholder="Ex: 'No seu caso, o item Hamburguer Duplo representa 32% das vendas e é o maior problema de margem...'"
            )
            if ajuste:
                st.session_state["ajuste_manual"] = ajuste


def render_lock_card(titulo: str, itens_bloqueados: list, wpp_numero: str = "5511999999999"):
    """Card padrão de bloqueio premium."""
    itens_html = "".join(f"<li>{i}</li>" for i in itens_bloqueados)
    wpp_msg = "Olá! Quero ver o diagnóstico completo do meu delivery."
    wpp_url = f"https://wa.me/{wpp_numero}?text={wpp_msg.replace(' ', '%20')}"

    st.markdown(f"""
    <div class="lock-card">
        <div class="lock-icon">🔒</div>
        <div class="lock-title">{titulo}</div>
        <div class="lock-sub">Disponível no diagnóstico completo. O que você vai ver:</div>
        <ul class="lock-items">{itens_html}</ul>
        <a href="{wpp_url}" class="wpp-btn" target="_blank">💬 Quero o diagnóstico completo</a>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MOCK DATA
# ─────────────────────────────────────────────

BAIRROS = [
    "Centro", "Vila Madalena", "Pinheiros", "Itaim Bibi",
    "Moema", "Lapa", "Santana", "Tatuapé",
    "Perdizes", "Consolação", "Bela Vista", "Liberdade"
]

COORDS_BAIRROS = {
    "Centro":            (-23.5505, -46.6333),
    "Vila Madalena":     (-23.5558, -46.6920),
    "Pinheiros":         (-23.5665, -46.6947),
    "Itaim Bibi":        (-23.5853, -46.6767),
    "Moema":             (-23.6013, -46.6650),
    "Lapa":              (-23.5270, -46.7060),
    "Santana":           (-23.4970, -46.6260),
    "Tatuapé":           (-23.5380, -46.5700),
    "Perdizes":          (-23.5350, -46.6680),
    "Consolação":        (-23.5520, -46.6570),
    "Bela Vista":        (-23.5590, -46.6430),
    "Liberdade":         (-23.5599, -46.6338),
}

ITENS_CARDAPIO = {
    "Pizza Margherita":         {"custo": 18.0, "preco": 49.90},
    "Pizza Calabresa":          {"custo": 20.0, "preco": 54.90},
    "Pizza Frango c/ Catupiry": {"custo": 22.0, "preco": 59.90},
    "Pizza Portuguesa":         {"custo": 24.0, "preco": 62.90},
    "Pizza Quatro Queijos":     {"custo": 25.0, "preco": 64.90},
    "Hamburger Clássico":       {"custo": 14.0, "preco": 32.90},
    "Hamburger Bacon":          {"custo": 16.0, "preco": 38.90},
    "Hamburger Duplo":          {"custo": 18.0, "preco": 44.90},
    "Batata Frita P":           {"custo":  5.0, "preco": 16.90},
    "Batata Frita G":           {"custo":  7.0, "preco": 22.90},
    "Refrigerante Lata":        {"custo":  3.5, "preco":  8.90},
    "Suco Natural":             {"custo":  4.0, "preco": 12.90},
    "Combo Família":            {"custo": 38.0, "preco": 89.90},
    "Sobremesa Brownie":        {"custo":  6.0, "preco": 18.90},
}

POPULARIDADE = {
    "Pizza Margherita":         0.13,
    "Pizza Calabresa":          0.11,
    "Pizza Frango c/ Catupiry": 0.09,
    "Pizza Portuguesa":         0.07,
    "Pizza Quatro Queijos":     0.06,
    "Hamburger Clássico":       0.10,
    "Hamburger Bacon":          0.09,
    "Hamburger Duplo":          0.06,
    "Batata Frita P":           0.08,
    "Batata Frita G":           0.05,
    "Refrigerante Lata":        0.07,
    "Suco Natural":             0.03,
    "Combo Família":            0.04,
    "Sobremesa Brownie":        0.02,
}

MARGEM_PROXY        = 0.30
TAXA_RETORNO_CLIENTE = 0.25


def generate_mock_ifood_data(n_pedidos: int = 800) -> pd.DataFrame:
    np.random.seed(42)
    random.seed(42)

    hoje   = datetime.today()
    datas  = sorted([hoje - timedelta(days=random.randint(0, 180)) for _ in range(n_pedidos)])
    itens  = random.choices(list(POPULARIDADE.keys()), weights=list(POPULARIDADE.values()), k=n_pedidos)
    bairros = random.choices(BAIRROS, k=n_pedidos)
    status  = np.random.choice(["Concluído", "Cancelado"], size=n_pedidos, p=[0.88, 0.12])

    valor_itens    = [ITENS_CARDAPIO[i]["preco"] * random.randint(1, 3) for i in itens]
    taxa_entrega   = [random.uniform(3.0, 8.5) for _ in range(n_pedidos)]
    valor_bruto    = [v + t for v, t in zip(valor_itens, taxa_entrega)]
    comissao_pct   = [random.uniform(0.12, 0.27) for _ in range(n_pedidos)]
    comissao_ifood = [v * c for v, c in zip(valor_bruto, comissao_pct)]
    distancia_km   = [random.uniform(0.5, 8.5) for _ in range(n_pedidos)]
    tempo_entrega  = [int(15 + d * 4 + np.random.normal(0, 5)) for d in distancia_km]

    n_cli   = int(n_pedidos * 0.55)
    cli_ids = [f"CLI{random.randint(1000,9999)}" for _ in range(n_cli)]

    coords = [COORDS_BAIRROS[b] for b in bairros]

    return pd.DataFrame({
        "Data do Pedido":         datas,
        "ID do Pedido":           [f"PED{random.randint(100000,999999)}" for _ in range(n_pedidos)],
        "ID do Cliente":          [random.choice(cli_ids) for _ in range(n_pedidos)],
        "Status":                 status,
        "Nome do Item":           itens,
        "Valor dos Itens":        valor_itens,
        "Taxa de Entrega":        taxa_entrega,
        "Valor Bruto":            valor_bruto,
        "Comissão iFood":         comissao_ifood,
        "Distância (km)":         distancia_km,
        "Bairro":                 bairros,
        "Tempo de Entrega (min)": tempo_entrega,
        "lat":  [c[0] + np.random.normal(0, 0.005) for c in coords],
        "lon":  [c[1] + np.random.normal(0, 0.005) for c in coords],
    })


def process_ifood_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    date_cols = [c for c in df.columns if "data" in c.lower() or "date" in c.lower()]
    if date_cols:
        df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], dayfirst=True, errors="coerce")
        df.rename(columns={date_cols[0]: "Data do Pedido"}, inplace=True)

    if "Status" in df.columns:
        df["Status"] = df["Status"].str.strip().str.title()

    for col in ["Valor dos Itens", "Taxa de Entrega", "Valor Bruto", "Comissão iFood"]:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = (df[col].astype(str)
                    .str.replace("R$","",regex=False).str.replace(".","",regex=False)
                    .str.replace(",",".",regex=False).str.strip())
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Receita Líquida"] = df.get("Valor Bruto", 0) - df.get("Comissão iFood", 0)
    df["is_cancelado"]    = df.get("Status", pd.Series("")).str.lower().str.contains("cancel").fillna(False)

    if "Data do Pedido" in df.columns:
        df["Mês"]        = df["Data do Pedido"].dt.to_period("M").astype(str)
        df["Dia Semana"] = df["Data do Pedido"].dt.day_name()
        df["Hora"]       = df["Data do Pedido"].dt.hour

    return df


def get_kpis(df: pd.DataFrame) -> dict:
    ok  = df[~df["is_cancelado"]]
    can = df[df["is_cancelado"]]
    fat = ok["Valor Bruto"].sum()
    liq = ok["Receita Líquida"].sum()
    return {
        "faturamento":         fat,
        "receita_liquida":     liq,
        "ticket_medio":        ok["Valor Bruto"].mean() if len(ok) else 0,
        "total_pedidos":       len(ok),
        "taxa_cancelamento":   len(can) / len(df) * 100 if len(df) else 0,
        "comissao_total":      ok["Comissão iFood"].sum(),
        "perda_cancelamentos": can["Valor Bruto"].sum(),
    }


# ─────────────────────────────────────────────
#  CHOQUE DE REALIDADE
# ─────────────────────────────────────────────

def calcular_choque(df: pd.DataFrame) -> dict:
    ok = df[~df["is_cancelado"]].copy()

    # Itens-problema
    item_s = (ok.groupby("Nome do Item")
               .agg(vendas=("Nome do Item","count"), receita=("Valor dos Itens","sum"))
               .reset_index())
    item_s["margem"] = item_s["Nome do Item"].apply(
        lambda n: (ITENS_CARDAPIO[n]["preco"]-ITENS_CARDAPIO[n]["custo"])/ITENS_CARDAPIO[n]["preco"]
        if n in ITENS_CARDAPIO else MARGEM_PROXY)
    med_v = item_s["vendas"].median()
    med_m = item_s["margem"].median()

    problema = item_s[(item_s["vendas"] >= med_v) & (item_s["margem"] < med_m)]
    n_problema = len(problema)
    perda_m_base = (problema["receita"] * (med_m - problema["margem"])).sum()

    # Clientes inativos
    hoje = ok["Data do Pedido"].max()
    cli  = (ok.groupby("ID do Cliente")
              .agg(ultimo=("Data do Pedido","max"), pedidos=("ID do Pedido","count"))
              .reset_index())
    cli["dias_inativo"] = (hoje - cli["ultimo"]).dt.days
    inativos   = cli[cli["dias_inativo"] > 30]
    n_inativos = len(inativos)
    pct_churn  = n_inativos / len(cli) * 100 if len(cli) else 0

    ticket_med   = ok["Valor Bruto"].mean()
    ped_med      = ok.groupby("ID do Cliente").size().mean()
    perda_r_base = n_inativos * TAXA_RETORNO_CLIENTE * ticket_med * max(ped_med, 1)

    perda_cancel = df[df["is_cancelado"]]["Valor Bruto"].sum()

    dias = max((ok["Data do Pedido"].max() - ok["Data do Pedido"].min()).days, 1)
    fator = 30 / dias

    total_base = (perda_m_base + perda_r_base + perda_cancel * 0.35) * fator
    return {
        "perda_low":          max(total_base * 0.65, 0),
        "perda_high":         max(total_base * 1.10, 0),
        "n_itens_problema":   n_problema,
        "pct_churn":          pct_churn,
        "n_inativos":         n_inativos,
        "perda_margem_base":  perda_m_base,
        "perda_retencao_base":perda_r_base,
        "perda_cancel":       perda_cancel,
    }


# ─────────────────────────────────────────────
#  GERADOR DE PLANO (regras if/else)
# ─────────────────────────────────────────────
 
# Badges de confiança — usados nos cards do plano
CONFIANCA = {
    "alta":   {"badge": "🟢 Alta confiança",  "cor": "#34d399", "bg": "rgba(52,211,153,0.10)", "borda": "rgba(52,211,153,0.25)"},
    "media":  {"badge": "🟡 Média confiança", "cor": "#f59e0b", "bg": "rgba(245,158,11,0.10)", "borda": "rgba(245,158,11,0.25)"},
    "estimativa": {"badge": "🔴 Estimativa",  "cor": "#f87171", "bg": "rgba(248,113,113,0.10)","borda": "rgba(248,113,113,0.25)"},
}
 
 
def gerar_plano_automatico(df: pd.DataFrame) -> dict:
    ok     = df[~df["is_cancelado"]].copy()
    choque = calcular_choque(df)
    kpis   = get_kpis(df)
 
    problemas = []
 
    # ── cardápio ─────────────────────────────────────────────────────────
    item_s = (ok.groupby("Nome do Item")
               .agg(vendas=("Nome do Item","count"), receita=("Valor dos Itens","sum"))
               .reset_index())
 
    # Verificar se custo veio de dado real ou proxy
    tem_custo_real = any(n in ITENS_CARDAPIO for n in item_s["Nome do Item"])
 
    item_s["margem"] = item_s["Nome do Item"].apply(
        lambda n: (ITENS_CARDAPIO[n]["preco"]-ITENS_CARDAPIO[n]["custo"])/ITENS_CARDAPIO[n]["preco"]
        if n in ITENS_CARDAPIO else MARGEM_PROXY)
    item_s["ticket"] = item_s["receita"] / item_s["vendas"]
    med_v = item_s["vendas"].median()
    med_m = item_s["margem"].median()
 
    cavalos    = item_s[(item_s["vendas"] >= med_v) & (item_s["margem"] < med_m)].sort_values("receita", ascending=False)
    potenciais = item_s[(item_s["vendas"] < med_v)  & (item_s["margem"] >= med_m)].sort_values("margem", ascending=False)
 
    if len(cavalos) > 0:
        nomes = ", ".join(cavalos["Nome do Item"].head(3).tolist())
        confianca_luc = "alta" if tem_custo_real else "media"
 
        acoes = []
        for _, r in cavalos.head(3).iterrows():
            m        = r["margem"] * 100
            vendas_r = int(r["vendas"])
            ticket_r = r["ticket"]
            nome     = r["Nome do Item"]
 
            # Buscar complementos para combo (itens de baixo custo e alta margem)
            complementos = item_s[
                (item_s["Nome do Item"] != nome) &
                (item_s["margem"] >= med_m) &
                (item_s["ticket"] < ticket_r * 0.4)
            ].sort_values("margem", ascending=False)
 
            if m < 25:
                aumento_preco = round(ticket_r * 0.10, 2)
                ganho_mensal  = round(aumento_preco * vendas_r, 2)
                acoes.append(
                    f"**{nome}** — margem de {m:.0f}%, vendeu {vendas_r}x no período. "
                    f"Aumentar R$ {aumento_preco:.2f} no preço mantendo volume = "
                    f"+R$ {ganho_mensal:.0f} direto na margem."
                )
            elif len(complementos) > 0 and r["vendas"] > med_v * 1.2:
                comp        = complementos.iloc[0]
                preco_comp  = comp["ticket"]
                nome_comp   = comp["Nome do Item"]
                ticket_novo = round(ticket_r + preco_comp * 0.85, 2)
                ganho_combo = round((ticket_novo - ticket_r) * vendas_r * 0.35, 2)
                acoes.append(
                    f"**{nome}** — criar combo com {nome_comp} "
                    f"(+R$ {preco_comp*0.85:.2f} no ticket). "
                    f"Se 35% dos pedidos virar combo = +R$ {ganho_combo:.0f} no período."
                )
            else:
                aumento = round(ticket_r * 0.08, 2)
                acoes.append(
                    f"**{nome}** — {vendas_r} pedidos no período, margem apertada. "
                    f"Testar reajuste de R$ {aumento:.2f} — se volume se mantiver, "
                    f"adiciona R$ {aumento*vendas_r:.0f} ao resultado."
                )
 
        impacto = choque["perda_margem_base"]
        dias    = max((ok["Data do Pedido"].max() - ok["Data do Pedido"].min()).days, 1)
        fator   = 30 / dias
        imp_mes_low  = impacto * fator * 0.6
        imp_mes_high = impacto * fator * 1.0
 
        raciocinio = (
            f"{len(cavalos)} {'item' if len(cavalos)==1 else 'itens'} com volume acima da média "
            f"e margem abaixo — diferença acumulada de R$ {impacto:.0f} no período "
            f"(~R$ {imp_mes_low:.0f} – R$ {imp_mes_high:.0f}/mês projetado)."
        )
 
        problemas.append({
            "categoria":   "💰 Lucratividade",
            "titulo":      f"{len(cavalos)} {'item' if len(cavalos)==1 else 'itens'} vendendo muito, mas com margem baixa",
            "descricao":   f"Itens como {nomes} representam boa parte do volume, mas a margem está abaixo da média do seu cardápio. Você trabalha mais para ganhar menos nesses produtos.",
            "raciocinio":  raciocinio,
            "impacto_r":   impacto,
            "confianca":   confianca_luc,
            "acoes":       acoes,
            "prioridade":  1 if impacto > 500 else 2,
        })
 
    if len(potenciais) > 0:
        nomes = ", ".join(potenciais["Nome do Item"].head(2).tolist())
        confianca_pot = "alta" if tem_custo_real else "media"
        impacto_pot   = potenciais["receita"].sum() * 0.25
 
        acoes = []
        for _, r in potenciais.head(2).iterrows():
            m       = r["margem"] * 100
            vendas_r = int(r["vendas"])
            nome    = r["Nome do Item"]
            # Estimar ganho se dobrar o volume
            ganho_dobrar = round(r["receita"] * r["margem"] * 0.5, 2)
            acoes.append(
                f"**{nome}** — margem de {m:.0f}%, só {vendas_r} pedidos no período. "
                f"Destacar com foto e descrição no app — dobrar o volume geraria "
                f"+R$ {ganho_dobrar:.0f} de margem adicional."
            )
 
        problemas.append({
            "categoria":  "💰 Lucratividade",
            "titulo":     f"{len(potenciais)} {'item' if len(potenciais)==1 else 'itens'} com ótima margem sendo ignorados",
            "descricao":  f"{nomes} têm margem acima da média mas baixo volume. São os produtos mais rentáveis do seu cardápio — e poucos clientes os pedem.",
            "raciocinio": f"Potencial de +R$ {impacto_pot:.0f} no período se esses itens dobrarem de volume.",
            "impacto_r":  impacto_pot,
            "confianca":  confianca_pot,
            "acoes":      acoes,
            "prioridade": 2,
        })
 
    # ── operação ─────────────────────────────────────────────────────────
    tempo_med = ok["Tempo de Entrega (min)"].mean() if "Tempo de Entrega (min)" in ok.columns else 0
    tx_cancel = kpis["taxa_cancelamento"]
    n_cancel  = int(df["is_cancelado"].sum())
    ticket_med = kpis["ticket_medio"]
 
    if tempo_med > 45:
        lentos = (ok.groupby("Bairro")["Tempo de Entrega (min)"].mean()
                   .sort_values(ascending=False).head(3).index.tolist())
        excesso_min  = tempo_med - 45
        cancel_extra = round(n_cancel * (excesso_min * 0.03), 0)
        impacto_op   = kpis["perda_cancelamentos"] * 0.40
        imp_mes_low  = impacto_op * (30 / max((ok["Data do Pedido"].max() - ok["Data do Pedido"].min()).days,1)) * 0.6
        imp_mes_high = impacto_op * (30 / max((ok["Data do Pedido"].max() - ok["Data do Pedido"].min()).days,1))
 
        raciocinio = (
            f"Tempo médio {tempo_med:.0f} min = {excesso_min:.0f} min acima da meta de 45 min. "
            f"Cada minuto extra aumenta ~3% a chance de cancelamento — "
            f"estimativa de {cancel_extra:.0f} cancelamentos evitáveis "
            f"(~R$ {imp_mes_low:.0f} – R$ {imp_mes_high:.0f}/mês)."
        )
 
        problemas.append({
            "categoria":  "🚚 Operação",
            "titulo":     f"Tempo médio de entrega em {tempo_med:.0f} min — acima do ideal",
            "descricao":  "Entregas longas aumentam cancelamentos e derrubam a avaliação no app. Clientes que esperam mais do que esperavam raramente voltam.",
            "raciocinio": raciocinio,
            "impacto_r":  impacto_op,
            "confianca":  "media",
            "acoes": [
                f"Reduzir raio de entrega em {lentos[0]} e {lentos[1] if len(lentos)>1 else lentos[0]} — os bairros com pior tempo médio.",
                f"Ajustar horário de pico: verificar se há motoboys suficientes nos horários de maior volume.",
                f"Aumentar taxa de entrega para bairros acima de 6 km — desestimula pedidos que prejudicam o tempo médio.",
            ],
            "prioridade": 2 if tempo_med < 55 else 1,
        })
 
    if tx_cancel > 10:
        cancel_evit   = round(n_cancel * 0.35, 0)
        recuper       = round(cancel_evit * ticket_med, 2)
        impacto_can   = kpis["perda_cancelamentos"] * 0.35
        dias          = max((ok["Data do Pedido"].max() - ok["Data do Pedido"].min()).days, 1)
        imp_mes       = impacto_can * (30 / dias)
 
        raciocinio = (
            f"{n_cancel} cancelamentos no período = R$ {kpis['perda_cancelamentos']:,.0f} perdidos. "
            f"Com ajustes operacionais, ~35% são evitáveis ({cancel_evit:.0f} pedidos × "
            f"R$ {ticket_med:.0f} ticket = R$ {recuper:,.0f} recuperáveis — "
            f"~R$ {imp_mes:.0f}/mês projetado)."
        )
 
        problemas.append({
            "categoria":  "🚚 Operação",
            "titulo":     f"Taxa de cancelamento de {tx_cancel:.1f}% acima da meta de 8%",
            "descricao":  f"Você perdeu R$ {kpis['perda_cancelamentos']:,.0f} em pedidos cancelados no período. Cancelamento é receita que entra e sai antes de virar lucro.",
            "raciocinio": raciocinio,
            "impacto_r":  impacto_can,
            "confianca":  "media",
            "acoes": [
                f"Identificar se os cancelamentos concentram em horário ou bairro específico (ver aba Operação).",
                f"Verificar se algum item específico aparece em cancelamentos — pode ser problema de estoque ou preparo.",
                f"Ativar mensagem automática de confirmação de pedido no iFood — reduz desistência por ansiedade.",
            ],
            "prioridade": 1 if tx_cancel > 15 else 2,
        })
 
    # ── fidelização ───────────────────────────────────────────────────────
    pct_c      = choque["pct_churn"]
    n_inat     = choque["n_inativos"]
    ticket_med = kpis["ticket_medio"]
 
    if pct_c > 40:
        n_retorno    = round(n_inat * TAXA_RETORNO_CLIENTE, 0)
        receita_camp = round(n_retorno * ticket_med, 2)
        custo_cupom  = round(n_retorno * 12.50, 2)   # cupom médio de R$ 12,50
        lucro_camp   = round(receita_camp - custo_cupom, 2)
        imp_low      = lucro_camp * 0.7
        imp_high     = lucro_camp * 1.1
 
        raciocinio = (
            f"{n_inat} clientes inativos há +30 dias → reativar ~25% = "
            f"{n_retorno:.0f} clientes voltando → "
            f"{n_retorno:.0f} × R$ {ticket_med:.0f} ticket = R$ {receita_camp:,.0f} em receita. "
            f"Descontando cupom de R$ 12,50 por cliente = "
            f"R$ {imp_low:,.0f} – R$ {imp_high:,.0f} de retorno líquido."
        )
 
        problemas.append({
            "categoria":  "❤️ Fidelização",
            "titulo":     f"{pct_c:.0f}% dos clientes não voltaram a pedir",
            "descricao":  f"Dos clientes que já compraram de você, {pct_c:.0f}% estão inativos há mais de 30 dias. Trazer cliente de volta custa 5x menos do que conquistar um novo.",
            "raciocinio": raciocinio,
            "impacto_r":  choque["perda_retencao_base"],
            "confianca":  "alta",
            "acoes": [
                f"Criar campanha no iFood para os {n_inat} clientes inativos com cupom de R$ 10–15.",
                f"Priorizar os {min(20, n_inat)} clientes de maior ticket histórico para abordagem manual.",
                f"Meta: {n_retorno:.0f} clientes voltando no próximo mês = R$ {receita_camp:,.0f} em receita adicional.",
            ],
            "prioridade": 1 if pct_c > 55 else 2,
        })
 
    problemas.sort(key=lambda x: (x["prioridade"], -x["impacto_r"]))
 
    impacto_total = sum(p["impacto_r"] for p in problemas)
    dias  = max((ok["Data do Pedido"].max() - ok["Data do Pedido"].min()).days, 1)
    fator = 30 / dias
 
    return {
        "problemas":           problemas,
        "impacto_mensal_low":  max(impacto_total * fator * 0.60, 0),
        "impacto_mensal_high": max(impacto_total * fator * 1.00, 0),
        "n_problemas":         len(problemas),
    }
