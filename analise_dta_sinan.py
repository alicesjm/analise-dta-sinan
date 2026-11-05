#!/usr/bin/env python3
"""
Análise de Doenças Transmitidas por Alimentos (DTA) no Brasil, 2010-2024 (SINAN).

Lê a planilha original (uma aba por ano) e gera TODAS as tabelas (1-10) e
figuras (1-10) do artigo. Nada é digitado à mão, exceto:
  - o mapa código IBGE -> sigla da UF (usado na aba 2016);
  - a população por UF (dados/populacao_uf.csv: IBGE, Tabela 6579), usada só nas taxas.

Uso:
    python analise_dta_sinan.py --entrada Dados_de_2010_a_2025.xlsx --saida resultados
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ANOS = list(range(2010, 2025))          # recorte do estudo
ANOS_PRE = [a for a in range(2010, 2020) if a != 2014]   # 2014 sem dados
ANOS_POS = list(range(2020, 2025))

# Na aba 2016 a coluna UF vem como código numérico do IBGE (nas demais, sigla).
IBGE_UF = {12: "AC", 27: "AL", 16: "AP", 13: "AM", 29: "BA", 23: "CE", 53: "DF",
           32: "ES", 52: "GO", 21: "MA", 51: "MT", 50: "MS", 31: "MG", 15: "PA",
           25: "PB", 41: "PR", 26: "PE", 22: "PI", 33: "RJ", 24: "RN", 43: "RS",
           11: "RO", 14: "RR", 42: "SC", 35: "SP", 28: "SE", 17: "TO"}

REGIOES = {
    "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MS", "MT"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
}
UF_REGIAO = {uf: r for r, ufs in REGIOES.items() for uf in ufs}

NAO_IDENTIFICADO = ["Ignorado", "Inconclusivo", "Inconsistente"]
AGENTES_PRINCIPAIS = ["Escherichia coli", "Salmonella spp", "Shigella sonnei",
                      "Staphylococcus aureus", "Clostridium perfringens",
                      "Bacillus cereus"]
COLS_ALIMENTO = ["Água", "Carne bovina", "Carne de ave", "Alimentos mistos",
                 "Múltiplos alimentos", "Cereais/farináceos", "Hortaliças", "Ignorado"]
TOP8_LOCAIS = ["Ambiente domiciliar (casa)", "Via oral",
               "Ignorado (informação não disponível)", "Creche",
               "Local de lazer (parque, clube, praia)", "Hospital",
               "Local de trabalho", "Ambulatório (Clínica, Centro de Saúde, etc.)"]
LOCAL_CURTO = {"Ambiente domiciliar (casa)": "Amb. domiciliar", "Via oral": "Via oral",
               "Ignorado (informação não disponível)": "Ignorado", "Creche": "Creche",
               "Local de lazer (parque, clube, praia)": "Local de lazer",
               "Hospital": "Hospital", "Local de trabalho": "Local de trabalho",
               "Ambulatório (Clínica, Centro de Saúde, etc.)": "Ambulatório"}

AZUL = "#1F3864"
PIZZA = ["#1F3864", "#2E5395", "#4472C4", "#5B87D6", "#7FA0DC",
         "#8FAADC", "#B4C7E7", "#D9E2F3", "#EEF2FA"]


# --------------------------------------------------------------------------
# 1. Leitura e tratamento
# --------------------------------------------------------------------------
def achar_coluna(df, *prefixos):
    """Acha a coluna cujo nome (minúsculo, sem espaços nas pontas) começa com
    algum dos prefixos. Os nomes variam entre abas (maiúsculas, acentos)."""
    for c in df.columns:
        nome = str(c).strip().lower()
        if any(nome.startswith(p) for p in prefixos):
            return c
    raise KeyError(f"coluna não encontrada: {prefixos}")


def ler_planilha(caminho):
    xl = pd.ExcelFile(caminho)
    partes, log = [], []
    for aba in xl.sheet_names:
        ano = int(aba)
        if ano not in ANOS:
            continue                         # 2025 fora do recorte
        df = xl.parse(aba)
        if len(df) == 0:
            log.append(f"{ano}: aba vazia (sem registros)")
            continue
        out = pd.DataFrame({
            "ano": ano,                      # ano = nome da aba
            "casos": pd.to_numeric(df[achar_coluna(df, "quantidade total de casos")],
                                   errors="coerce"),
            "uf": df[achar_coluna(df, "uf")],
            "local": df[achar_coluna(df, "local provável da exposição")],
            "agente": df[achar_coluna(df, "agente etiológico")],
            "alimento": df[achar_coluna(df, "alimento consumido")],
        })
        partes.append(out)
    full = pd.concat(partes, ignore_index=True)
    return full, log


def uf_para_sigla(v):
    if pd.isna(v):
        return np.nan
    if isinstance(v, (int, float, np.integer, np.floating)):
        return IBGE_UF.get(int(v), np.nan)
    v = str(v).strip().upper()
    return IBGE_UF.get(int(v), v) if v.isdigit() else v


def bucket_alimento(v):
    if v in NAO_IDENTIFICADO:
        return "Ignorado"
    if v == "Água":
        return "Água"
    if v == "Alimentos mistos":
        return "Alimentos mistos"
    if "Carne bovina" in v:
        return "Carne bovina"
    if v == "Múltiplos alimentos":
        return "Múltiplos alimentos"
    if "Cereais" in v or "farin" in v.lower():
        return "Cereais/farináceos"
    if "Carne de ave" in v:
        return "Carne de ave"
    if v == "Hortaliças":
        return "Hortaliças"
    return "Outros"


def bucket_alimento_t10(v):
    """Agrupamento usado na Tabela 10 do artigo (por palavra-chave, em minúsculas)."""
    f = v.lower()
    if "carne" in f or "ovo" in f:
        return "Carnes/Ovos"
    if "cereai" in f or "farin" in f:
        return "Cereais/Arroz"
    if "leite" in f or "doce" in f or "sobremesa" in f:
        return "Laticínios/Doces"
    if f.strip() == "água":
        return "Água"
    if "mist" in f or "múltiplos" in f:
        return "Mistos"
    return "Outro"


def tratar(full):
    full = full.copy()
    full["uf"] = full["uf"].apply(uf_para_sigla)
    full["agente"] = (full["agente"].astype(str).str.strip()
                      .replace({"Bacillus Cereus": "Bacillus cereus",
                                "Escherichia Coli": "Escherichia coli"}))
    full["alimento"] = (full["alimento"].fillna("Ignorado").astype(str).str.strip()
                        .replace({"ignorado": "Ignorado"}))
    full["local"] = full["local"].astype(str).str.strip()
    full["alimento_bucket"] = full["alimento"].apply(bucket_alimento)
    full["alimento_t10"] = full["alimento"].apply(bucket_alimento_t10)
    full["regiao"] = full["uf"].map(UF_REGIAO)
    return full


# --------------------------------------------------------------------------
# 2. Tabelas
# --------------------------------------------------------------------------
def tabelas(full, pop):
    T = {}
    total = full["casos"].sum()

    # Tabela 1 - evolução anual (+ % de linhas sem "Quantidade total de casos")
    anual = full.groupby("ano")["casos"].sum()
    sem_casos = full.groupby("ano")["casos"].apply(lambda s: s.isna().mean() * 100)
    t1 = pd.DataFrame({"ano": ANOS})
    t1["pessoas_afetadas"] = t1["ano"].map(anual)        # 2014 fica vazio (NaN)
    t1["pct_linhas_sem_qtd_casos"] = t1["ano"].map(sem_casos).round(1)
    T["tabela1_anual"] = t1

    # Tabela 2 - pré e pós-COVID
    linhas = []
    for nome, anos in [("Pré-COVID (2010-2019, sem 2014)", ANOS_PRE),
                       ("Pós-COVID (2020-2024)", ANOS_POS)]:
        s = anual.loc[anos]
        linhas.append({"periodo": nome, "n_anos": len(s), "total": s.sum(),
                       "media_anual": s.mean(), "maximo": s.max(),
                       "ano_maximo": s.idxmax(), "minimo": s.min(),
                       "ano_minimo": s.idxmin()})
    T["tabela2_pre_pos_covid"] = pd.DataFrame(linhas)

    # Tabela 3 - por UF, com taxa cumulativa por 100 mil hab.
    uf = full.groupby("uf")["casos"].sum().sort_values(ascending=False)
    t3 = pd.DataFrame({"uf": uf.index, "regiao": uf.index.map(UF_REGIAO),
                       "pessoas_afetadas": uf.values})
    t3["populacao_milhoes"] = t3["uf"].map(pop)
    t3["taxa_100mil"] = (t3["pessoas_afetadas"] / (t3["populacao_milhoes"] * 1e6)
                         * 1e5).round(1)
    T["tabela3_uf"] = t3
    reg = full.groupby("regiao")["casos"].sum().sort_values(ascending=False)
    T["tabela3b_regiao"] = pd.DataFrame({
        "regiao": reg.index, "pessoas_afetadas": reg.values,
        "pct_sobre_total_com_uf": (reg.values / reg.sum() * 100).round(1)})

    # Tabela 4 - agentes etiológicos
    g = full.groupby("agente")["casos"].sum()
    nao_id = sum(g.get(a, 0) for a in NAO_IDENTIFICADO)
    identificados = total - nao_id
    linhas = [{"agente": "Ignorado/Inconclusivo/Inconsistente", "pessoas": nao_id,
               "pct_total": nao_id / total * 100, "pct_identificados": np.nan}]
    soma = 0
    for a in AGENTES_PRINCIPAIS:
        v = g.get(a, 0)
        soma += v
        linhas.append({"agente": a, "pessoas": v, "pct_total": v / total * 100,
                       "pct_identificados": v / identificados * 100})
    outros = identificados - soma
    linhas.append({"agente": "Outros identificados", "pessoas": outros,
                   "pct_total": outros / total * 100,
                   "pct_identificados": outros / identificados * 100})
    linhas.append({"agente": "TOTAL IDENTIFICADOS", "pessoas": identificados,
                   "pct_total": identificados / total * 100, "pct_identificados": 100})
    linhas.append({"agente": "TOTAL GERAL", "pessoas": total, "pct_total": 100,
                   "pct_identificados": np.nan})
    T["tabela4_agentes"] = pd.DataFrame(linhas).round(1)

    # Tabela 5 - alimentos (categorias agrupadas)
    a5 = full.groupby("alimento_bucket")["casos"].sum().sort_values(ascending=False)
    T["tabela5_alimentos"] = pd.DataFrame({
        "alimento": a5.index, "pessoas": a5.values,
        "pct_total": (a5.values / total * 100).round(1)})

    # Tabela 6 - locais prováveis de exposição (valores originais da planilha)
    l6 = full.groupby("local")["casos"].sum().sort_values(ascending=False)
    T["tabela6_locais"] = pd.DataFrame({
        "local": l6.index, "pessoas": l6.values,
        "pct_total": (l6.values / total * 100).round(1)})

    # Tabelas 7, 8, 9 - cruzamentos
    sub = full[full["agente"].isin(AGENTES_PRINCIPAIS)]
    t7 = (sub.pivot_table(index="agente", columns="alimento_bucket", values="casos",
                          aggfunc="sum", fill_value=0)
          .reindex(AGENTES_PRINCIPAIS).reindex(columns=COLS_ALIMENTO, fill_value=0))
    T["tabela7_agente_x_alimento"] = t7.reset_index()
    t8 = (sub.pivot_table(index="agente", columns="local", values="casos",
                          aggfunc="sum", fill_value=0)
          .reindex(AGENTES_PRINCIPAIS).reindex(columns=TOP8_LOCAIS, fill_value=0))
    T["tabela8_agente_x_local"] = t8.reset_index()
    cols9 = [c for c in COLS_ALIMENTO if c != "Ignorado"]
    t9 = (full[full["alimento_bucket"].isin(cols9)]
          .pivot_table(index="alimento_bucket", columns="local", values="casos",
                       aggfunc="sum", fill_value=0)
          .reindex(cols9).reindex(columns=TOP8_LOCAIS, fill_value=0))
    T["tabela9_alimento_x_local"] = t9.reset_index()

    # Tabela 10 - intensidade da associação agente x tipo de alimento.
    # % = casos do agente na categoria / total de casos do agente (todas as
    # categorias, incluindo "Outro"). Agrupamento de alimentos: ver bucket_alimento_t10.
    cols10 = ["Carnes/Ovos", "Cereais/Arroz", "Laticínios/Doces", "Água", "Mistos", "Outro"]
    p10 = (sub.pivot_table(index="agente", columns="alimento_t10", values="casos",
                           aggfunc="sum", fill_value=0)
           .reindex(AGENTES_PRINCIPAIS).reindex(columns=cols10, fill_value=0))
    pct = p10.div(p10.sum(axis=1), axis=0) * 100
    niveis = pct.apply(lambda col: col.map(
        lambda p: "★★★" if p >= 35 else "★★" if p >= 15 else "★" if p >= 5 else "—"))
    out = pct.round(1).add_suffix(" (%)").join(niveis.add_suffix(" (nível)"))
    T["tabela10_intensidade"] = out.reset_index()
    return T


# --------------------------------------------------------------------------
# 3. Figuras
# --------------------------------------------------------------------------
def salvar(fig, caminho):
    fig.tight_layout()
    fig.savefig(caminho, dpi=200)
    plt.close(fig)


def figuras(full, T, pasta):
    plt.rcParams["font.family"] = "DejaVu Sans"
    total = full["casos"].sum()

    # Fig 1 - evolução anual (2014 em cinza = sem dados)
    t1 = T["tabela1_anual"]
    vals = t1["pessoas_afetadas"].fillna(0)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(t1["ano"].astype(str), vals,
           color=[AZUL if a != 2014 else "#CCCCCC" for a in t1["ano"]])
    ax.set_ylabel("Pessoas afetadas"); ax.set_xlabel("Ano")
    ax.set_title("Evolução anual dos casos associados a surtos de DTA (2010–2024)")
    plt.xticks(rotation=45)
    salvar(fig, f"{pasta}/fig1_evolucao_anual.png")

    # Fig 2 - por UF
    t3 = T["tabela3_uf"]
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.bar(t3["uf"], t3["pessoas_afetadas"], color=AZUL)
    ax.set_ylabel("Pessoas afetadas"); ax.set_xlabel("UF")
    ax.set_title("Distribuição dos casos de DTA por Estado (2010–2024)")
    salvar(fig, f"{pasta}/fig2_estados.png")

    # Fig 3 - por região
    r = T["tabela3b_regiao"]
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(r["pessoas_afetadas"],
           labels=[f"{a}\n{p:.1f}%" for a, p in zip(r["regiao"], r["pct_sobre_total_com_uf"])],
           colors=PIZZA[:5], startangle=90)
    ax.set_title("Distribuição proporcional dos casos de DTA por Região (2010–2024)")
    salvar(fig, f"{pasta}/fig3_regiao.png")

    # Fig 4 - taxa por 100 mil hab.
    t4 = t3.sort_values("taxa_100mil", ascending=False)
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.bar(t4["uf"], t4["taxa_100mil"], color=AZUL)
    ax.set_ylabel("Taxa por 100 mil habitantes (cumulativa, 2010–2024)")
    ax.set_xlabel("UF")
    ax.set_title("Taxas de pessoas afetadas por DTA por 100 mil habitantes, por Estado (2010–2024)")
    salvar(fig, f"{pasta}/fig4_taxas.png")

    # Fig 5 - agentes (absoluto) | Fig 6 - agentes (proporção entre identificados)
    g = full.groupby("agente")["casos"].sum()
    nao_id = sum(g.get(a, 0) for a in NAO_IDENTIFICADO)
    ident = total - nao_id
    ordem5 = ["Escherichia coli", "Salmonella spp", "Shigella sonnei",
              "Staphylococcus aureus", "Bacillus cereus", "Clostridium perfringens"]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(["Ignorado/\nInconclusivo"] + ordem5, [nao_id] + [g.get(a, 0) for a in ordem5],
           color=AZUL)
    ax.set_ylabel("Pessoas afetadas")
    ax.set_title("Distribuição dos principais agentes etiológicos identificados em casos de DTA (2010–2024)")
    plt.xticks(rotation=30, ha="right")
    salvar(fig, f"{pasta}/fig5_agentes.png")

    v6 = [g.get(a, 0) for a in ordem5]
    v6.append(ident - sum(v6))
    l6 = ordem5 + ["Outros identificados"]
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(v6, labels=[f"{l}\n{v / ident * 100:.1f}%" for l, v in zip(l6, v6)],
           colors=PIZZA[:7], startangle=90)
    ax.set_title("Proporção dos principais agentes etiológicos\n(entre os casos com identificação, 2010–2024)")
    salvar(fig, f"{pasta}/fig6_agentes_prop.png")

    # Fig 7 - top 8 alimentos | Fig 8 - proporção
    a = full.groupby("alimento_bucket")["casos"].sum().sort_values(ascending=False)
    top8 = a[a.index != "Outros"].head(8)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(top8.index, top8.values, color=AZUL)
    ax.set_ylabel("Pessoas afetadas")
    ax.set_title("Top 8 alimentos envolvidos em casos de DTA no Brasil (2010–2024)")
    plt.xticks(rotation=30, ha="right")
    salvar(fig, f"{pasta}/fig7_alimentos.png")

    v8 = list(top8.values) + [total - top8.sum()]
    l8 = list(top8.index) + ["Outros"]
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(v8, labels=[f"{l}\n{v / total * 100:.1f}%" for l, v in zip(l8, v8)],
           colors=PIZZA, startangle=90)
    ax.set_title("Proporção dos principais alimentos envolvidos em casos de DTA (2010–2024)")
    salvar(fig, f"{pasta}/fig8_alimentos_prop.png")

    # Fig 9 - top 8 locais | Fig 10 - proporção
    loc = full.groupby("local")["casos"].sum().sort_values(ascending=False).head(8)
    rot = [LOCAL_CURTO.get(k, k) for k in loc.index]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(rot, loc.values, color=AZUL)
    ax.set_ylabel("Pessoas afetadas")
    ax.set_title("Distribuição dos principais locais prováveis de exposição em casos de DTA (2010–2024)")
    plt.xticks(rotation=30, ha="right")
    salvar(fig, f"{pasta}/fig9_locais.png")

    v10 = list(loc.values) + [total - loc.sum()]
    l10 = rot + ["Outros"]
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(v10, labels=[f"{l}\n{v / total * 100:.1f}%" for l, v in zip(l10, v10)],
           colors=PIZZA, startangle=90)
    ax.set_title("Proporção dos principais locais prováveis de exposição em casos de DTA (2010–2024)")
    salvar(fig, f"{pasta}/fig10_locais_prop.png")


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", default="dados/Dados_de_2010_a_2025.xlsx")
    ap.add_argument("--populacao", default="dados/populacao_uf.csv")
    ap.add_argument("--saida", default="resultados")
    a = ap.parse_args()

    if not os.path.exists(a.entrada):
        sys.exit(f"Planilha não encontrada: {a.entrada}\n"
                 "Ela não é distribuída neste repositório. Veja dados/LEIA-ME_dados.md "
                 "para a origem e o formato esperado, ou use --entrada CAMINHO.xlsx")
    os.makedirs(f"{a.saida}/tabelas", exist_ok=True)
    os.makedirs(f"{a.saida}/figuras", exist_ok=True)

    pop = (pd.read_csv(a.populacao).set_index("uf")["populacao_media"] / 1e6).to_dict()  # milhões
    bruto, log = ler_planilha(a.entrada)
    for l in log:
        print("aviso:", l)
    full = tratar(bruto)

    sem_uf = int(full["uf"].isna().sum())
    print(f"registros lidos: {len(full)} | pessoas afetadas (soma): {full['casos'].sum():.0f}"
          f" | linhas sem UF: {sem_uf} | linhas sem 'Quantidade total de casos': "
          f"{int(full['casos'].isna().sum())}")
    desconhecidas = sorted(set(full['uf'].dropna()) - set(UF_REGIAO))
    if desconhecidas:
        sys.exit(f"UF não reconhecida: {desconhecidas}")

    T = tabelas(full, pop)
    for nome, df in T.items():
        df.to_csv(f"{a.saida}/tabelas/{nome}.csv", index=False, encoding="utf-8-sig")
    figuras(full, T, f"{a.saida}/figuras")
    print(f"ok: {len(T)} tabelas e 10 figuras em '{a.saida}/'")


if __name__ == "__main__":
    main()
