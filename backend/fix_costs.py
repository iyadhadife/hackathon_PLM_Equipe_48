import re

# Lire le fichier
with open('scripts.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver la deuxième occurrence de html_costs_by_step (la vraie fonction)
pattern = r'#erreur a la ligne 290.*?def html_costs_by_step.*?(?=\ndef [a-z_]+\(|$)'

match = re.search(pattern, content, re.DOTALL)
if match:
    func_start = match.start()
    func_content = match.group(0)
    
    # Corriger la fonction
    # 1. Ajouter la vérification initiale
    func_content = func_content.replace(
        '    else:\n        return "<p>Impossible de trouver la colonne \'Nom\' (ou \'Nom_operation\') dans MES.</p>"',
        '''    else:
        return "<p>Impossible de trouver la colonne 'Nom' (ou 'Nom_operation') dans MES.</p>"
    
    # Vérifier la présence de 'Temps Prévu' dès le début
    has_temps_prevu = "Temps Prévu" in mes.columns'''
    )
    
    # 2. Corriger la section 3 (TEMPS PREVU)
    old_section3 = '''    mes_time = mes[[step_col, "Temps Prévu"]].copy()
    mes_time["Temps_Prevu_td"] = mes_time["Temps Prévu"].apply(time_to_timedelta)
 
    time_by_step = (
        mes_time
        .groupby(step_col)["Temps_Prevu_td"]
        .sum()
        .reset_index()
    )
    time_by_step["Temps_prevu_heures"] = time_by_step["Temps_Prevu_td"].dt.total_seconds() / 3600'''
    
    new_section3 = '''    # Calculer les temps seulement si la colonne existe
    if has_temps_prevu:
        mes_time = mes[[step_col, "Temps Prévu"]].copy()
        mes_time["Temps_Prevu_td"] = mes_time["Temps Prévu"].apply(time_to_timedelta)
     
        time_by_step = (
            mes_time
            .groupby(step_col)["Temps_Prevu_td"]
            .sum()
            .reset_index()
        )
        time_by_step["Temps_prevu_heures"] = time_by_step["Temps_Prevu_td"].dt.total_seconds() / 3600
    else:
        # Créer un DataFrame vide si pas de temps prévu
        time_by_step = pd.DataFrame({
            step_col: [],
            "Temps_Prevu_td": pd.Series([], dtype='timedelta64[ns]'),
            "Temps_prevu_heures": []
        })'''
    
    func_content = func_content.replace(old_section3, new_section3, 1)
    
    # 3. Corriger la section 4.2 (cols_emp)
    old_section4 = '''    cols_emp = [step_col, "Poste", "Temps Prévu"]
    if hour_col is not None:
        cols_emp.append(hour_col)
    cols_emp.append("Nom_personne")
 
    mes_emp = mes_emp.merge(
        erp_long[cols_emp],
        on="Poste",
        how="left",
        suffixes=("", "_ERP")
    )
 
    # Conversion Temps Prévu
    mes_emp["Temps_Prevu_td"] = mes_emp["Temps Prévu"].apply(time_to_timedelta)'''
    
    new_section4 = '''    # Construire cols_emp seulement avec les colonnes qui existent dans erp_long
    cols_to_merge_from_erp = ["Poste"]
    if hour_col is not None and hour_col in erp_long.columns:
        cols_to_merge_from_erp.append(hour_col)
    if "Nom_personne" in erp_long.columns:
        cols_to_merge_from_erp.append("Nom_personne")
 
    mes_emp = mes_emp.merge(
        erp_long[cols_to_merge_from_erp],
        on="Poste",
        how="left",
        suffixes=("", "_ERP")
    )
 
    # Conversion Temps Prévu seulement s'il existe
    if has_temps_prevu:
        mes_emp["Temps_Prevu_td"] = mes_emp["Temps Prévu"].apply(time_to_timedelta)
    else:
        mes_emp["Temps_Prevu_td"] = pd.NaT'''
    
    func_content = func_content.replace(old_section4, new_section4, 1)
    
    # Remplacer dans le contenu original
    new_content = content[:func_start] + func_content + content[func_start + len(match.group(0)):]
    
    # Écrire le fichier corrigé
    with open('scripts.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Fonction html_costs_by_step corrigée avec succès!")
else:
    print("❌ Fonction html_costs_by_step non trouvée")
