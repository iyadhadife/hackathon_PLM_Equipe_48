import pandas as pd
import re
import numpy as np

# Charger les fichiers
mes = pd.read_excel('uploads/MES_Extraction.xlsx')
plm = pd.read_excel('uploads/PLM_DataSet.xlsx')
erp = pd.read_excel('uploads/ERP_Equipes_Airplus.xlsx')

# Étape 1 : MES explodé
df_mes = mes.copy()
df_mes['Code_piece'] = df_mes['Référence'].astype(str).str.split(';')
df_mes = df_mes.explode('Code_piece')
df_mes['Code_piece'] = df_mes['Code_piece'].str.strip()
df_mes = df_mes[df_mes['Code_piece'] != '']

print('Colonnes après explode MES:', df_mes.columns.tolist())
print('Temps Prévu présent?', 'Temps Prévu' in df_mes.columns)

# Étape 2 : Merge avec PLM
plm_renamed = plm.rename(columns={'Code / Référence': 'Code_piece'})
df_mes_plm = df_mes.merge(plm_renamed, on='Code_piece', how='left')

print('\nColonnes après merge PLM:', len(df_mes_plm.columns), 'colonnes')
print('Temps Prévu présent?', 'Temps Prévu' in df_mes_plm.columns)

# Étape 3 : ERP transform
pattern = re.compile(r'Semaine\s*(\d+)\s*:\s*Poste\s*(\d+)', flags=re.I)
rotation_rows = []
for _, row in erp.iterrows():
    rotation = row.get('Rotation', None)
    if pd.isna(rotation):
        continue
    for semaine, poste in pattern.findall(str(rotation)):
        rec = row.to_dict()
        rec['Semaine'] = int(semaine)
        rec['Poste'] = int(poste)
        rotation_rows.append(rec)

erp_long = pd.DataFrame(rotation_rows)
if 'Rotation' in erp_long.columns:
    erp_long = erp_long.drop(columns=['Rotation'])

print('\nColonnes ERP_long:', erp_long.columns.tolist())

# Étape 4 : Merge final
df_mes_plm['Poste'] = pd.to_numeric(df_mes_plm['Poste'], errors='coerce').astype('Int64')
erp_long['Poste'] = pd.to_numeric(erp_long['Poste'], errors='coerce').astype('Int64')

production_chains = df_mes_plm.merge(erp_long, on='Poste', how='left', suffixes=('', '_ERP'))

print('\nColonnes finales production_chains:', len(production_chains.columns), 'colonnes')
print('Temps Prévu présent?', 'Temps Prévu' in production_chains.columns)
if 'Temps Prévu' not in production_chains.columns:
    print('\nColonnes disponibles:', production_chains.columns.tolist())
