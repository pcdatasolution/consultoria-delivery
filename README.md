# 🍕 DeliveryPro — Hub de Soluções

Consultoria de dados para donos de restaurantes e delivery.  
Transforma relatórios brutos do iFood em decisões que aumentam o lucro.

## 📁 Estrutura

```
hub_delivery/
├── streamlit_app.py          # Landing Page + Visão Geral
├── utils.py                  # Mock data + process_ifood_data()
├── requirements.txt
└── pages/
    ├── 1_Operacao.py         # Tempo de entrega, cancelamentos, mapa
    ├── 2_Lucratividade.py    # Matriz de cardápio, vazamento de lucro
    └── 3_Fidelizacao.py      # Cohort, churn, lista de recuperação
```

## 🚀 Como Rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Rodar o app
streamlit run streamlit_app.py
```

O dashboard abre automaticamente com **800 pedidos simulados** no formato iFood.  
Nenhum arquivo necessário para visualizar o potencial da ferramenta.

## 📤 Usando com Dados Reais

1. Acesse **Portal do Parceiro iFood → Relatórios → Pedidos**
2. Exporte o período desejado como `.csv`
3. Arraste o arquivo no **upload da landing page**
4. Todos os módulos atualizam automaticamente

### Colunas esperadas no CSV do iFood:
| Coluna | Exemplo |
|--------|---------|
| Data do Pedido | 01/05/2025 20:34 |
| ID do Pedido | PED123456 |
| Status | Concluído / Cancelado |
| Valor dos Itens | R$ 49,90 |
| Taxa de Entrega | R$ 5,00 |
| Valor Bruto | R$ 54,90 |
| Comissão iFood | R$ 8,78 |
| Nome do Item | Pizza Margherita |
| Bairro | Vila Madalena |

## 🎯 Os 3 Módulos

### 🚚 Operação
- Tempo médio de entrega por bairro
- Mapa de calor de cancelamentos
- Análise por dia da semana

### 💰 Lucratividade
- Matriz Estrela / Potencial / Cavalo / Problema
- Estimativa de "Vazamento de Lucro"
- Plano de ação por item

### ❤️ Fidelização
- Análise de Cohort simplificada
- Funil de risco de churn
- Lista de clientes para recuperar (>30 dias inativos)

## 🔧 Personalização

- Edite `utils.py` para ajustar os produtos do seu cardápio em `ITENS_CARDAPIO`
- Altere o link do WhatsApp em `streamlit_app.py` na seção CTA
- O slider de "custo médio" na página de Lucratividade é editável em tempo real
