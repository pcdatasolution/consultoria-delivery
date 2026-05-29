"""
Utilitários — Hub de Soluções iFood
Inclui: mock data, processamento CSV, gate de acesso, métricas de choque, gerador de plano.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import streamlit as st
import gspread
import json
import os
from google.oauth2.service_account import Credentials

# ─────────────────────────────────────────────
#  CONTROLE DE ACESSO
# ─────────────────────────────────────────────

SENHA_MASTER = "master2025"

CLIENTES_PREMIUM = {
    "burger123": {"nome": "Burguer do João",        "sheets_id": "1fonnx8d9zbdTtGLIy__jv9P2atycuIFT82bjaOm0jfc"},
    "pizza456":  {"nome": "Pizzaria Bella Napoli",  "sheets_id": ""},
    "frango789": {"nome": "Frango Assado do Zé",    "sheets_id": ""},
    "burgueria0000": {"nome": "Burgueria",           "sheets_id": "12xeUXbNQlKdafczf1v2H59Ewk_VFk_L0tyDee1UJa2k"},
}

def detectar_modo() -> dict:
    params = st.query_params
    acesso = params.get("acesso", "")

    if acesso == SENHA_MASTER:
        st.session_state["senha_digitada"] = acesso
        return {"modo": "premium", "cliente": "Master", "sheets_id": None, "is_master": True}
    if acesso in CLIENTES_PREMIUM:
        st.session_state["senha_digitada"] = acesso
        info = CLIENTES_PREMIUM[acesso]
        return {"modo": "premium", "cliente": info["nome"], "sheets_id": info["sheets_id"], "is_master": False}

    senha_s = st.session_state.get("senha_digitada", "")
    if senha_s == SENHA_MASTER:
        return {"modo": "premium", "cliente": "Master", "sheets_id": None, "is_master": True}
    if senha_s in CLIENTES_PREMIUM:
        info = CLIENTES_PREMIUM[senha_s]
        return {"modo": "premium", "cliente": info["nome"], "sheets_id": info["sheets_id"], "is_master": False}

    # Sem senha — acesso livre, mock data, tudo visível
    return {"modo": "premium", "cliente": None, "sheets_id": None, "is_master": False}


# ─────────────────────────────────────────────
#  CSS GLOBAL (compartilhado entre páginas)
# ─────────────────────────────────────────────

CSS_GLOBAL = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Base ── */
html, body, [class*="css"], * {
    font-family: 'Inter', sans-serif !important;
}
.stApp {
    background: #ffffff !important;
    color: #111111 !important;
}
.stApp [data-testid="stMarkdownContainer"] p {
    color: inherit !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e5e9f0 !important;
}
[data-testid="stSidebar"] * {
    color: #111111 !important;
}
/* ── Esconder label nativo do file_uploader ── */
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] {
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}
/* ── Sidebar nav links ── */
[data-testid="stSidebar"] a,
[data-testid="stSidebar"] a p,
[data-testid="stSidebar"] a span,
[data-testid="stSidebar"] [data-testid="stPageLink"] a,
[data-testid="stSidebar"] [data-testid="stPageLink"] p,
[data-testid="stSidebar"] [data-testid="stPageLink"] span {
    color: #111111 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    text-decoration: none !important;
}
[data-testid="stSidebar"] a:hover p,
[data-testid="stSidebar"] a:hover span,
[data-testid="stSidebar"] [data-testid="stPageLink"]:hover p,
[data-testid="stSidebar"] [data-testid="stPageLink"]:hover span {
    color: #2f5f98 !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #f5f7fb !important;
    border: 1px solid #e0e6f0 !important;
    border-radius: 10px !important;
    padding: 16px !important;
}
[data-testid="stMetricLabel"] p {
    color: #111111 !important;
    font-weight: 500 !important;
}
[data-testid="stMetricValue"] {
    color: #2f5f98 !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDeltaIcon--up"]   { color: #16a34a !important; }
[data-testid="stMetricDeltaIcon--down"] { color: #dc2626 !important; }

/* ── Headings ── */
h1, h2, h3 {
    font-family: 'Inter', sans-serif !important;
    color: #2f5f98 !important;
}

/* ── Section header ── */
.section-header {
    font-family: 'Inter', sans-serif;
    font-size: 17px;
    font-weight: 700;
    color: #2f5f98;
    margin: 28px 0 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #e0e6f0;
}

/* ── Lock / premium card ── */
.lock-card {
    background: #f5f7fb;
    border: 1px solid #d0daf0;
    border-radius: 12px;
    padding: 28px 24px;
    text-align: center;
    margin: 20px 0;
}
.lock-icon  { font-size: 36px; margin-bottom: 10px; }
.lock-title { font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 700; color: #2f5f98; margin-bottom: 6px; }
.lock-sub   { font-size: 14px; color: #555; line-height: 1.6; margin-bottom: 18px; }
.lock-items { list-style: none; padding: 0; margin: 0 0 20px; text-align: left; display: inline-block; }
.lock-items li { font-size: 13px; color: #333; padding: 4px 0; }
.lock-items li::before { content: "🔒 "; }
.wpp-btn {
    display: inline-block; background: #25d366; color: #000 !important;
    font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 700;
    padding: 12px 28px; border-radius: 8px; text-decoration: none !important;
}

/* ── Insight boxes ── */
.insight { background: #f5f7fb; border: 1px solid #e0e6f0; border-radius: 8px; padding: 14px 18px; margin: 10px 0; }
.insight.yellow { border-left: 3px solid #f59e0b; }
.insight.red    { border-left: 3px solid #dc2626; }
.insight.green  { border-left: 3px solid #16a34a; }
.insight.purple { border-left: 3px solid #2f5f98; }
.insight-title  { font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 700; color: #111; margin-bottom: 3px; }
.insight-text   { font-size: 13px; color: #444; line-height: 1.5; }

/* ── Teaser blur ── */
.blur-wrap { position: relative; border-radius: 10px; overflow: hidden; }
.blur-wrap .blur-content { filter: blur(5px) brightness(0.9); pointer-events: none; user-select: none; }
.blur-wrap .blur-overlay {
    position: absolute; inset: 0; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    background: rgba(255,255,255,0.70); backdrop-filter: blur(2px);
    font-family: 'Inter', sans-serif; text-align: center; padding: 16px;
}
.blur-overlay span { font-size: 28px; margin-bottom: 8px; }
.blur-overlay p    { font-size: 14px; color: #333; margin: 0; }

/* ── Plano card ── */
.plano-card {
    background: #f5f7fb; border: 1px solid #e0e6f0; border-radius: 12px;
    padding: 20px 22px; margin: 12px 0;
}
.plano-cat   { font-size: 12px; color: #2f5f98; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
.plano-title { font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 700; color: #111; margin-bottom: 6px; }
.plano-desc  { font-size: 13px; color: #444; line-height: 1.6; margin-bottom: 12px; }
.plano-impacto { font-size: 13px; color: #f59e0b; font-weight: 500; margin-bottom: 10px; }
.plano-acao  { font-size: 13px; color: #555; padding: 4px 0; border-top: 1px solid #e0e6f0; }

/* ── Choque numbers ── */
.choque-grid { display: flex; gap: 16px; flex-wrap: wrap; margin: 20px 0; }
.choque-item {
    flex: 1; min-width: 200px;
    background: #f5f7fb; border: 1px solid #e0e6f0; border-radius: 12px;
    padding: 20px 18px;
}
.choque-icon  { font-size: 26px; margin-bottom: 8px; }
.choque-value { font-family: 'Inter', sans-serif; font-size: 28px; font-weight: 800; color: #FF4040; line-height: 1.1; }
.choque-label { font-size: 12px; color: #666; margin-top: 4px; line-height: 1.4; }

/* ── Tags ── */
.tag-demo    { display: inline-block; background: rgba(22,163,74,0.10); border: 1px solid rgba(22,163,74,0.3); color: #16a34a; font-size: 11px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; padding: 3px 10px; border-radius: 20px; margin-bottom: 12px; }
.tag-premium { display: inline-block; background: rgba(245,158,11,0.10); border: 1px solid rgba(245,158,11,0.3); color: #008000; font-size: 11px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; padding: 3px 10px; border-radius: 20px; margin-bottom: 12px; }

/* ── Streamlit misc overrides ── */
/* ── Esconder navegação automática do Streamlit ── */
[data-testid="stSidebarNav"] {
    display: none !important;
}
/* ── Esconder botão de colapsar sidebar ── */
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}
[data-testid="stMarkdownContainer"] > div > p,
[data-testid="stMarkdownContainer"] > div > li {
    color: #111111 !important;
}
.stTextInput input {
    background: #f5f7fb !important;
    border: 1px solid #c8d4e8 !important;
    color: #111 !important;
}
.stButton button {
    font-family: 'Inter', sans-serif !important;
}
</style>
"""

