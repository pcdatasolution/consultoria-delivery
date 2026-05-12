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
    "burger123": {"nome": "Burguer do João",        "sheets_id": "1fonnx8d9zbdTtGLIy__jv9P2atycuIFT82bjaOm0jfc"},
    "pizza456":  {"nome": "Pizzaria Bella Napoli",  "sheets_id": ""},
    "frango789": {"nome": "Frango Assado do Zé",    "sheets_id": ""},
    "demo_full": {"nome": "Demo Interna",           "sheets_id": ""},
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

        # Se já tem dados enviados, mostra badge e botão para limpar
        if not st.session_state.get("is_mock", True):
            st.markdown("""
            <div style="background:#f0faf4;border:1px solid #a7d7b8;
              border-radius:8px;padding:10px 12px;margin-bottom:8px;">
              <div style="font-size:12px;color:#16a34a;font-weight:600;">
                ✅ Utilizando dados enviados
              </div>
              <div style="font-size:11px;color:#5a7a6a;margin-top:2px;">
                Dados do cliente carregados com sucesso.
              </div>
            </div>""", unsafe_allow_html=True)

            if st.button("🔄 Usar dados de demonstração",
                         use_container_width=True, key="btn_limpar_dados"):
                st.session_state["df_main"] = process_ifood_data(
                    generate_mock_ifood_data(800)
                )
                st.session_state["is_mock"] = True
                st.session_state.pop("upload_pendente", None)
                st.rerun()

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
          text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">
          Etapas
        </div>""", unsafe_allow_html=True)

        st.page_link("app.py",                   label="🏠  Visão Geral")
        st.page_link("pages/1_Operacao.py",      label="🚚  Operação")
        st.page_link("pages/2_Lucratividade.py", label="💰  Lucratividade")
        st.page_link("pages/3_Fidelizacao.py",   label="❤️  Fidelização")

        st.page_link("pages/4_Plano.py",     label="🧠  Plano de Crescimento")

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


def render_lock_card(titulo: str, itens_bloqueados: list, wpp_numero: str = "5512996320085"):
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


# ─────────────────────────────────────────────
#  GOOGLE SHEETS — leitura de dados do cliente
# ─────────────────────────────────────────────

def _limpar_valor_monetario(val) -> float:
    """Remove R$, pontos e vírgulas e converte para float."""
    if pd.isna(val) or str(val).strip() == "":
        return 0.0
    return float(
        str(val)
        .replace("R$", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )


def _limpar_float(val) -> float:
    """Converte string com vírgula decimal para float."""
    if pd.isna(val) or str(val).strip() == "":
        return 0.0
    return float(str(val).replace(",", ".").strip())


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
        gc       = gspread.service_account(filename="credentials.json")
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

    # ── 3. Intervenções ──────────────────────────────────────────────────
    try:
        df_int = pd.DataFrame(planilha.worksheet("intervencoes").get_all_records())
        df_int["data"] = pd.to_datetime(df_int["data"], dayfirst=True, errors="coerce")
        df_int["id"]   = pd.to_numeric(df_int["id"], errors="coerce")
        resultado["intervencoes"] = df_int
    except Exception as e:
        resultado["intervencoes"] = pd.DataFrame()
        st.warning(f"Aba 'intervencoes' com erro: {e}")

    # ── 4. Ganhos ────────────────────────────────────────────────────────
    try:
        df_gan = pd.DataFrame(planilha.worksheet("ganhos").get_all_records())
        df_gan["valor"]          = df_gan["valor"].apply(_limpar_valor_monetario)
        df_gan["intervencao_id"] = pd.to_numeric(df_gan["intervencao_id"], errors="coerce")
        resultado["ganhos"] = df_gan
    except Exception as e:
        resultado["ganhos"] = pd.DataFrame()
        st.warning(f"Aba 'ganhos' com erro: {e}")

    # ── 5. Notas ─────────────────────────────────────────────────────────
    try:
        df_not = pd.DataFrame(planilha.worksheet("notas").get_all_records())
        df_not["data"] = pd.to_datetime(df_not["data"], dayfirst=True, errors="coerce")
        resultado["notas"] = df_not
    except Exception as e:
        resultado["notas"] = pd.DataFrame()
        st.warning(f"Aba 'notas' com erro: {e}")

    return resultado

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
        gc       = gspread.service_account(filename="credentials.json")
        planilha = gc.open_by_key(sheets_id)
        df       = pd.DataFrame(planilha.worksheet("pedidos").get_all_records())
    except Exception as e:
        st.error(f"Erro ao ler aba 'pedidos': {e}")
        return None

    if df.empty:
        return None

    # Garantir tipos corretos
    df["Data do Pedido"]        = pd.to_datetime(df["Data do Pedido"], dayfirst=True, errors="coerce")
    df["Valor Bruto"]           = df["Valor Bruto"].apply(_limpar_valor_monetario)
    df["Taxa iFood"]            = df["Taxa iFood"].apply(_limpar_valor_monetario)
    df["Tempo de Entrega (min)"]= pd.to_numeric(df["Tempo de Entrega (min)"], errors="coerce").fillna(0)
    df["is_cancelado"]          = df["is_cancelado"].astype(str).str.strip().str.lower().isin(["true", "1", "sim", "s"])
    df["Dia Semana"]            = df["Data do Pedido"].dt.day_name()

    return df
