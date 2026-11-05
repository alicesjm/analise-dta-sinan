# Código de análise — DTA no Brasil (2010–2024), dados SINAN

Código e documentação para reproduzir todas as tabelas e figuras do artigo
**"Doenças transmitidas por alimentos no Brasil (2010–2024): padrões
epidemiológicos e implicações para a vigilância sanitária"**.

> DOI do depósito: _a preencher após o depósito (Zenodo)._

## Conteúdo

| Arquivo | Função |
|---|---|
| `analise_dta_sinan.py` | Script único: lê a planilha, trata os dados e gera tabelas e figuras |
| `conferir_resultados.py` | Compara as saídas com os valores publicados no artigo |
| `dados/populacao_uf.csv` | População média por UF (IBGE, Tabela 6579) usada nas taxas |
| `dados/Dados_de_2010_a_2025.xlsx` | Planilha de entrada (ver "Dados") |
| `requirements.txt` | Versões das bibliotecas |
| `resultados/` | Saídas (11 tabelas em CSV, 10 figuras em PNG) |

## Dados

Fonte: Sistema de Informação de Agravos de Notificação (SINAN), módulo de
surtos de DTA, Ministério da Saúde, consultado e exportado pelos autores.
A planilha `Dados_de_2010_a_2025.xlsx` reúne uma aba por ano (2010–2025),
com 10.336 registros no recorte 2010–2024. Os dados são agregados por
surto/notificação, sem identificação de pessoas.

## Como reproduzir

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python analise_dta_sinan.py --entrada dados/Dados_de_2010_a_2025.xlsx --saida resultados
python conferir_resultados.py resultados              # deve terminar com "DIVERGÊNCIAS: 0"
```

## Etapas de processamento (o que o script faz)

1. Lê as abas 2010–2024 (2025 fica fora do recorte). Os nomes de coluna variam
   entre abas; o script os localiza por prefixo, ignorando maiúsculas e espaços.
2. O ano é o nome da aba. As abas **2014** e **2025** não têm registros.
3. **Pessoas afetadas** = soma da coluna "Quantidade total de casos" (não a
   contagem de linhas). Linhas com essa coluna em branco não entram na soma.
4. **UF:** na aba 2016 a coluna vem como código numérico do IBGE (ex.: 35);
   o script converte para sigla. Restam 100 linhas sem UF, que entram nos totais
   nacionais e ficam fora das tabelas por UF/região.
5. Agentes: "Ignorado", "Inconclusivo" e "Inconsistente" = não identificado.
   Grafias "Bacillus Cereus" e "Escherichia Coli" são normalizadas.
6. Alimentos: categorias agrupadas por regra explícita (`bucket_alimento`,
   e `bucket_alimento_t10` para a Tabela 10).
7. **Taxa por 100 mil hab.** = pessoas afetadas em 2010–2024 ÷ população média da UF
   (IBGE, Tabela 6579) × 100.000. É taxa **cumulativa do período**, não anual.
8. Tabela 10: % dos casos do agente por categoria de alimento; ★★★ ≥ 35 %,
   ★★ 15–34 %, ★ 5–14 %, — < 5 %.
9. Pré-COVID = 2010–2019 sem 2014 (9 anos); pós-COVID = 2020–2024.

## Limitações conhecidas

- **2014 sem dados** na fonte; **2025** fora do recorte.
- **Subnotificação do campo de casos em 2016–2018:** 54,8 %, 55,9 % e 61,3 % das
  linhas, respectivamente, não têm "Quantidade total de casos". Esses três anos
  estão subestimados e comparações temporais devem considerar isso.
- **População (`dados/populacao_uf.csv`):** "População residente estimada" (variável
  9324) da Tabela 6579 do IBGE (API SIDRA), por UF. A tabela não traz 2010, 2022 e
  2023 (anos de Censo/contagem); por isso a população usada é a **média dos 12 anos
  disponíveis em 2010–2024** (2011–2021 e 2024). Arquivo `populacao_uf_anterior_artigo.csv`
  guarda os valores arredondados usados em versões anteriores do texto, só para
  comparação; as taxas oficiais diferem deles em até ~5 % (maioria 1–2 %).
- Cerca de 60 % dos casos não têm agente identificado e 57 % não têm alimento
  identificado; as proporções entre "identificados" refletem só a parte investigada.

## Como citar

Moreira, A. S. J.; Favareto, A. P. A.; Costa, S. M.; Uliana, M. R. Código de
análise: DTA no Brasil (2010–2024), SINAN. Zenodo, 2025. DOI: _a preencher_.

## Uso de inteligência artificial

O script foi (re)escrito com apoio do assistente de IA Claude (Anthropic) e
conferido pelos autores contra a planilha original e contra os resultados
publicados (`conferir_resultados.py`). Os autores respondem pelo conteúdo.

## Licença

Código: MIT (`LICENSE`). Dados e resultados: CC BY 4.0 (fonte original:
SINAN/Ministério da Saúde).