def inject_css():
    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

def _get_gspread_client():


    raw = os.environ.get("GOOGLE_CREDENTIALS")
    if raw:
        info = json.loads(raw)
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        return gspread.authorize(creds)
    else:
        return gspread.service_account(filename="credentials.json")


def render_sidebar(active: str = "home"):
    """Sidebar padrão com navegação + gate de acesso."""
    acesso = detectar_modo()

    with st.sidebar:

        # ── TOPO: Logo ───────────────────────────────────────────────
        st.markdown("""
        <div style="padding:20px 4px 16px;">
            <div style="font-family:'Inter',sans-serif;font-size:21px;
              font-weight:800;color:#2f5f98;line-height:1.1;">
                🍕 DeliveryPro
            </div>
            <div style="font-size:11px;color:#7a90b0;letter-spacing:1.4px;
              text-transform:uppercase;margin-top:4px;font-weight:500;">
                Hub de Soluções
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="height:1px;background:#e5e9f0;margin-bottom:16px;"></div>
        """, unsafe_allow_html=True)

        # ── UPLOAD ───────────────────────────────────────────────────
        st.markdown("""
        <div style="font-size:11px;font-weight:600;color:#7a90b0;
          text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
          📂 Dados do Cliente
        </div>""", unsafe_allow_html=True)

        # Indicador de dados reais vs mock
        if not st.session_state.get("is_mock", True):
            st.markdown("""
            <div style="background:#f0faf4;border:1px solid #a7d7b8;
              border-radius:8px;padding:10px 12px;margin-bottom:8px;">
              <div style="font-size:12px;color:#16a34a;font-weight:600;">
                ✅ Utilizando dados reais
              </div>
              <div style="font-size:11px;color:#5a7a6a;margin-top:2px;">
                Dados do cliente carregados com sucesso.
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="font-size:12px;color:#9aabb8;
              font-style:italic;padding:4px 0 8px;">
              Usando dados de demonstração.
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="height:1px;background:#e5e9f0;margin:14px 0 12px;"></div>
        """, unsafe_allow_html=True)

        # ── NAVEGAÇÃO ────────────────────────────────────────────────
        st.markdown("""
        <div style="font-size:11px;font-weight:600;color:#7a90b0;
          text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;text-align: center">
          Etapas
        </div>""", unsafe_allow_html=True)

        st.page_link("app.py",                   label="🏠  Visão Geral")
        st.page_link("pages/1_Operacao.py",      label="🚚  Operação")
        st.page_link("pages/2_Lucratividade.py", label="💰  Lucratividade")
        st.page_link("pages/3_Fidelizacao.py",   label="❤️  Fidelização")

        st.markdown("""
        <div style="height:1px;background:#e5e9f0;margin:14px auto 12px;"></div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:11px;font-weight:600;color:#7a90b0;
          text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;text-align: center">
          Planejamento
        </div>""", unsafe_allow_html=True)


        st.page_link("pages/4_Plano.py",     label="🧠  Plano de Crescimento")
        st.page_link("pages/5_Experimentos.py", label="⚗️  Experimentos")

        st.markdown("""
        <div style="height:1px;background:#e5e9f0;margin:14px 0 12px;"></div>
        """, unsafe_allow_html=True)

        # ── ACESSO ───────────────────────────────────────────────────
        if acesso["modo"] == "premium":
            if acesso.get("cliente"):
                # Cliente identificado — mostra badge e botão de sair
                nome = acesso["cliente"]
                st.markdown(f"""
                <div style="background:#f0faf4;border:1px solid #a7d7b8;
                  border-radius:8px;padding:10px 12px;">
                  <div style="font-size:11px;color:#16a34a;font-weight:600;
                    text-transform:uppercase;letter-spacing:1px;">
                    ✅ Acesso Premium
                  </div>
                  <div style="font-size:13px;color:#3a5a4a;
                    margin-top:2px;font-weight:500;">{nome}</div>
                </div>""", unsafe_allow_html=True)

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                if st.button("Sair", use_container_width=True, key="btn_sair"):
                    st.session_state["senha_digitada"] = ""
                    st.session_state.pop("df_main", None)
                    st.session_state.pop("is_mock", None)
                    st.session_state.pop("sheets_id_carregado", None)
                    st.query_params.clear()
                    st.rerun()

            else:
                # Visitante sem senha — mostra input de login
                st.markdown("""
                <div style="font-size:12px;color:#9aabb8;
                  font-style:italic;padding:4px 0 8px;">
                  Dados de demonstração ativos.
                </div>""", unsafe_allow_html=True)

                senha_input = st.text_input(
                    "Código de acesso", type="password",
                    placeholder="Digite seu código",
                    key="senha_input_sidebar",
                    label_visibility="collapsed",
                )
                if st.button("Acessar", use_container_width=True,
                             key="btn_acessar", type="tertiary"):
                    if senha_input:
                        if senha_input == SENHA_MASTER or senha_input in CLIENTES_PREMIUM:
                            st.session_state["senha_digitada"] = senha_input
                            st.session_state.pop("df_main", None)
                            st.session_state.pop("is_mock", None)
                            st.rerun()
                        else:
                            st.error("Acesso negado.")
                    else:
                        st.warning("Digite seu código de acesso.")

        # ── PAINEL MASTER ────────────────────────────────────────────
        if acesso["is_master"]:
            st.markdown("""
            <div style="height:1px;background:#e5e9f0;margin:14px 0 12px;"></div>
            <div style="font-size:11px;color:#2f5f98;font-weight:600;
              text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
              🔧 Painel Master
            </div>""", unsafe_allow_html=True)
            ajuste = st.text_area(
                "Observações para este cliente",
                key="ajuste_manual_master", height=120,
                placeholder="Ex: 'No seu caso, o Hamburguer Duplo representa 32% das vendas...'"
            )
            if ajuste:
                st.session_state["ajuste_manual"] = ajuste

    carregar_sessao(acesso)
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
    # Horas com distribuição realista: pico almoço (11-14h) e jantar (18-22h)
    horas_possiveis = (
        list(range(11, 15)) * 3 +   # almoço — peso 3
        list(range(18, 23)) * 5 +   # jantar — peso 5
        list(range(15, 18)) * 1     # tarde — peso 1
    )
    datas = sorted([
        hoje - timedelta(
            days=random.randint(0, 180),
            hours=-random.choice(horas_possiveis),
            minutes=-random.randint(0, 59)
        )
        for _ in range(n_pedidos)
    ])
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

    # Suporta tanto "Taxa iFood" (Sheets) quanto "Comissão iFood" (CSV)
    if "Taxa iFood" in df.columns:
        comissao = ok["Taxa iFood"].sum()
    elif "Comissão iFood" in df.columns:
        comissao = ok["Comissão iFood"].sum()
    else:
        comissao = 0

    liq = fat - comissao

    # Ticket médio por pedido (não por linha/item)
    ticket = (
        ok.groupby("ID do Pedido")["Valor Bruto"].sum().mean()
        if "ID do Pedido" in ok.columns and len(ok) else
        (ok["Valor Bruto"].mean() if len(ok) else 0)
    )

    return {
        "faturamento":         fat,
        "receita_liquida":     liq,
        "ticket_medio":        ticket,
        "total_pedidos":       ok["ID do Pedido"].nunique() if "ID do Pedido" in ok.columns else len(ok),
        "taxa_cancelamento":   len(can) / len(df) * 100 if len(df) else 0,
        "comissao_total":      comissao,
        "perda_cancelamentos": can["Valor Bruto"].sum(),
    }


