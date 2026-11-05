#!/usr/bin/env python3
"""Confere as saídas do script principal contra os valores publicados no artigo.
Uso: python conferir_resultados.py [pasta_resultados]"""
import sys
import pandas as pd

pasta = sys.argv[1] if len(sys.argv) > 1 else "resultados"
rd = lambda n: pd.read_csv(f"{pasta}/tabelas/{n}.csv")
falhas = 0
def checa(rotulo, obtido, esperado, tol=0.0):
    global falhas
    ok = abs(float(obtido) - float(esperado)) <= tol
    falhas += (not ok)
    print(("OK    " if ok else "DIFERE"), f"{rotulo}: obtido={obtido} esperado={esperado}")

t1 = rd("tabela1_anual").set_index("ano")["pessoas_afetadas"]
for a, v in {2010: 23954, 2011: 52662, 2012: 42138, 2013: 64362, 2015: 37165,
             2016: 19892, 2017: 4525, 2018: 5498, 2019: 17388, 2020: 10548,
             2021: 17076, 2022: 33977, 2023: 27854, 2024: 42617}.items():
    checa(f"ano {a}", t1[a], v)
t2 = rd("tabela2_pre_pos_covid")
checa("pré total", t2.loc[0, "total"], 267584); checa("pré média", t2.loc[0, "media_anual"], 29732, 0.5)
checa("pós total", t2.loc[1, "total"], 132072); checa("pós média", t2.loc[1, "media_anual"], 26414, 0.5)

t3 = rd("tabela3_uf").set_index("uf")
for uf, v in {"PE": 111646, "MG": 40093, "RS": 37511, "RJ": 30466, "SC": 29299,
              "BA": 23164, "SP": 20239, "PR": 15802, "RN": 11207, "CE": 11151,
              "SE": 10773}.items():
    checa(f"UF {uf}", t3.loc[uf, "pessoas_afetadas"], v)
# Taxas com população oficial do IBGE (Tabela 6579, média dos anos disponíveis em 2010-2024)
checa("taxa PE", t3.loc["PE", "taxa_100mil"], 1192.0, 0.05)
checa("taxa SP", t3.loc["SP", "taxa_100mil"], 45.3, 0.05)
checa("taxa SE", t3.loc["SE", "taxa_100mil"], 479.9, 0.05)
checa("MS pessoas", t3.loc["MS", "pessoas_afetadas"], 1999)
checa("MT pessoas", t3.loc["MT", "pessoas_afetadas"], 882)
checa("taxa MS", t3.loc["MS", "taxa_100mil"], 74.2, 0.05)
checa("taxa MT", t3.loc["MT", "taxa_100mil"], 26.2, 0.05)
checa("total com UF", t3["pessoas_afetadas"].sum(), 396400)
checa("PR é o 8º", list(t3.index).index("PR") + 1, 8)

r = rd("tabela3b_regiao").set_index("regiao")["pct_sobre_total_com_uf"]
for k, v in {"Nordeste": 44.0, "Sudeste": 25.3, "Sul": 20.8, "Centro-Oeste": 5.4, "Norte": 4.4}.items():
    checa(f"região {k} %", r[k], v, 0.05)

t4 = rd("tabela4_agentes").set_index("agente")
for k, (n, pt, pi) in {"Escherichia coli": (41727, 10.4, 26.1), "Salmonella spp": (16413, 4.1, 10.3),
                       "Shigella sonnei": (14143, 3.5, 8.9), "Staphylococcus aureus": (14061, 3.5, 8.8),
                       "Clostridium perfringens": (10587, 2.6, 6.6), "Bacillus cereus": (11240, 2.8, 7.0),
                       "Outros identificados": (51631, 12.9, 32.3)}.items():
    checa(f"{k} n", t4.loc[k, "pessoas"], n); checa(f"{k} %total", t4.loc[k, "pct_total"], pt, 0.05)
    checa(f"{k} %ident", t4.loc[k, "pct_identificados"], pi, 0.05)
checa("identificados", t4.loc["TOTAL IDENTIFICADOS", "pessoas"], 159802)
checa("não identificados %", t4.iloc[0]["pct_total"], 60.0, 0.05)

t5 = rd("tabela5_alimentos").set_index("alimento")
for k, (n, p) in {"Ignorado": (229168, 57.3), "Água": (65009, 16.3), "Alimentos mistos": (27294, 6.8),
                  "Carne bovina": (19906, 5.0), "Múltiplos alimentos": (16706, 4.2),
                  "Carne de ave": (8020, 2.0), "Cereais/farináceos": (7810, 2.0),
                  "Hortaliças": (6587, 1.6)}.items():
    checa(f"alimento {k}", t5.loc[k, "pessoas"], n); checa(f"alimento {k} %", t5.loc[k, "pct_total"], p, 0.05)

t6 = rd("tabela6_locais").set_index("local")
for k, (n, p) in {"Ambiente domiciliar (casa)": (100783, 25.2), "Via oral": (73880, 18.5),
                  "Ignorado (informação não disponível)": (52218, 13.1), "Creche": (45667, 11.4),
                  "Local de lazer (parque, clube, praia)": (35917, 9.0), "Hospital": (34201, 8.6),
                  "Local de trabalho": (27025, 6.8),
                  "Ambulatório (Clínica, Centro de Saúde, etc.)": (16344, 4.1)}.items():
    checa(f"local {k[:22]}", t6.loc[k, "pessoas"], n); checa(f"local {k[:22]} %", t6.loc[k, "pct_total"], p, 0.05)
t10 = rd("tabela10_intensidade").set_index("agente")
esperado = {  # Tabela 10 do artigo (Carnes/Ovos, Cereais/Arroz, Laticínios/Doces, Água, Mistos)
    "Escherichia coli": ["★", "★", "—", "★★★", "★"],
    "Salmonella spp": ["★★★", "—", "—", "★", "★★"],
    "Shigella sonnei": ["—", "—", "—", "★★★", "—"],
    "Staphylococcus aureus": ["★", "★", "—", "—", "★★★"],
    "Bacillus cereus": ["★★", "★★", "—", "—", "★★★"],
    "Clostridium perfringens": ["★★★", "—", "—", "—", "★★"]}
cols = ["Carnes/Ovos", "Cereais/Arroz", "Laticínios/Doces", "Água", "Mistos"]
for ag, niv in esperado.items():
    obt = [t10.loc[ag, f"{c} (nível)"] for c in cols]
    ok = obt == niv
    falhas += (not ok)
    print(("OK    " if ok else "DIFERE"), f"Tabela 10 – {ag}: obtido={obt} esperado={niv}")
print("\nDIVERGÊNCIAS:", falhas)
sys.exit(1 if falhas else 0)
