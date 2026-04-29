"""
Utilitários de dados para o Hub de Soluções iFood.
Inclui geração de dados fictícios e processamento de CSVs reais.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random


# ─────────────────────────────────────────────
#  MOCK DATA — Simula relatório do iFood
# ─────────────────────────────────────────────

BAIRROS = [
    "Centro", "Vila Madalena", "Pinheiros", "Itaim Bibi",
    "Moema", "Lapa", "Santana", "Tatuapé",
    "Perdizes", "Consolação", "Bela Vista", "Liberdade"
]

COORDS_BAIRROS = {
    "Centro":       (-23.5505, -46.6333),
    "Vila Madalena":(-23.5558, -46.6920),
    "Pinheiros":    (-23.5665, -46.6947),
    "Itaim Bibi":   (-23.5853, -46.6767),
    "Moema":        (-23.6013, -46.6650),
    "Lapa":         (-23.5270, -46.7060),
    "Santana":      (-23.4970, -46.6260),
    "Tatuapé":      (-23.5380, -46.5700),
    "Perdizes":     (-23.5350, -46.6680),
    "Consolação":   (-23.5520, -46.6570),
    "Bela Vista":   (-23.5590, -46.6430),
    "Liberdade":    (-23.5599, -46.6338),
}

ITENS_CARDAPIO = {
    "Pizza Margherita":    {"custo": 18.0,  "preco": 49.90},
    "Pizza Calabresa":     {"custo": 20.0,  "preco": 54.90},
    "Pizza Frango c/ Catupiry": {"custo": 22.0, "preco": 59.90},
    "Pizza Portuguesa":    {"custo": 24.0,  "preco": 62.90},
    "Pizza Quatro Queijos":{"custo": 25.0,  "preco": 64.90},
    "Hamburger Clássico":  {"custo": 14.0,  "preco": 32.90},
    "Hamburger Bacon":     {"custo": 16.0,  "preco": 38.90},
    "Hamburger Duplo":     {"custo": 18.0,  "preco": 44.90},
    "Batata Frita P":      {"custo":  5.0,  "preco": 16.90},
    "Batata Frita G":      {"custo":  7.0,  "preco": 22.90},
    "Refrigerante Lata":   {"custo":  3.5,  "preco":  8.90},
    "Suco Natural":        {"custo":  4.0,  "preco": 12.90},
    "Combo Familia":       {"custo": 38.0,  "preco": 89.90},
    "Sobremesa Brownie":   {"custo":  6.0,  "preco": 18.90},
}

# Pesos de popularidade por item (quanto mais pedidos)
POPULARIDADE = {
    "Pizza Margherita":    0.13,
    "Pizza Calabresa":     0.11,
    "Pizza Frango c/ Catupiry": 0.09,
    "Pizza Portuguesa":    0.07,
    "Pizza Quatro Queijos":0.06,
    "Hamburger Clássico":  0.10,
    "Hamburger Bacon":     0.09,
    "Hamburger Duplo":     0.06,
    "Batata Frita P":      0.08,
    "Batata Frita G":      0.05,
    "Refrigerante Lata":   0.07,
    "Suco Natural":        0.03,
    "Combo Familia":       0.04,
    "Sobremesa Brownie":   0.02,
}


def generate_mock_ifood_data(n_pedidos: int = 800) -> pd.DataFrame:
    """
    Gera um DataFrame que simula exatamente a estrutura
    de exportação do Portal do Parceiro iFood.
    """
    np.random.seed(42)
    random.seed(42)

    hoje = datetime.today()
    datas = [hoje - timedelta(days=random.randint(0, 180)) for _ in range(n_pedidos)]
    datas.sort()

    itens = random.choices(
        list(POPULARIDADE.keys()),
        weights=list(POPULARIDADE.values()),
        k=n_pedidos
    )

    bairros = random.choices(BAIRROS, k=n_pedidos)

    # Status: ~88% concluído, ~12% cancelado
    status = np.random.choice(
        ["Concluído", "Cancelado"],
        size=n_pedidos,
        p=[0.88, 0.12]
    )

    # Valores por item
    valor_itens   = [ITENS_CARDAPIO[i]["preco"] * random.randint(1, 3) for i in itens]
    taxa_entrega  = [random.uniform(3.0, 8.5) for _ in range(n_pedidos)]
    valor_bruto   = [v + t for v, t in zip(valor_itens, taxa_entrega)]
    comissao_pct  = [random.uniform(0.12, 0.27) for _ in range(n_pedidos)]
    comissao_ifood= [v * c for v, c in zip(valor_bruto, comissao_pct)]
    distancia_km  = [random.uniform(0.5, 8.5) for _ in range(n_pedidos)]

    # Tempo de entrega em minutos (correlacionado com distância)
    tempo_entrega = [
        int(15 + dist * 4 + np.random.normal(0, 5))
        for dist in distancia_km
    ]

    # IDs únicos de clientes (para análise de retenção)
    n_clientes = int(n_pedidos * 0.55)
    cliente_ids = [f"CLI{random.randint(1000, 9999)}" for _ in range(n_clientes)]
    clientes_pedido = [random.choice(cliente_ids) for _ in range(n_pedidos)]

    coords = [COORDS_BAIRROS[b] for b in bairros]
    lats   = [c[0] + np.random.normal(0, 0.005) for c in coords]
    lons   = [c[1] + np.random.normal(0, 0.005) for c in coords]

    df = pd.DataFrame({
        "Data do Pedido":    datas,
        "ID do Pedido":      [f"PED{random.randint(100000, 999999)}" for _ in range(n_pedidos)],
        "ID do Cliente":     clientes_pedido,
        "Status":            status,
        "Nome do Item":      itens,
        "Valor dos Itens":   valor_itens,
        "Taxa de Entrega":   taxa_entrega,
        "Valor Bruto":       valor_bruto,
        "Comissão iFood":    comissao_ifood,
        "Distância (km)":    distancia_km,
        "Bairro":            bairros,
        "Tempo de Entrega (min)": tempo_entrega,
        "lat":               lats,
        "lon":               lons,
    })

    return df


# ─────────────────────────────────────────────
#  PROCESSAMENTO DE DADOS REAIS (upload CSV)
# ─────────────────────────────────────────────

def process_ifood_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpeza e enriquecimento do relatório iFood.
    Converte datas, trata cancelados e calcula margem líquida.
    """
    df = df.copy()

    # 1. Converter coluna de data
    date_cols = [c for c in df.columns if "data" in c.lower() or "date" in c.lower()]
    if date_cols:
        df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], dayfirst=True, errors="coerce")
        df.rename(columns={date_cols[0]: "Data do Pedido"}, inplace=True)

    # 2. Normalizar coluna de status
    if "Status" in df.columns:
        df["Status"] = df["Status"].str.strip().str.title()

    # 3. Colunas numéricas — remover R$, vírgulas etc. (somente se forem string)
    num_cols = ["Valor dos Itens", "Taxa de Entrega", "Valor Bruto", "Comissão iFood"]
    for col in num_cols:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = (
                    df[col].astype(str)
                    .str.replace("R$", "", regex=False)
                    .str.replace(".", "", regex=False)
                    .str.replace(",", ".", regex=False)
                    .str.strip()
                )
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 4. Calcular Margem Líquida Estimada
    if "Valor Bruto" in df.columns and "Comissão iFood" in df.columns:
        df["Receita Líquida"] = df["Valor Bruto"] - df["Comissão iFood"]

    # 5. Adicionar flag de cancelado
    if "Status" in df.columns:
        df["is_cancelado"] = df["Status"].str.lower().str.contains("cancel")
    else:
        df["is_cancelado"] = False

    # 6. Campos de data derivados
    if "Data do Pedido" in df.columns:
        df["Mês"]         = df["Data do Pedido"].dt.to_period("M").astype(str)
        df["Dia Semana"]  = df["Data do Pedido"].dt.day_name()
        df["Hora"]        = df["Data do Pedido"].dt.hour

    return df