# ─────────────────────────────────────────────
#  CHOQUE DE REALIDADE
# ─────────────────────────────────────────────

def calcular_choque(df: pd.DataFrame, dias_churn: int = 30) -> dict:
    ok = df[~df["is_cancelado"]].copy()

    # Itens-problema
    item_s = (ok.groupby("Nome do Item")
               .agg(vendas=("Nome do Item","count"), receita=("Valor dos Itens","sum"))
               .reset_index())
    cardapio_ativo = st.session_state.get("cardapio", {})
    item_s["margem"] = item_s["Nome do Item"].apply(
        lambda n: cardapio_ativo[n]["margem"]
        if n in cardapio_ativo
        else (ITENS_CARDAPIO[n]["preco"]-ITENS_CARDAPIO[n]["custo"])/ITENS_CARDAPIO[n]["preco"]
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
    inativos   = cli[cli["dias_inativo"] > dias_churn]
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
 
 
def gerar_plano_automatico(df: pd.DataFrame, config: dict = None, cardapio: dict = None) -> dict:
    if config is None:
        config = {}
    if cardapio is None:
        cardapio = {}
    

    ok          = df[~df["is_cancelado"]].copy()
    dias_churn  = int(config.get("churn", 30))
    margem_proxy = float(config.get("margem_proxy", MARGEM_PROXY))

    hoje   = ok["Data do Pedido"].max()
    dias   = max((hoje - ok["Data do Pedido"].min()).days, 1)
    fator  = 30 / dias
    n_semanas = max(dias // 7, 1)

    # Fallback se histórico curto
    historico_curto = n_semanas < 8

    ok["Semana"] = ok["Data do Pedido"].dt.to_period("W")

    problemas = []


    # ── helper σ ─────────────────────────────────────────────────────────
    def sigma_oportunidade(serie: pd.Series, atual_real=None):
        """Retorna (media, std, pico, atual, gap)
        atual_real: valor calculado do período completo (preferido sobre iloc[-1])
        """
        media = serie.mean()
        std   = serie.std() if len(serie) > 1 else 0
        pico  = media + std
        atual = atual_real if atual_real is not None else serie.iloc[-1]
        gap   = max(pico - atual, 0)
        return media, std, pico, atual, gap

    # ─────────────────────────────────────────────────────────────────────
    # 1. TICKET MÉDIO SEMANAL
    # ─────────────────────────────────────────────────────────────────────
    ticket_sem = (
        ok.groupby(["Semana", "ID do Pedido"])["Valor Bruto"].sum()
        .reset_index()
        .groupby("Semana")["Valor Bruto"].mean()
        if "ID do Pedido" in ok.columns
        else ok.groupby("Semana")["Valor Bruto"].mean()
    )
    # atual_real = ticket médio do período completo
    ticket_atual_real = (
        ok.groupby("ID do Pedido")["Valor Bruto"].sum().mean()
        if "ID do Pedido" in ok.columns
        else ok["Valor Bruto"].mean()
    )

    if len(ticket_sem) >= 3:
        media_tk, std_tk, pico_tk, atual_tk, gap_tk = sigma_oportunidade(serie=ticket_sem, atual_real=ticket_atual_real)
        pedidos_mes = ok.groupby("Semana").size().mean() * 4
        impacto_tk  = gap_tk * pedidos_mes

        if gap_tk > 0.5 and impacto_tk > 100:
            problemas.append({
                "categoria":  "🎫 Ticket Médio",
                "titulo":     f"Ticket médio caiu para R$ {atual_tk:.2f} — potencial de R$ {pico_tk:.2f}",
                "descricao":  f"No seu melhor período recente, o ticket médio chegou a R$ {pico_tk:.2f}. Hoje está em R$ {atual_tk:.2f}. Clientes estão pedindo menos itens por pedido.",
                "raciocinio": f"Média histórica: R$ {media_tk:.2f} ± R$ {std_tk:.2f}. Gap de R$ {gap_tk:.2f} × ~{pedidos_mes:.0f} pedidos/mês = R$ {impacto_tk:.0f} de oportunidade.",
                "impacto_r":  impacto_tk,
                "confianca":  "media" if historico_curto else "alta",
                "acoes": [
                    f"Criar combo ou sugestão de adicional para aumentar o ticket em R$ {gap_tk*0.5:.2f} por pedido.",
                    f"Revisar se algum item de alto ticket saiu do cardápio recentemente.",
                    f"Ativar 'peça também' no iFood com itens complementares aos mais vendidos.",
                ],
                "prioridade": 1 if gap_tk / media_tk > 0.15 else 2,
            })

    # ─────────────────────────────────────────────────────────────────────
    # 2. TAXA DE CANCELAMENTO SEMANAL
    # ─────────────────────────────────────────────────────────────────────
    cancel_sem = df.groupby(df["Data do Pedido"].dt.to_period("W")).apply(
        lambda x: x["is_cancelado"].sum() / len(x) * 100
    )
    media_ca = std_ca = atual_ca = meta_ca = gap_ca = None
    cancel_atual_real = df["is_cancelado"].sum() / len(df) * 100 if len(df) else 0
    if len(cancel_sem) >= 3:
        media_ca, std_ca, _, atual_ca, _ = sigma_oportunidade(cancel_sem, atual_real=cancel_atual_real)
        # Aqui "gap" é inverso — queremos baixo cancelamento
        # pico ruim = média + 1σ; bom = média - 1σ
        meta_ca  = max(media_ca - std_ca, 0)
        gap_ca   = max(atual_ca - meta_ca, 0)

        if gap_ca > 1.0:
            ticket_med   = ok["Valor Bruto"].mean()
            pedidos_total = len(df)
            cancel_evit  = round(pedidos_total * (gap_ca / 100) * 0.35, 0)
            impacto_ca   = cancel_evit * ticket_med * fator

            problemas.append({
                "categoria":  "🚚 Operação",
                "titulo":     f"Cancelamento em {atual_ca:.1f}% — acima do seu próprio histórico",
                "descricao":  f"No seu melhor período, a taxa de cancelamento ficou em {meta_ca:.1f}%. Hoje está em {atual_ca:.1f}%. Cada ponto percentual a mais representa pedidos perdidos.",
                "raciocinio": f"Gap de {gap_ca:.1f}pp × {pedidos_total} pedidos × 35% evitáveis × R$ {ticket_med:.0f} ticket = R$ {impacto_ca:.0f}/mês.",
                "impacto_r":  impacto_ca,
                "confianca":  "media" if historico_curto else "alta",
                "acoes": [
                    "Identificar se cancelamentos concentram em horário ou bairro específico (ver aba Operação).",
                    "Verificar itens que aparecem com frequência em pedidos cancelados.",
                    "Ativar confirmação automática de pedido no iFood — reduz desistência.",
                ],
                "prioridade": 1 if gap_ca > 5 else 2,
            })

    # ─────────────────────────────────────────────────────────────────────
    # 3. TEMPO DE ENTREGA SEMANAL
    # ─────────────────────────────────────────────────────────────────────
    if "Tempo de Entrega (min)" in ok.columns:
        tempo_sem = ok.groupby("Semana")["Tempo de Entrega (min)"].mean()
        media_te = std_te = atual_te = meta_te = gap_te = None
        tempo_sem = pd.Series(dtype=float)
        tempo_atual_real = ok["Tempo de Entrega (min)"].mean()
        if len(tempo_sem) >= 3:
            media_te, std_te, _, atual_te, _ = sigma_oportunidade(tempo_sem, atual_real=tempo_atual_real)
            meta_te = max(media_te - std_te, 20)
            gap_te  = max(atual_te - meta_te, 0)

            if gap_te > 3:
                impacto_te = len(df[df["is_cancelado"]]) * 0.3 * ok["Valor Bruto"].mean() * fator

                problemas.append({
                    "categoria":  "🚚 Operação",
                    "titulo":     f"Tempo de entrega em {atual_te:.0f} min — {gap_te:.0f} min acima do seu melhor",
                    "descricao":  f"Você já entregou com média de {meta_te:.0f} min. Hoje está em {atual_te:.0f} min. Entregas mais lentas aumentam cancelamentos e reduzem avaliação.",
                    "raciocinio": f"Média histórica: {media_te:.0f} min ± {std_te:.0f} min. Gap de {gap_te:.0f} min — recuperar esse nível pode evitar ~30% dos cancelamentos atuais.",
                    "impacto_r":  impacto_te,
                    "confianca":  "media",
                    "acoes": [
                        f"Revisar raio de entrega nos bairros com maior tempo médio.",
                        f"Verificar cobertura de motoboys nos horários de pico.",
                        f"Considerar taxa extra para bairros acima de 6 km.",
                    ],
                    "prioridade": 1 if gap_te > 10 else 2,
                })

    # ─────────────────────────────────────────────────────────────────────
    # 4. TEMPO ENTRE COMPRAS (proxy churn)
    # ─────────────────────────────────────────────────────────────────────
    cli = (ok.groupby("ID do Cliente")
             .agg(primeiro=("Data do Pedido","min"),
                  ultimo  =("Data do Pedido","max"),
                  pedidos =("ID do Pedido",  "count"))
             .reset_index())
    cli_recorrentes = cli[cli["pedidos"] > 1].copy()

    if len(cli_recorrentes) >= 10:
        cli_recorrentes["intervalo"] = (
            (cli_recorrentes["ultimo"] - cli_recorrentes["primeiro"]).dt.days
            / (cli_recorrentes["pedidos"] - 1)
        )
        # Série semanal: mediana do intervalo dos clientes com último pedido naquela semana
        ok2 = ok.merge(cli_recorrentes[["ID do Cliente","intervalo"]], on="ID do Cliente", how="inner")
        intervalo_sem = ok2.groupby("Semana")["intervalo"].median()

        media_iv = std_iv = atual_iv = meta_iv = gap_iv = None
        intervalo_sem = pd.Series(dtype=float)

        intervalo_atual_real = cli_recorrentes["intervalo"].median() if len(cli_recorrentes) > 0 else None
        if len(intervalo_sem) >= 3:
            media_iv, std_iv, _, atual_iv, _ = sigma_oportunidade(intervalo_sem, atual_real=intervalo_atual_real)
            meta_iv = max(media_iv - std_iv, 1)
            gap_iv  = max(atual_iv - meta_iv, 0)

            if gap_iv > 2:
                ticket_med   = ok["Valor Bruto"].mean()
                n_recorrentes = len(cli_recorrentes)
                pedidos_extras = n_recorrentes * (gap_iv / max(atual_iv, 1))
                impacto_iv    = pedidos_extras * ticket_med * fator

                problemas.append({
                    "categoria":  "❤️ Fidelização",
                    "titulo":     f"Clientes voltando a cada {atual_iv:.0f} dias — antes eram {meta_iv:.0f} dias",
                    "descricao":  f"O intervalo médio entre compras dos clientes recorrentes aumentou {gap_iv:.0f} dias. Eles estão comprando com menos frequência — sinal de churn gradual.",
                    "raciocinio": f"Gap de {gap_iv:.0f} dias × {n_recorrentes} clientes recorrentes = ~{pedidos_extras:.0f} pedidos/mês não realizados × R$ {ticket_med:.0f} = R$ {impacto_iv:.0f}.",
                    "impacto_r":  impacto_iv,
                    "confianca":  "media" if historico_curto else "alta",
                    "acoes": [
                        f"Campanha de reativação para clientes sem pedido há mais de {dias_churn} dias.",
                        f"Criar programa de fidelidade simples — 'na 5ª compra, ganhe X'.",
                        f"Verificar se mudança no cardápio ou preço coincide com o aumento do intervalo.",
                    ],
                    "prioridade": 1 if gap_iv > 7 else 2,
                })

    # ─────────────────────────────────────────────────────────────────────
    # 5. CLIENTES ATIVOS %
    # ─────────────────────────────────────────────────────────────────────
    ativos_sem = ok.groupby("Semana").apply(
        lambda x: x["ID do Cliente"].nunique()
    )
    total_cli = ok["ID do Cliente"].nunique()
    pct_ativos_sem = ativos_sem / total_cli * 100
    media_at = std_at = pico_at = atual_at = gap_at = None
    hoje_real = ok["Data do Pedido"].max()
    cli_todos = ok.groupby("ID do Cliente")["Data do Pedido"].max().reset_index()
    cli_todos["dias"] = (hoje_real - cli_todos["Data do Pedido"]).dt.days
    ativos_atual_real = (cli_todos["dias"] <= dias_churn).sum() / len(cli_todos) * 100 if len(cli_todos) else 0

    if len(ativos_sem) >= 3:
        media_at, std_at, pico_at, atual_at, gap_at = sigma_oportunidade(pct_ativos_sem, atual_real=ativos_atual_real)

        if gap_at > 2:
            cli_gap    = round(total_cli * gap_at / 100, 0)
            ticket_med = (
                ok.groupby("ID do Pedido")["Valor Bruto"].sum().mean()
                if "ID do Pedido" in ok.columns
                else ok["Valor Bruto"].mean()
            )
            impacto_at = cli_gap * ticket_med * fator

            problemas.append({
                "categoria":  "❤️ Fidelização",
                "titulo":     f"Base ativa caiu para {atual_at:.1f}% — já foi {pico_at:.1f}%",
                "descricao":  f"No seu melhor período, {pico_at:.1f}% da base de clientes estava ativa. Hoje só {atual_at:.1f}% pediu recentemente. São ~{cli_gap:.0f} clientes que sumiram.",
                "raciocinio": f"Gap de {gap_at:.1f}pp × {total_cli} clientes = {cli_gap:.0f} clientes × R$ {ticket_med:.0f} ticket = R$ {impacto_at:.0f}/mês.",
                "impacto_r":  impacto_at,
                "confianca":  "media" if historico_curto else "alta",
                "acoes": [
                    f"Identificar os {int(cli_gap)} clientes inativos de maior ticket histórico para abordagem prioritária.",
                    f"Criar cupom exclusivo para clientes sem pedido há mais de {dias_churn} dias.",
                    f"Revisar se houve mudança de preço ou cardápio que coincide com a queda.",
                ],
                "prioridade": 1 if gap_at > 10 else 2,
            })

    # ─────────────────────────────────────────────────────────────────────
    # 6. PRODUTOS INDIVIDUAIS
    # ─────────────────────────────────────────────────────────────────────
    item_sem = (ok.groupby(["Semana","Nome do Item"])
                  .size()
                  .reset_index(name="vendas"))

    itens_lista = []
    for item, grp in item_sem.groupby("Nome do Item"):
        if len(grp) < 3:
            continue

        serie = grp.set_index("Semana")["vendas"]
        # atual_real = volume médio semanal do período completo (total / semanas)
        total_vendas_item = ok[ok["Nome do Item"] == item].shape[0]
        atual_real_it     = total_vendas_item / n_semanas
        media_it, std_it, pico_it, atual_it, gap_it = sigma_oportunidade(serie, atual_real=atual_real_it)

        if gap_it < 1:
            continue

        # Margem: real do cardápio ou proxy
        if item in cardapio:
            margem_r  = cardapio[item]["margem"]
            ticket_it = cardapio[item]["preco"]
            tem_real  = True
        else:
            margem_r  = margem_proxy
            ticket_it = ok[ok["Nome do Item"] == item]["Valor Bruto"].mean()
            tem_real  = False

        margem_R   = ticket_it * margem_r          # margem em R$ por unidade
        impacto_it = gap_it * margem_R * 4         # gap semanal × 4 semanas

        itens_lista.append({
            "item":      item,
            "gap":       gap_it,
            "pico":      pico_it,
            "atual":     atual_it,
            "margem_r":  margem_R,
            "impacto":   impacto_it,
            "tem_real":  tem_real,
        })

    itens_lista.sort(key=lambda x: -x["impacto"])

    for it in itens_lista[:3]:
        problemas.append({
            "categoria":  "📦 Produto",
            "titulo":     f"{it['item']} — vendendo {it['atual']:.0f}/sem, já vendeu {it['pico']:.0f}/sem",
            "descricao":  f"Volume atual está {it['gap']:.0f} unidades/semana abaixo do pico histórico. Recuperar esse volume vale R$ {it['impacto']:.0f}/mês.",
            "raciocinio": f"Gap de {it['gap']:.1f} un/sem × R$ {it['margem_r']:.2f} margem × 4 semanas = R$ {it['impacto']:.0f}. Margem {'real do cardápio' if it['tem_real'] else 'estimada por proxy'}.",
            "impacto_r":  it["impacto"],
            "confianca":  "alta" if it["tem_real"] else "media",
            "acoes": [
                f"Destacar {it['item']} com foto atualizada e descrição no iFood.",
                f"Testar promoção relâmpago em horário de baixo volume para reativar demanda.",
                f"Verificar se houve mudança de preço ou ingrediente que coincide com a queda.",
            ],
            "prioridade": 1 if it["impacto"] > 300 else 2,
        })
        


    # ─────────────────────────────────────────────────────────────────────
    # 7. VAZAMENTO DE LUCRATIVIDADE (itens com margem abaixo da mediana)
    # ─────────────────────────────────────────────────────────────────────
    item_stats = (
        ok.groupby("Nome do Item")
        .agg(vendas=("Nome do Item", "count"), receita=("Valor dos Itens", "sum"))
        .reset_index()
    )
    item_stats["margem"] = item_stats["Nome do Item"].apply(
        lambda n: cardapio[n]["margem"]
        if n in cardapio
        else (ITENS_CARDAPIO[n]["preco"] - ITENS_CARDAPIO[n]["custo"]) / ITENS_CARDAPIO[n]["preco"]
        if n in ITENS_CARDAPIO else margem_proxy
    )
    med_v_luc = item_stats["vendas"].median()
    med_m_luc = item_stats["margem"].median()

    cavalos = item_stats[
        (item_stats["vendas"] >= med_v_luc) & (item_stats["margem"] < med_m_luc)
    ]
    vazamento = (cavalos["receita"] * (med_m_luc - cavalos["margem"])).sum()
    vazamento = max(vazamento, 0)

    if vazamento > 200 and len(cavalos) > 0:
        top_cavalos = cavalos.nlargest(3, "receita")["Nome do Item"].tolist()
        nomes_fmt = ", ".join(top_cavalos)
        margem_med_pct = med_m_luc * 100

        problemas.append({
            "categoria":  "💰 Lucratividade",
            "titulo":     f"R$ {vazamento:,.0f} em lucro não realizado por margem baixa no cardápio".replace(",", "."),
            "descricao":  (
                f"{len(cavalos)} item(ns) com alto volume mas margem abaixo da mediana "
                f"({margem_med_pct:.0f}%): {nomes_fmt}. "
                f"Esses itens vendem bem mas comprimem sua margem. "
                f"Pequenos ajustes de preço ou custo convertem diretamente em lucro."
            ),
            "raciocinio": (
                f"Para cada item: receita_item × (margem_mediana − margem_item). "
                f"Soma dos {len(cavalos)} itens-problema = R$ {vazamento:,.0f} no período "
                f"({dias} dias). Impacto mensal = valor do período × fator ({fator:.2f}).".replace(",", ".")
            ),
            "impacto_r":  vazamento * fator,
            "confianca":  "alta" if cardapio else "media",
            "acoes": [
                f"Revisar preço de {top_cavalos[0]}: aumento de 8–12% provavelmente não reduz volume.",
                f"Verificar se custo dos insumos subiu sem repasse ao preço de venda.",
                f"Considerar criar versão premium do item mais vendido para elevar margem média.",
            ],
            "prioridade": 1 if vazamento * fator > 500 else 2,
        })

    # ─────────────────────────────────────────────────────────────────────
    # Ranking final
    # ─────────────────────────────────────────────────────────────────────
    problemas.sort(key=lambda x: (x["prioridade"], -x["impacto_r"]))

    impacto_total = sum(p["impacto_r"] for p in problemas)

    return {
        "problemas":           problemas,
        "impacto_mensal_low":  max(impacto_total * 0.65, 0),
        "impacto_mensal_high": max(impacto_total * 1.10, 0),
        "n_problemas":         len(problemas),
        # dados brutos para a página de experimentos
        "metricas": {
            "ticket_medio": {
                "serie":  ticket_sem.to_dict()       if len(ticket_sem) >= 3 else {},
                "atual":  atual_tk                   if len(ticket_sem) >= 3 else None,
                "pico":   pico_tk                    if len(ticket_sem) >= 3 else None,
                "media":  media_tk                   if len(ticket_sem) >= 3 else None,
                "std":    std_tk                     if len(ticket_sem) >= 3 else None,
            },
            "cancelamento": {
                "serie":  cancel_sem.to_dict()       if len(cancel_sem) >= 3 else {},
                "atual":  atual_ca                   if len(cancel_sem) >= 3 else None,
                "meta":   meta_ca                    if len(cancel_sem) >= 3 else None,
                "media":  media_ca                   if len(cancel_sem) >= 3 else None,
                "std":    std_ca                     if len(cancel_sem) >= 3 else None,
            },
            "tempo_entrega": {
                "serie":  tempo_sem.to_dict()        if "Tempo de Entrega (min)" in ok.columns and len(tempo_sem) >= 3 else {},
                "atual":  atual_te                   if "Tempo de Entrega (min)" in ok.columns and len(tempo_sem) >= 3 else None,
                "meta":   meta_te                    if "Tempo de Entrega (min)" in ok.columns and len(tempo_sem) >= 3 else None,
            },
            "intervalo_compras": {
                "serie":  intervalo_sem.to_dict()    if len(cli_recorrentes) >= 10 and len(intervalo_sem) >= 3 else {},
                "atual":  atual_iv                   if len(cli_recorrentes) >= 10 and len(intervalo_sem) >= 3 else None,
                "meta":   meta_iv                    if len(cli_recorrentes) >= 10 and len(intervalo_sem) >= 3 else None,
            },
            "clientes_ativos_pct": {
                "serie":  pct_ativos_sem.to_dict()   if len(ativos_sem) >= 3 else {},
                "atual":  atual_at                   if len(ativos_sem) >= 3 else None,
                "pico":   pico_at                    if len(ativos_sem) >= 3 else None,
            },
            "produtos": {
                it["item"]: it for it in itens_lista
            },
        }
    }


# ─────────────────────────────────────────────
#  GOOGLE SHEETS — leitura de dados do cliente
# ─────────────────────────────────────────────

def _limpar_valor_monetario(val) -> float:
    """Remove R$, pontos e vírgulas e converte para float."""
    if pd.isna(val) or str(val).strip() == "":
        return 0.0
    s = str(val).replace("R$", "").replace(" ", "").strip()
    # Formato brasileiro: 1.234,56 → tem vírgula como decimal
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    # Formato americano: 32.00 → já está correto, não mexe
    return float(s)


def _limpar_float(val) -> float:
    """Converte string com vírgula decimal para float."""
    if pd.isna(val) or str(val).strip() == "":
        return 0.0
    return float(str(val).replace(",", ".").strip())


def carregar_sessao(acesso: dict):
    """
    Carrega (ou recarrega) os dados do cliente no session_state.
    Deve ser chamada em todas as páginas logo após render_sidebar.
    """
    sheets_id = acesso.get("sheets_id")
    ja_carregado = st.session_state.get("sheets_id_carregado")

    if sheets_id and sheets_id != ja_carregado:
        # Novo cliente ou primeiro carregamento — busca do Sheets
        df_sheets    = carregar_pedidos_sheets(sheets_id)
        dados_cliente = carregar_dados_cliente(sheets_id)
        st.session_state["df_main"]  = df_sheets if df_sheets is not None else process_ifood_data(generate_mock_ifood_data(800))
        st.session_state["is_mock"]  = df_sheets is None
        st.session_state["config"]   = dados_cliente.get("config", {})
        st.session_state["cardapio"] = dados_cliente.get("cardapio", {})
        st.session_state["sheets_id_carregado"] = sheets_id

    elif not sheets_id and "df_main" not in st.session_state:
        # Visitante sem senha e sem dados — inicializa mock
        st.session_state["df_main"]  = process_ifood_data(generate_mock_ifood_data(800))
        st.session_state["is_mock"]  = True
        st.session_state["config"]   = {}
        st.session_state["cardapio"] = {}


def carregar_dados_cliente(sheets_id: str) -> dict:
    """
    Lê todas as abas da planilha do cliente no Google Sheets.
    Retorna dict com: config, cardapio, intervencoes, ganhos, notas.
    Em caso de erro em qualquer aba, retorna dados parciais sem quebrar.
    """
    try:
        import gspread
    except ImportError:
        st.warning("Biblioteca gspread não instalada. Rode: pip install gspread")
        return {}

    try:
        gc = _get_gspread_client()
        planilha = gc.open_by_key(sheets_id)
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Sheets: {e}")
        return {}

    resultado = {}

    # ── 1. Config ────────────────────────────────────────────────────────
    try:
        df_cfg = pd.DataFrame(planilha.worksheet("config").get_all_records())
        config = dict(zip(df_cfg["chave"], df_cfg["valor"]))
        config["margem_proxy"]        = _limpar_float(config.get("margem_proxy", 0.30))
        config["dias_inativo"]        = int(config.get("dias_inativo", 30))
        config["churn"]               = int(config.get("churn", 30))
        config["investimento_mensal"] = _limpar_float(config.get("investimento_mensal", 0))
        resultado["config"] = config
    except Exception as e:
        resultado["config"] = {}
        st.warning(f"Aba 'config' com erro: {e}")

    # ── 2. Cardápio ──────────────────────────────────────────────────────
    try:
        df_card = pd.DataFrame(planilha.worksheet("cardapio").get_all_records())
        df_card["custo"] = df_card["custo"].apply(_limpar_valor_monetario)
        df_card["preco"] = df_card["preco"].apply(_limpar_valor_monetario)
        df_card = df_card[df_card["ativo"].str.lower().str.strip() == "sim"].copy()
        df_card["margem"] = (
            (df_card["preco"] - df_card["custo"]) / df_card["preco"]
        ).round(4)
        cardapio_dict = {
            row["item"].strip(): {
                "custo":     row["custo"],
                "preco":     row["preco"],
                "margem":    row["margem"],
                "categoria": row.get("categoria", ""),
            }
            for _, row in df_card.iterrows()
            if row["preco"] > 0
        }
        resultado["cardapio"]    = cardapio_dict
        resultado["cardapio_df"] = df_card
    except Exception as e:
        resultado["cardapio"]    = {}
        resultado["cardapio_df"] = pd.DataFrame()
        st.warning(f"Aba 'cardapio' com erro: {e}")


    return resultado


# ─────────────────────────────────────────────
#  GOOGLE SHEETS — experimentos
# ─────────────────────────────────────────────

def salvar_experimento_sheets(sheets_id: str, exp: dict) -> bool:
    """
    Grava (ou atualiza) o experimento ativo na aba 'experimentos' do Sheets.
    Procura por uma linha com status='ativo' e sobrescreve; se não existir, append.
    Retorna True em sucesso.
    """
    try:
        import gspread, json
    except ImportError:
        st.warning("gspread não instalado.")
        return False

    try:
        gc       = _get_gspread_client()
        planilha = gc.open_by_key(sheets_id)
        ws       = planilha.worksheet("experimentos")
    except Exception as e:
        st.error(f"Erro ao conectar ao Sheets: {e}")
        return False

    # Monta o payload — serializa campos complexos como JSON
    def _ser(v):
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(v, dict) or isinstance(v, list):
            return json.dumps(v, ensure_ascii=False)
        return str(v) if v is not None else ""

    nova_linha = [
        exp.get("id", ""),                          # id
        exp.get("tipo_acao", ""),                   # acao
        exp.get("item", "") or "",                  # item
        exp.get("baseline_atual", ""),              # parametro_antes
        exp.get("baseline_alvo", ""),               # parametro_depois
        _ser(exp.get("data_inicio")),               # data_inicio
        "",                                         # data_fim
        "ativo",                                    # status
        "",                                         # baseline_volume  (reservado)
        "",                                         # baseline_margem  (reservado)
        _ser(exp.get("problema", {})),              # conclusao → reutilizamos para guardar o blob do problema
        exp.get("chave_primaria", ""),              # coluna extra: chave_primaria
        exp.get("label_primaria", ""),              # coluna extra: label_primaria
        _ser(exp.get("guardrails", [])),            # coluna extra: guardrails
        str(exp.get("impacto", "")),                # coluna extra: impacto
        exp.get("raciocinio", ""),                  # coluna extra: raciocinio
    ]

    try:
        todas = ws.get_all_values()
        headers = todas[0] if todas else []
        # Procura linha ativa existente para sobrescrever
        for i, row in enumerate(todas[1:], start=2):
            status_col = 7  # índice 0-based = coluna H = índice 7
            if len(row) > status_col and row[status_col].strip().lower() == "ativo":
                # Atualiza a linha inteira
                ws.update(f"A{i}:{chr(64+len(nova_linha))}{i}", [nova_linha])
                return True
        # Não encontrou → append
        ws.append_row(nova_linha, value_input_option="RAW")
        return True
    except Exception as e:
        st.error(f"Erro ao salvar experimento: {e}")
        return False


def encerrar_experimento_sheets(sheets_id: str) -> bool:
    """
    Marca a linha com status='ativo' como 'encerrado' e preenche data_fim.
    """
    try:
        import gspread
    except ImportError:
        return False

    try:
        gc       = _get_gspread_client()
        planilha = gc.open_by_key(sheets_id)
        ws       = planilha.worksheet("experimentos")
        todas    = ws.get_all_values()
    except Exception as e:
        st.error(f"Erro ao conectar ao Sheets: {e}")
        return False

    for i, row in enumerate(todas[1:], start=2):
        if len(row) > 7 and row[7].strip().lower() == "ativo":
            ws.update(f"G{i}", [[pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")]])  # data_fim
            ws.update(f"H{i}", [["encerrado"]])                                        # status
            return True
    return False


def carregar_experimento_ativo_sheets(sheets_id: str) -> dict | None:
    """
    Lê a aba 'experimentos' e retorna o dict do experimento com status='ativo',
    no mesmo formato que session_state['experimento_ativo']. Retorna None se não houver.
    """
    try:
        import gspread, json
    except ImportError:
        return None

    try:
        gc       = _get_gspread_client()
        planilha = gc.open_by_key(sheets_id)
        ws       = planilha.worksheet("experimentos")
        todas    = ws.get_all_values()
    except Exception:
        return None

    if len(todas) < 2:
        return None

    for row in todas[1:]:
        # Garante tamanho mínimo
        while len(row) < 16:
            row.append("")

        status = row[7].strip().lower()
        if status != "ativo":
            continue

        # Desserializa o blob do problema
        try:
            problema = json.loads(row[10]) if row[10] else {}
        except Exception:
            problema = {}

        try:
            guardrails = json.loads(row[13]) if row[13] else []
        except Exception:
            guardrails = []

        try:
            data_inicio = pd.Timestamp(row[5])
        except Exception:
            data_inicio = pd.Timestamp.now()

        return {
            "id":             row[0],
            "tipo_acao":      row[1],
            "item":           row[2] or None,
            "baseline_atual": row[3],
            "baseline_alvo":  row[4],
            "data_inicio":    data_inicio,
            "chave_primaria": row[11],
            "label_primaria": row[12],
            "guardrails":     guardrails,
            "impacto":        float(row[14]) if row[14] else 0,
            "raciocinio":     row[15],
            "problema":       problema,
        }

    return None


def carregar_pedidos_sheets(sheets_id: str) -> pd.DataFrame | None:
    """
    Lê a aba 'pedidos' da planilha do cliente e retorna
    um DataFrame no mesmo formato de process_ifood_data.
    Retorna None se a aba estiver vazia ou ocorrer erro.
    """
    try:
        import gspread
    except ImportError:
        st.warning("Biblioteca gspread não instalada. Rode: pip install gspread")
        return None

    try:
        gc       = _get_gspread_client()
        planilha = gc.open_by_key(sheets_id)
        rows     = planilha.worksheet("pedidos").get_all_values()
        print(f"DEBUG get_all_values: {len(rows)} linhas lidas")
        headers  = rows[0]
        # Remove colunas sem cabeçalho
        cols_validas = [i for i, h in enumerate(headers) if h.strip() != ""]
        headers  = [headers[i] for i in cols_validas]
        data     = [[row[i] for i in cols_validas] for row in rows[1:]]
        df       = pd.DataFrame(data, columns=headers)
        print(f"DEBUG df antes agregação: {len(df)} linhas | data max raw: {df['Data do Pedido'].max()}")
    except Exception as e:
        st.error(f"Erro ao ler aba 'pedidos': {e}")
        return None

    if df.empty:
            return None

    # Conta itens por pedido antes de agregar
    itens_por_pedido = df.groupby("ID do Pedido")["Nome do Item"].count().rename("Qtd Itens")

    # Garantir tipos corretos
    # Combina data + hora se existirem separados, senão usa só a data
    if "Hora" in df.columns:
        df["Data do Pedido"] = pd.to_datetime(
            df["Data do Pedido"].astype(str) + " " + df["Hora"].astype(str),
            dayfirst=True, errors="coerce"
        )
    else:
        df["Data do Pedido"] = pd.to_datetime(df["Data do Pedido"], dayfirst=True, errors="coerce")
    df["Hora"] = df["Data do Pedido"].dt.hour
    df["Valor Bruto"]            = df["Valor Bruto"].apply(_limpar_valor_monetario)
    df["Valor dos Itens"]        = df["Valor dos Itens"].apply(_limpar_valor_monetario)
    df["Comissão iFood"]         = df["Comissão iFood"].apply(_limpar_valor_monetario)
    df["Taxa de Entrega"]        = df["Taxa de Entrega"].apply(_limpar_valor_monetario)
    df["Tempo de Entrega (min)"] = pd.to_numeric(df["Tempo de Entrega (min)"], errors="coerce").fillna(0)
    df["Distância (km)"]         = pd.to_numeric(df["Distância (km)"], errors="coerce").fillna(0)
    df["lat"]                    = df["lat"].apply(_limpar_valor_monetario)
    df["lon"]                    = df["lon"].apply(_limpar_valor_monetario)

    # Agregar para 1 linha por pedido (mesmo formato do mock)
    df = (
        df.groupby("ID do Pedido", as_index=False)
        .agg(
            **{
                "Data do Pedido":         ("Data do Pedido",         "first"),
                "ID do Cliente":          ("ID do Cliente",          "first"),
                "Status":                 ("Status",                 "first"),
                "Nome do Item":           ("Nome do Item",           "first"),
                "Valor Bruto":            ("Valor Bruto",            "sum"),
                "Valor dos Itens":        ("Valor dos Itens",        "sum"),
                "Comissão iFood":         ("Comissão iFood",         "sum"),
                "Tempo de Entrega (min)": ("Tempo de Entrega (min)", "first"),
                "Taxa de Entrega":        ("Taxa de Entrega",        "first"),
                "Bairro":                 ("Bairro",                 "first"),
                "Distância (km)":         ("Distância (km)",         "first"),
                "lat":                    ("lat",                    "first"),
                "lon":                    ("lon",                    "first"),
                "Hora":                   ("Hora",                   "first"),
            }
        )
        .merge(itens_por_pedido, on="ID do Pedido", how="left")
    )
    df["is_cancelado"] = df["Status"].str.strip().str.lower().str.contains("cancel").fillna(False)
    df["Dia Semana"]   = df["Data do Pedido"].dt.day_name()
    print(f"DEBUG df após agregação: {len(df)} linhas | data max: {df['Data do Pedido'].max()}")

    return df