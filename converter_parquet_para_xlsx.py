#!/usr/bin/env python3
"""Converte os arquivos SDTABRaa.parquet (SINAN/DTHA, DATASUS) na planilha
Dados_de_2010_a_2025.xlsx usada por analise_dta_sinan.py.

Uso:
    python converter_parquet_para_xlsx.py --entrada PASTA_COM_PARQUET --saida dados/Dados_de_2010_a_2025.xlsx

Regras (verificadas contra a planilha original, ver LEIA-ME_dados.md):
  * 1 aba por ano (nome da aba = ano); 2014 não existe na fonte.
  * Quantidade total de casos  <- QT_TOTAL_C
  * UF                         <- SG_UF (sigla; de 2016 em diante a fonte traz o
                                  código IBGE numérico, convertido para sigla)
  * Local provável da exposição <- CS_LOCAL (dicionário da ficha DTHA)
  * Agente etiológico          <- AGENTE_ETI (2010-2021) / AGENTE_ET1 (2022-2024)
  * Alimento consumido         <- ALIMENTO_C
  * Textos: UTF-8 lido como Latin-1 na fonte ("Ã£") é reparado.
"""
import argparse, re, sys
from pathlib import Path
import pandas as pd

COD_UF = {'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI',
          '23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES',
          '33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO','53':'DF'}
LOCAL = {'1':'Hospital','2':'Ambulatório (Clínica, Centro de Saúde, etc.)','3':'Creche','4':'Escola',
         '5':'Ambiente domiciliar (casa)','6':'Local de trabalho','7':'Local de lazer (parque, clube, praia)',
         '8':'Outro (local não especificado nas opções anteriores)','9':'Ignorado (informação não disponível)',
         '10':'Via aérea','11':'Via oral'}

SUSPEITOS = set('ÃÂµ£Æ¢¡¤¥ª') | {chr(c) for c in range(0x80, 0xA0)} | {'\xa0'}

def _pontos(t):
    return sum(ch in SUSPEITOS for ch in t)

def reparar(s):
    """Os arquivos da fonte misturam codificações: alguns têm UTF-8 lido como
    Latin-1 ("Ã£") e outros, texto DOS/CP850 lido como Latin-1 ("µgua" = "Água",
    "Açaí" = "A\\x87a¡"). Testa as três leituras e fica com a menos suspeita."""
    if not isinstance(s, str): return s
    candidatos = [s]
    for enc_in, enc_out in (('cp1252', 'utf8'), ('latin1', 'utf8'), ('latin1', 'cp850')):
        try: candidatos.append(s.encode(enc_in).decode(enc_out))
        except Exception: pass
    return min(candidatos, key=_pontos)

def converter_ano(df):
    ag = 'AGENTE_ETI' if 'AGENTE_ETI' in df.columns else 'AGENTE_ET1'
    uf = df['SG_UF'].fillna('').astype(str).str.strip().replace(COD_UF)
    loc = df['CS_LOCAL'].fillna('').astype(str).str.strip().str.lstrip('0').map(LOCAL).fillna('')
    out = pd.DataFrame({
        'Código do agravo': df['ID_AGRAVO'],
        'ano da notificação': pd.to_numeric(df['NU_ANO'], errors='coerce'),
        'Quantidade total de casos': pd.to_numeric(df['QT_TOTAL_C'], errors='coerce'),
        'Local provável da exposição': loc,
        'UF': uf,
        'Agente etiológico identificado': df[ag].map(reparar),
        'Alimento consumido (ex.: carne, ovo, leite)': df['ALIMENTO_C'].map(reparar),
    })
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--entrada', required=True, help='pasta com SDTABR*.parquet')
    ap.add_argument('--saida', default='dados/Dados_de_2010_a_2025.xlsx')
    a = ap.parse_args()
    arqs = sorted(Path(a.entrada).glob('SDTABR*.parquet'))
    Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with pd.ExcelWriter(a.saida, engine='openpyxl') as w:
        for f in arqs:
            m = re.search(r'SDTABR(\d\d)', f.name); ano = 2000 + int(m.group(1))
            if not 2010 <= ano <= 2024: continue
            conv = converter_ano(pd.read_parquet(f))
            conv.to_excel(w, sheet_name=str(ano), index=False)
            print(f'{ano}: {len(conv)} linhas, {int(conv["Quantidade total de casos"].sum())} casos')
            n += 1
    print(f'{n} abas gravadas em {a.saida}')

if __name__ == '__main__':
    main()