def get_kpis(df: pd.DataFrame) -> dict:
    """Retorna os KPIs principais para exibição no dashboard."""
    concluidos = df[~df.get("is_cancelado", pd.Series(False, index=df.index))]

    faturamento = concluidos["Valor Bruto"].sum() if "Valor Bruto" in df.columns else 0
    receita_liq = concluidos["Receita Líquida"].sum() if "Receita Líquida" in df.columns else 0
    ticket_medio = concluidos["Valor Bruto"].mean() if "Valor Bruto" in df.columns else 0
    total_pedidos = len(concluidos)
    cancelados = df["is_cancelado"].sum() if "is_cancelado" in df.columns else 0
    taxa_cancelamento = (cancelados / len(df) * 100) if len(df) > 0 else 0
    comissao_total = concluidos["Comissão iFood"].sum() if "Comissão iFood" in df.columns else 0

    return {
        "faturamento":        faturamento,
        "receita_liquida":    receita_liq,
        "ticket_medio":       ticket_medio,
        "total_pedidos":      total_pedidos,
        "taxa_cancelamento":  taxa_cancelamento,
        "comissao_total":     comissao_total,
        "perda_cancelamentos": df[df.get("is_cancelado", pd.Series(False, index=df.index))]["Valor Bruto"].sum() if "Valor Bruto" in df.columns else 0,
    }
