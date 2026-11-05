# Dados de entrada

**Fonte:** banco de dados de surtos de DTHA (SINAN, Ministério da Saúde/DATASUS),
2007–2024. Este estudo usa 2010–2024.

**Como o arquivo foi montado:** os arquivos anuais `SDTABRaa.parquet` (DATASUS,
transferência de arquivos, acesso em 04/09/2026) são convertidos por
`converter_parquet_para_xlsx.py` em uma única planilha Excel, `Dados_de_2010_a_2025.xlsx`, com **uma aba por
ano**, nomeada com o ano (`2010`, `2011`, …, `2025`).
A planilha não é redistribuída aqui; a decisão sobre sua publicação depende da
verificação das condições de redistribuição da fonte.

### Regras da conversão
- Quantidade total de casos ← `QT_TOTAL_C`; UF ← `SG_UF` (código IBGE → sigla);
  Local provável da exposição ← `CS_LOCAL` (1 Hospital … 11 Via oral); Agente ←
  `AGENTE_ETI` (2010–2021) ou `AGENTE_ET1` (2022–2024); Alimento ← `ALIMENTO_C`.
- Os arquivos misturam codificações de texto (UTF-8 lido como Latin-1 e CP850); o
  script repara os rótulos.
- Verificação: contra a planilha construída antes, as 10.336 linhas e 399.656 pessoas
  afetadas coincidem. A única divergência de conteúdo era de 17 linhas de 2024 (462
  pessoas) que a planilha antiga trazia como MS e a fonte registra como MT (código 51);
  vale a fonte (MS 1.999; MT 882).

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
