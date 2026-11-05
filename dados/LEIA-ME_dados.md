# Dados de entrada

**Fonte:** banco de dados de surtos de DTHA (SINAN, Ministério da Saúde/DATASUS),
2007–2024. Este estudo usa 2010–2024.

**Como o arquivo foi montado:** os autores reuniram os arquivos anuais exportados da
fonte em uma única planilha Excel, `Dados_de_2010_a_2025.xlsx`, com **uma aba por
ano**, nomeada com o ano (`2010`, `2011`, …, `2025`).
A planilha não é redistribuída aqui; a decisão sobre sua publicação depende da
verificação das condições de redistribuição da fonte.

## O que o script espera

| Informação | Coluna na aba (maiúsculas e espaços não importam) |
|---|---|
| Pessoas afetadas | começa com "Quantidade total de casos" |
| Unidade da Federação | "UF" (sigla; na aba 2016 vem como código IBGE numérico) |
| Local/via de exposição | começa com "Local provável da exposição" |
| Agente etiológico | começa com "Agente etiológico" |
| Alimento/veículo | começa com "Alimento consumido" |

O **ano** é o nome da aba. Abas vazias (2014 e 2025 na versão usada) são ignoradas.
O script usa as abas 2010–2024.

## Tratamentos aplicados
Ver `README.md`, seção "Etapas de processamento".

## População (IBGE)
`populacao_uf.csv`: população residente estimada por UF (IBGE, Tabela 6579, variável
9324), média dos anos disponíveis entre 2010 e 2024 (2011–2021 e 2024).
`populacao_uf_anterior_artigo.csv` guarda valores arredondados de versões anteriores
do texto, apenas para comparação.
