import pandas as pd
import numpy as np
import re
import plotly.express as px
import datetime
import plotly.graph_objects as go
from urllib.parse import unquote

# ======================================================
# STYLE CONSTANT FOR UNIFIED TABLE STYLING
# ======================================================
TABLE_STYLE = 'border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; font-family: Arial; width: 100%;"'
TABLE_HEADER_STYLE = 'style="background-color:#f0f0f0;font-weight:bold;text-align:center;"'

# Helper function to style pandas to_html output
def style_pandas_table(html_str: str) -> str:
    """
    Stylise le HTML généré par pandas.to_html() pour qu'il soit cohérent avec les autres tableaux.
    """
    # Ajouter du CSS pour styliser la table
    styled_html = f"""
    <style>
        table {{
            border-collapse: collapse;
            font-family: Arial, sans-serif;
            width: 100%;
            border: 1px solid #ddd;
        }}
        th {{
            background-color: #f0f0f0;
            font-weight: bold;
            text-align: center;
            padding: 8px;
            border: 1px solid #ddd;
        }}
        td {{
            padding: 8px;
            border: 1px solid #ddd;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
    </style>
    {html_str}
    """
    return styled_html

# ======================================================
# 1. FONCTION DE FUSION : MES + PLM + ERP
# ======================================================

def build_production_chains(mes_path: str, plm_path: str, erp_path: str) -> pd.DataFrame:
    """
    Construit le DataFrame fusionné 'production_chains' à partir des 3 fichiers Excel.
 
    mes_path : chemin vers MES_Extraction.xlsx
    plm_path : chemin vers PLM_DataSet.xlsx
    erp_path : chemin vers ERP_Equipes Airplus.xlsx
 
    Retourne : DataFrame production_chains
        - 1 ligne = 1 opération MES * 1 pièce * (éventuellement 1 personne / semaine)
        - colonnes clés : Poste, Code_piece, Délai Approvisionnement, Nom (étape), Nom_personne, Semaine, etc.
    """
 
    # --- 1) Lecture des fichiers ---
    mes = pd.read_excel(mes_path)
    plm = pd.read_excel(plm_path)
    erp = pd.read_excel(erp_path)
 
    # --- 2) MES : exploser la colonne "Référence" en 1 ligne par pièce ---
    df_mes = mes.copy()
    df_mes["Code_piece"] = df_mes["Référence"].astype(str).str.split(";")
    df_mes = df_mes.explode("Code_piece")
    df_mes["Code_piece"] = df_mes["Code_piece"].str.strip()
    df_mes = df_mes[df_mes["Code_piece"] != ""]  # enlever les vides
 
    # --- 3) PLM : rejoindre sur "Code / Référence" ---
    plm_renamed = plm.rename(columns={"Code / Référence": "Code_piece"})
    df_mes_plm = df_mes.merge(plm_renamed, on="Code_piece", how="left")
 
    # --- 4) ERP : transformer "Rotation" en (Semaine, Poste) ---
    pattern = re.compile(r"Semaine\s*(\d+)\s*:\s*Poste\s*(\d+)", flags=re.I)
    rotation_rows = []
 
    for _, row in erp.iterrows():
        rotation = row.get("Rotation", None)
        if pd.isna(rotation):
            continue
 
        for semaine, poste in pattern.findall(str(rotation)):
            rec = row.to_dict()
            rec["Semaine"] = int(semaine)
            rec["Poste"] = int(poste)
            rotation_rows.append(rec)
 
    erp_long = pd.DataFrame(rotation_rows)
    if "Rotation" in erp_long.columns:
        erp_long = erp_long.drop(columns=["Rotation"])
 
    # Nom complet de la personne
    if {"Prénom", "Nom"}.issubset(erp_long.columns):
        erp_long["Nom_personne"] = (
            erp_long["Prénom"].fillna("").astype(str).str.strip()
            + " "
            + erp_long["Nom"].fillna("").astype(str).str.strip()
        ).str.strip()
    else:
        erp_long["Nom_personne"] = np.nan
 
    # Harmoniser les types de Poste
    df_mes_plm["Poste"] = pd.to_numeric(df_mes_plm["Poste"], errors="coerce").astype("Int64")
    erp_long["Poste"] = pd.to_numeric(erp_long["Poste"], errors="coerce").astype("Int64")
 
    # --- 5) Merge final MES+PLM avec ERP_long sur Poste ---
    production_chains = df_mes_plm.merge(
        erp_long,
        on="Poste",
        how="left",
        suffixes=("", "_ERP")
    )
 
    return production_chains

# ======================================================
# 2. UTILITAIRE COMMUN : parsing du délai d'appro
# ======================================================
 
def parse_delai_jours(val):
    """
    Transforme un texte type '15-20 jours' ou '30 jours'
    en nb de jours (float) en prenant la borne haute.
    """
    if pd.isna(val):
        return np.nan
    s = str(val)
    nums = re.findall(r"(\d+(?:[.,]\d+)?)", s)
    if not nums:
        return np.nan
    nums_float = [float(x.replace(",", ".")) for x in nums]
    return max(nums_float)

# ======================================================
# 3. VISU 1 : POSTE -> PIÈCES & DÉLAI D'APPRO (HTML)
# ======================================================
 
def html_poste_pieces(production_chains: pd.DataFrame, poste: int) -> str:
    """
    Génère un HTML contenant :
    - un tableau : pour le poste donné, liste des pièces + texte du délai d'appro + délai max en jours
    - un bar chart Plotly (délai appro en jours par pièce)
 
    Retourne : string HTML (à injecter côté front).
    """
 
    df = production_chains.copy()
 
    df_poste = df[df["Poste"] == poste]
    if df_poste.empty:
        return f"<p>Aucune donnée pour le poste {poste}.</p>"
 
    # Colonnes utiles
    cols = ["Poste", "Code_piece", "Délai Approvisionnement"]
    cols = [c for c in cols if c in df_poste.columns]
 
    df_small = (
        df_poste[cols]
        .dropna(subset=["Code_piece"])
        .drop_duplicates()
        .copy()
    )
 
    # Ajouter la version numérique en jours
    df_small["Delai_appro_jours"] = df_small["Délai Approvisionnement"].apply(parse_delai_jours)
 
    # Regrouper par pièce (au cas où plusieurs lignes)
    by_piece = (
        df_small
        .groupby("Code_piece", dropna=False)
        .agg({
            "Délai Approvisionnement": "first",
            "Delai_appro_jours": "max"
        })
        .reset_index()
        .sort_values("Delai_appro_jours", ascending=False)
    )
 
    # Tableau HTML
    table_html = by_piece.to_html(
        index=False,
        escape=False,
        border=1,
        justify="center",
        classes="table table-striped",
    )
    table_html = style_pandas_table(table_html)
 
    # Graphique Plotly
    fig = px.bar(
        by_piece,
        x="Code_piece",
        y="Delai_appro_jours",
        labels={
            "Code_piece": "Référence pièce",
            "Delai_appro_jours": "Délai appro (jours)"
        },
        title=f"Délai d'approvisionnement par pièce – Poste {poste}"
    )
    fig.update_layout(xaxis_tickangle=-45, height=500)
 
    graph_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
 
    # Wrapper global
    final_html = f"""
<h2>Poste {poste} – Références pièces & délais d'approvisionnement</h2>
    {table_html}
<br/>
    {graph_html}
    """
 
    return final_html

# ======================================================
# 4. VISU 2 : ÉTAPE -> POSTES -> EMPLOYÉS (HTML)
# ======================================================
 
def html_etape_postes_employes(production_chains: pd.DataFrame, etape: str | None = None) -> str:
    """
    Génère un HTML contenant :
    - un tableau hiérarchique Étape -> Poste -> Employé (Nb opérations),
      avec fusion visuelle (rowspan) pour Étape et Poste.
    - une heatmap Plotly Étape x Poste (nombre d'opérations).
 
    etape : 
        - None => toutes les étapes
        - "Assemblage aile gauche" => zoom sur cette étape
 
    Retourne : string HTML.
    """
 
    df = production_chains.copy()
 
    # Choix de la colonne contenant l'étape
    if "Nom" in df.columns:
        step_col = "Nom"
    elif "Nom_operation" in df.columns:
        step_col = "Nom_operation"
    else:
        return "<p>Colonne d'étape (Nom / Nom_operation) introuvable.</p>"
 
    # Filtre éventuel sur une étape précise
    if etape is not None:
        df = df[df[step_col] == etape]
        if df.empty:
            return f"<p>Aucune donnée pour l'étape : {etape}</p>"
 
    # Groupby Étape / Poste / Employé
    g = (
        df.groupby([step_col, "Poste", "Nom_personne"])
          .size()
          .reset_index(name="Nb_operations")
          .sort_values([step_col, "Poste", "Nom_personne"])
    )
 
    if g.empty:
        return "<p>Aucune donnée à afficher.</p>"
 
    # ---------- Construction du tableau HTML avec rowspan ----------
    html = """
<h2>Organisation par Étape → Poste → Employé</h2>
<table """ + TABLE_STYLE + """>
<tr """ + TABLE_HEADER_STYLE + """>
<td>Étape</td>
<td>Poste</td>
<td>Employé</td>
<td>Nb opérations</td>
</tr>
    """
 
    for step_name, df_step in g.groupby(step_col):
        step_rowspan = len(df_step)
        first_step_row = True
 
        for poste, df_poste in df_step.groupby("Poste"):
            poste_rowspan = len(df_poste)
            first_poste_row = True
 
            for _, row in df_poste.iterrows():
                html += "<tr>"
 
                # Étape (1 seule fois)
                if first_step_row:
                    html += (
                        f"<td rowspan='{step_rowspan}' "
                        f"style='font-weight:bold;vertical-align:top;'>{step_name}</td>"
                    )
                    first_step_row = False
 
                # Poste (1 seule fois)
                if first_poste_row:
                    html += (
                        f"<td rowspan='{poste_rowspan}' "
                        f"style='font-weight:bold;color:#444;vertical-align:top;'>{poste}</td>"
                    )
                    first_poste_row = False
 
                # Employé + Nb opérations
                html += f"<td>{row['Nom_personne']}</td>"
                html += f"<td style='text-align:right;'>{row['Nb_operations']}</td>"
 
                html += "</tr>"
 
    html += "</table>"
 
    # ---------- Heatmap Étape × Poste ----------
    try:
        pivot = (
            g.groupby([step_col, "Poste"])["Nb_operations"]
             .sum()
             .reset_index()
             .pivot(index=step_col, columns="Poste", values="Nb_operations")
             .fillna(0)
        )
 
        fig = px.imshow(
            pivot,
            labels={"x": "Poste", "y": "Étape", "color": "Nb opérations"},
            title="Répartition des opérations par Étape et Poste"
            if etape is None else f"Répartition des opérations par poste – {etape}"
        )
        fig.update_xaxes(side="top")
        fig.update_layout(height=500)
        heatmap_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
 
        html += "<br/>" + heatmap_html
    except Exception as e:
        # En cas de pb de heatmap, on renvoie quand même le tableau
        html += f"<!-- Heatmap non générée : {e} -->"
 
    return html

# ======================================================
# 5. VISU RETARDS > 10 MIN EN ROUGE (HTML)
# ======================================================
 
def html_retards_10min(production_chains: pd.DataFrame) -> str:
    """
    Retourne un tableau HTML avec tous les retards > 10 minutes par Poste.
    Affiche l'écart de retard, l'aléa industriel et la cause potentielle, triés par écart décroissant.
    Retourne : string HTML
    """
 
    df = production_chains.copy()

    # Vérifier que les colonnes requises existent
    if "Temps Prévu" not in df.columns or "Temps Réel" not in df.columns:
        return f"<p><b>Erreur :</b> Les colonnes 'Temps Prévu' ou 'Temps Réel' sont manquantes. Colonnes disponibles : {df.columns.tolist()}</p>"
 
    # --- Converter datetime.time -> timedelta ---
    def time_to_timedelta(x):
        if isinstance(x, datetime.time):
            return datetime.timedelta(
                hours=x.hour,
                minutes=x.minute,
                seconds=x.second
            )
        else:
            try:
                return pd.to_timedelta(x, errors="coerce")
            except:
                return pd.NaT
 
    # Conversion
    df["Temps_Reel_td"] = df["Temps Réel"].apply(time_to_timedelta)
    df["Temps_Prev_td"] = df["Temps Prévu"].apply(time_to_timedelta)
 
    # Écart
    df["Ecart"] = df["Temps_Reel_td"] - df["Temps_Prev_td"]
    df["Ecart_min"] = df["Ecart"].dt.total_seconds() / 60
 
    # Filtrer > 10 min
    retards = df[df["Ecart_min"] > 10].copy()
 
    if retards.empty:
        return "<p>Aucun retard supérieur à 10 minutes.</p>"
 
    # Grouper par Poste uniquement avec l'écart moyen et récupérer les aléas/causes
    retards_grouped = (
        retards
        .groupby("Poste", as_index=False)
        .agg({
            "Ecart_min": "mean",  # Écart moyen en minutes
            "Aléas Industriels": "first",  # Prendre le premier aléa
            "Cause Potentielle": "first"  # Prendre la première cause
        })
    )
    
    # Renommer pour clarté
    retards_grouped.columns = ['Poste', 'Ecart_moyen_min', 'Aléas Industriels', 'Cause Potentielle']
    
    # Remplacer les NaN par "Non renseigné"
    retards_grouped['Aléas Industriels'] = retards_grouped['Aléas Industriels'].fillna("Non renseigné")
    retards_grouped['Cause Potentielle'] = retards_grouped['Cause Potentielle'].fillna("Non renseignée")
 
    # Tri par écart décroissant
    retards_grouped = retards_grouped.sort_values('Ecart_moyen_min', ascending=False)
 
    # Construction HTML
    html = """
<h2 style="color:black;">Retards supérieurs à 10 minutes par Poste</h2>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; font-family: Arial; width: 100%;">
<tr style="background-color:#f0f0f0;font-weight:bold;text-align:center;color:black;">
<td>Poste</td>
<td>Écart moyen (min)</td>
<td>Aléa industriel</td>
<td>Cause potentielle</td>
</tr>
    """
 
    for _, row in retards_grouped.iterrows():
        html += f"""
<tr style="color:black;">
<td style="text-align:center;"><b>{row['Poste']}</b></td>
<td style="text-align:center;font-weight:bold;color:#d32f2f;">{row['Ecart_moyen_min']:.1f}</td>
<td>{row['Aléas Industriels']}</td>
<td>{row['Cause Potentielle']}</td>
</tr>
        """
 
    html += "</table>"
    
    # Créer un diagramme en barres horizontales pour les écarts par poste
    retards_sorted = retards_grouped.sort_values("Ecart_moyen_min", ascending=True)
    
    fig_retards = px.bar(
        retards_sorted,
        x="Ecart_moyen_min",
        y="Poste",
        labels={
            "Poste": "Poste",
            "Ecart_moyen_min": "Écart moyen (min)"
        },
        title="Écart moyen de retard par poste (>10 min)",
        color="Ecart_moyen_min",
        color_continuous_scale="Reds",
        orientation="h"
    )
    fig_retards.update_layout(
        height=max(400, len(retards_sorted) * 50),
        margin=dict(l=80, r=50, t=100, b=80),
        yaxis=dict(type="category")
    )
    fig_retards.update_xaxes(title_text="Écart moyen (minutes)")
    fig_retards.update_yaxes(title_text="Poste")
    graph_html = fig_retards.to_html(full_html=False, include_plotlyjs="cdn")
    
    html += graph_html
    html += f"""
<p style="margin-top:20px;font-size:0.9rem;color:#666;">
<b>Résumé :</b> {len(retards_grouped)} postes avec retards détectés | Total d'occurrences : {len(retards)} retards
</p>
    """
 
    return html


def html_step_details(mes: pd.DataFrame,
                      plm: pd.DataFrame,
                      erp: pd.DataFrame,
                      step_name: str) -> str:
    """
    Visualisation détaillée pour UNE étape de fabrication donnée (backend).
 
    Inputs
    ------
    mes : DataFrame (MES_Extraction)
        Colonnes attendues :
        - 'Nom' ou 'Nom_operation' : étape de production
        - 'Référence' : liste de références pièces (séparées par ';')
        - 'Temps Prévu'
        - 'Temps Réel'
        - éventuellement une colonne contenant 'CAO' pour le temps CAO
        - 'Poste'
 
    plm : DataFrame (PLM_DataSet)
        Colonnes :
        - 'Code / Référence'
        - 'Coût achat pièce (€)'
 
    erp : DataFrame (ERP_Equipes Airplus)
        Colonnes :
        - 'Rotation' : ex "Semaine 1: Poste 55 | Semaine 3: Poste 50"
        - 'Prénom', 'Nom'
        - 'Niveau d'expérience'
        - 'Coût horaire' (ou similaire)
 
    step_name : str
        Nom exact de l'étape (ex : "Assemblage queue avion")
 
    Retour
    ------
    html : str
        Bloc HTML complet avec :
        - nombre de pièces
        - coût des pièces
        - nombre de personnes
        - coût MO
        - coût total
        - temps prévu / réel / CAO
        - tableau des personnes impliquées
    """
 
    # =========================
    # 0) Colonne étape dans MES
    # =========================
    if "Nom" in mes.columns:
        step_col = "Nom"
    elif "Nom_operation" in mes.columns:
        step_col = "Nom_operation"
    else:
        return "<p><b>Impossible de trouver 'Nom' ou 'Nom_operation' dans MES.</b></p>"
 
    mes_step = mes[mes[step_col].astype(str).str.strip() == str(step_name).strip()].copy()
    if mes_step.empty:
        return f"<p><b>Aucune donnée dans MES pour l'étape : {step_name}</b></p>"
 
    # =========================
    # Utilitaire temps
    # =========================
    def time_to_td(x):
        if isinstance(x, datetime.time):
            return datetime.timedelta(hours=x.hour, minutes=x.minute, seconds=x.second)
        try:
            return pd.to_timedelta(x, errors="coerce")
        except Exception:
            return pd.NaT
 
    # ======================================================
    # 1) PIÈCES & COÛT PIÈCES (MES + PLM)
    # ======================================================
    mes_long = mes_step.copy()
    mes_long["Code_piece"] = mes_long["Référence"].astype(str).str.split(";")
    mes_long = mes_long.explode("Code_piece")
    mes_long["Code_piece"] = mes_long["Code_piece"].str.strip()
    mes_long = mes_long[mes_long["Code_piece"] != ""]
 
    nb_pieces = mes_long.shape[0]
 
    plm_renamed = plm.rename(columns={"Code / Référence": "Code_piece"})
    cols_plm = [c for c in ["Code_piece", "Coût achat pièce (€)"] if c in plm_renamed.columns]
    mes_plm_step = mes_long.merge(plm_renamed[cols_plm], on="Code_piece", how="left")
 
    if "Coût achat pièce (€)" in mes_plm_step.columns:
        mes_plm_step["_Cout_piece_num"] = (
            mes_plm_step["Coût achat pièce (€)"]
            .astype(str)
            .str.replace(",", ".", regex=False)
        )
        mes_plm_step["_Cout_piece_num"] = pd.to_numeric(
            mes_plm_step["_Cout_piece_num"], errors="coerce"
        )
        cout_pieces = mes_plm_step["_Cout_piece_num"].sum()
    else:
        cout_pieces = 0.0
 
    # ======================================================
    # 2) TEMPS PREVU / REEL / CAO (MES)
    # ======================================================
    # Temps prévu
    if "Temps Prévu" in mes_step.columns:
        mes_step["Temps_Prevu_td"] = mes_step["Temps Prévu"].apply(time_to_td)
        td_prev = mes_step["Temps_Prevu_td"].sum()
        h_prev = td_prev.total_seconds() / 3600 if pd.notna(td_prev) else 0
    else:
        td_prev = None
        h_prev = 0
 
    # Temps réel
    if "Temps Réel" in mes_step.columns:
        mes_step["Temps_Reel_td"] = mes_step["Temps Réel"].apply(time_to_td)
        td_reel = mes_step["Temps_Reel_td"].sum()
        h_reel = td_reel.total_seconds() / 3600 if pd.notna(td_reel) else 0
    else:
        td_reel = None
        h_reel = 0
 
    # Temps CAO
    cao_cols = [c for c in mes_step.columns if "cao" in c.lower()]
    cao_col = cao_cols[0] if cao_cols else None
    if cao_col is not None:
        mes_step["Temps_CAO_td"] = mes_step[cao_col].apply(time_to_td)
        td_cao = mes_step["Temps_CAO_td"].sum()
        h_cao = td_cao.total_seconds() / 3600 if pd.notna(td_cao) else 0
    else:
        td_cao = None
        h_cao = 0
    # ======================================================
    # 3) MAIN D'OEUVRE (MES + ERP via Poste)
    # ======================================================
    # Parse Rotation -> (Semaine, Poste)
    pattern = re.compile(r"Semaine\s*(\d+)\s*:\s*Poste\s*(\d+)", flags=re.I)
    rotation_rows = []
    for _, row in erp.iterrows():
        rotation = row.get("Rotation")
        if pd.isna(rotation):
            continue
        for semaine, poste in pattern.findall(str(rotation)):
            rec = row.to_dict()
            rec["Semaine"] = int(semaine)
            rec["Poste"] = int(poste)
            rotation_rows.append(rec)
 
    erp_long = pd.DataFrame(rotation_rows)
 
    if erp_long.empty:
        erp_long = pd.DataFrame(columns=["Poste", "Nom_personne", "Niveau d'expérience", "Coût horaire"])
 
    # Nom complet
    if {"Prénom", "Nom"}.issubset(erp_long.columns):
        erp_long["Nom_personne"] = (
            erp_long["Prénom"].fillna("").astype(str).str.strip()
            + " "
            + erp_long["Nom"].fillna("").astype(str).str.strip()
        ).str.strip()
    else:
        erp_long["Nom_personne"] = np.nan
 
    # Coût horaire
    hour_cols = [c for c in erp_long.columns if "horaire" in c.lower()]
    hour_col = hour_cols[0] if hour_cols else None
 
    # Niveau d'expérience
    exp_col = "Niveau d'expérience" if "Niveau d'expérience" in erp_long.columns else None
 
    # Merge MES_step + ERP_long sur Poste
    mes_emp = mes_step.copy()
    mes_emp["Poste"] = pd.to_numeric(mes_emp["Poste"], errors="coerce").astype("Int64")
    erp_long["Poste"] = pd.to_numeric(erp_long["Poste"], errors="coerce").astype("Int64")
 
    merge_cols = ["Poste", "Nom_personne"]
    if exp_col:
        merge_cols.append(exp_col)
    if hour_col:
        merge_cols.append(hour_col)
 
    mes_emp = mes_emp.merge(
        erp_long[merge_cols],
        on="Poste",
        how="left",
        suffixes=("", "_ERP"),
    )
 
    # Calcul coût MO
    personnes_details = []
    cout_mo_total = 0.0
    nb_personnes = 0
 
    if hour_col is not None and "Nom_personne" in mes_emp.columns:
        mes_emp[hour_col] = (
            mes_emp[hour_col]
            .astype(str)
            .str.replace(",", ".", regex=False)
        )
        mes_emp["_Taux_horaire_num"] = pd.to_numeric(mes_emp[hour_col], errors="coerce")
 
        if "Temps_Prevu_td" not in mes_emp.columns:
            mes_emp["Temps_Prevu_td"] = mes_emp["Temps Prévu"].apply(time_to_td)
 
        df_valid = mes_emp.dropna(subset=["Nom_personne", "Temps_Prevu_td", "_Taux_horaire_num"]).copy()
 
        if not df_valid.empty:
            grouped = (
                df_valid
                .groupby("Nom_personne")
                .agg(
                    Duree_totale=("Temps_Prevu_td", lambda x: x.sum()),
                    Taux_horaire=("_Taux_horaire_num", "first"),
                    Niveau_exp=(exp_col, "first") if exp_col else ("Nom_personne", "first")
                )
                .reset_index()
            )
 
            grouped["Heures_totales"] = grouped["Duree_totale"].dt.total_seconds() / 3600
            grouped["Cout_personne"] = grouped["Heures_totales"] * grouped["Taux_horaire"]
 
            cout_mo_total = grouped["Cout_personne"].sum()
            nb_personnes = grouped.shape[0]
 
            for _, r in grouped.iterrows():
                personnes_details.append({
                    "Nom": r["Nom_personne"],
                    "Niveau": r["Niveau_exp"] if exp_col else "",
                    "Heures": r["Heures_totales"],
                    "Taux": r["Taux_horaire"],
                    "Cout": r["Cout_personne"],
                })
 
            personnes_details = sorted(personnes_details, key=lambda x: x["Cout"], reverse=True)

    cout_total = cout_pieces + cout_mo_total
    
    def fmt_eur(x: float) -> str:
        return f"{x:,.2f} €".replace(",", " ").replace(".", ",")

    def fmt_td(td: datetime.timedelta | None) -> str:
        if td is None or pd.isna(td):
            return "-"
        return str(td)

    def fmt_h(x: float) -> str:
        return f"{x:.2f} h"

    # ======================================================
    # 5) Construction HTML (même style que la version Colab)
    # ======================================================
    card_style = (
        "flex:1 1 220px;"
        "border:1px solid #ddd;"
        "border-radius:6px;"
        "padding:12px;"
        "background:#fafafa;"
        "box-shadow:0 1px 3px rgba(0,0,0,0.06);"
    )
    wrap_style = "display:flex; gap:16px; flex-wrap:wrap; margin-bottom:16px;"

    html = f"""
    <div style="font-family:Arial, sans-serif; max-width:1100px;">
    <h2>Étape de fabrication : <span style="color:#0050b3;">{step_name}</span></h2>
    <p style="margin-top:0;color:#666;">Vue synthétique des pièces, personnes, coûts et temps.</p>

        <div style="{wrap_style}">
    <div style="{card_style}">
    <div style="color:#777;font-size:12px;">Nombre de pièces</div>
    <div style="font-size:22px;font-weight:bold;">{nb_pieces}</div>
    </div>

            <div style="{card_style}">
    <div style="color:#777;font-size:12px;">Coût pièces</div>
    <div style="font-size:22px;font-weight:bold;">{fmt_eur(cout_pieces)}</div>
    </div>

            <div style="{card_style}">
    <div style="color:#777;font-size:12px;">Nombre de personnes</div>
    <div style="font-size:22px;font-weight:bold;">{nb_personnes}</div>
    </div>

            <div style="{card_style}">
    <div style="color:#777;font-size:12px;">Coût main-d'œuvre</div>
    <div style="font-size:22px;font-weight:bold;">{fmt_eur(cout_mo_total)}</div>
    </div>

            <div style="{card_style}">
    <div style="color:#777;font-size:12px;">Coût total</div>
    <div style="font-size:22px;font-weight:bold;color:#c0392b;">{fmt_eur(cout_total)}</div>
    </div>
    </div>

        <div style="{wrap_style}">
    <div style="{card_style}">
    <div style="color:#777;font-size:12px;">Temps prévu cumulé</div>
    <div style="font-weight:bold;">{fmt_td(td_prev)}</div>
    <div style="font-size:11px;color:#555;">({fmt_h(h_prev)})</div>
    </div>

            <div style="{card_style}">
    <div style="color:#777;font-size:12px;">Temps réel cumulé</div>
    <div style="font-weight:bold;">{fmt_td(td_reel)}</div>
    <div style="font-size:11px;color:#555;">({fmt_h(h_reel)})</div>
    </div>

            <div style="{card_style}">
    <div style="color:#777;font-size:12px;">Temps CAO cumulé</div>
    <div style="font-weight:bold;">{fmt_td(td_cao)}</div>
    <div style="font-size:11px;color:#555;">({fmt_h(h_cao)})</div>
    </div>
    </div>

        <h3>Personnes impliquées</h3>
    <table """ + TABLE_STYLE + """>
    <tr """ + TABLE_HEADER_STYLE + """>
    <td>Nom</td>
    <td>Niveau</td>
    <td>Heures prévues</td>
    <td>Taux horaire</td>
    <td>Coût</td>
    </tr>
    """

    if personnes_details:
        for p in personnes_details:
            niv = p["Niveau"] if p["Niveau"] is not None else ""
            html += f"""
    <tr>
    <td>{p['Nom']}</td>
    <td style="text-align:center;">{niv}</td>
    <td style="text-align:right;">{fmt_h(p['Heures'])}</td>
    <td style="text-align:right;">{fmt_eur(p['Taux'])}</td>
    <td style="text-align:right;font-weight:bold;">{fmt_eur(p['Cout'])}</td>
    </tr>
            """
    else:
        html += """
    <tr>
    <td colspan="5" style="text-align:center;color:#888;">
                    Aucune information de main-d'œuvre exploitable pour cette étape.
    </td>
    </tr>
        """

    html += """
    </table>
    </div>
    """

    return html

# ======================================================
# 6. COÛTS PAR ÉTAPE (HTML)
# ======================================================

def html_costs_by_step(mes: pd.DataFrame,
                       plm: pd.DataFrame,
                       erp: pd.DataFrame) -> str:
    """
    Calcule les coûts par étape de production et renvoie un HTML contenant :
      - un tableau récapitulatif par étape
      - un camembert de répartition du coût TOTAL par étape
 
    Inputs
    ------
    mes : DataFrame (MES_Extraction)
        Colonnes attendues (noms à adapter si besoin) :
        - 'Nom' ou 'Nom_operation' : étape de production
        - 'Référence' : références pièces (séparées par ';')
        - 'Temps Prévu' : durée prévue (datetime.time ou 'HH:MM:SS')
        - 'Poste' : numéro de poste
 
    plm : DataFrame (PLM_DataSet)
        Colonnes :
        - 'Code / Référence' : code pièce
        - 'Coût achat pièce (€)' : coût d'achat de la pièce
 
    erp : DataFrame (ERP_Equipes Airplus)
        Colonnes :
        - 'Rotation' : ex "Semaine 1: Poste 55 | Semaine 3: Poste 50"
        - 'Prénom', 'Nom' : nom de l'employé
        - 'Coût horaire' (ou similaire) : taux horaire de l'employé
 
    Retour
    ------
    html : str
        HTML combinant tableau + camembert de répartition des coûts totaux.
    """
 
    # ======================================================
    # 1) Colonne étape de production
    # ======================================================
    if "Nom" in mes.columns:
        step_col = "Nom"
    elif "Nom_operation" in mes.columns:
        step_col = "Nom_operation"
    else:
        return "<p>Impossible de trouver la colonne 'Nom' (ou 'Nom_operation') dans MES.</p>"
 
    # ======================================================
    # 2) PARTIE PIECES (matière) : MES + PLM
    # ======================================================
 
    mes_long = mes.copy()
    mes_long["Code_piece"] = mes_long["Référence"].astype(str).str.split(";")
    mes_long = mes_long.explode("Code_piece")
    mes_long["Code_piece"] = mes_long["Code_piece"].str.strip()
    mes_long = mes_long[mes_long["Code_piece"] != ""]
 
    plm_renamed = plm.rename(columns={"Code / Référence": "Code_piece"})
    cols_plm_needed = ["Code_piece", "Coût achat pièce (€)"]
    cols_plm_needed = [c for c in cols_plm_needed if c in plm_renamed.columns]
 
    mes_plm_cost = mes_long.merge(
        plm_renamed[cols_plm_needed],
        on="Code_piece",
        how="left"
    )
 
    # Coût pièce en numérique
    if "Coût achat pièce (€)" in mes_plm_cost.columns:
        mes_plm_cost["Coût achat pièce (€)"] = (
            mes_plm_cost["Coût achat pièce (€)"]
            .astype(str)
            .str.replace(",", ".", regex=False)
        )
        mes_plm_cost["Coût achat pièce (€)"] = pd.to_numeric(
            mes_plm_cost["Coût achat pièce (€)"], errors="coerce"
        )
    else:
        mes_plm_cost["Coût achat pièce (€)"] = np.nan
 
    # Coût pièces par étape (somme de tous les coûts – doublons conservés)
    cost_pieces_by_step = (
        mes_plm_cost
        .groupby(step_col)["Coût achat pièce (€)"]
        .sum()
        .reset_index()
        .rename(columns={"Coût achat pièce (€)": "Cout_pieces"})
    )
 
    # Nombre de pièces (occurrences) par étape
    nb_pieces_by_step = (
        mes_plm_cost
        .groupby(step_col)["Code_piece"]
        .size()
        .reset_index(name="Nb_pieces")
    )
 
    # ======================================================
    # 3) TEMPS PREVU cumulé par étape (MES)
    # ======================================================
 
    def time_to_timedelta(x):
        # gère les datetime.time et les strings HH:MM:SS
        if isinstance(x, datetime.time):
            return datetime.timedelta(hours=x.hour, minutes=x.minute, seconds=x.second)
        try:
            return pd.to_timedelta(x, errors="coerce")
        except Exception:
            return pd.NaT
 
    mes_time = mes[[step_col, "Temps Prévu"]].copy()
    mes_time["Temps_Prevu_td"] = mes_time["Temps Prévu"].apply(time_to_timedelta)
 
    time_by_step = (
        mes_time
        .groupby(step_col)["Temps_Prevu_td"]
        .sum()
        .reset_index()
    )
    time_by_step["Temps_prevu_heures"] = time_by_step["Temps_Prevu_td"].dt.total_seconds() / 3600

    # 4) MAIN-D'ŒUVRE : MES + ERP (via Poste & Coût horaire)
    # ======================================================
 
    # 4.1 Parse de "Rotation" dans ERP -> (Semaine, Poste)
    pattern = re.compile(r"Semaine\s*(\d+)\s*:\s*Poste\s*(\d+)", flags=re.I)
    rotation_rows = []
    for _, row in erp.iterrows():
        rotation = row.get("Rotation")
        if pd.isna(rotation):
            continue
        for semaine, poste in pattern.findall(str(rotation)):
            rec = row.to_dict()
            rec["Semaine"] = int(semaine)
            rec["Poste"] = int(poste)
            rotation_rows.append(rec)
 
    erp_long = pd.DataFrame(rotation_rows)
    if erp_long.empty:
        # si on n'arrive pas à parser, on retournera des coûts main-d'œuvre à 0
        erp_long["Poste"] = []
        erp_long["Nom_personne"] = []
        erp_long["Coût horaire"] = []
 
    # Colonne coût horaire (on suppose "Coût horaire" dans ERP)
    hour_cols_erp = [c for c in erp_long.columns if "horaire" in c.lower()]
    hour_col = hour_cols_erp[0] if hour_cols_erp else None
 
    # Nom de la personne
    if {"Prénom", "Nom"}.issubset(erp_long.columns):
        erp_long["Nom_personne"] = (
            erp_long["Prénom"].fillna("").astype(str).str.strip()
            + " "
            + erp_long["Nom"].fillna("").astype(str).str.strip()
        ).str.strip()
    else:
        erp_long["Nom_personne"] = np.nan
 
    # 4.2 Join MES + ERP_long sur Poste
    mes_emp = mes.copy()
    mes_emp["Poste"] = pd.to_numeric(mes_emp["Poste"], errors="coerce").astype("Int64")
    erp_long["Poste"] = pd.to_numeric(erp_long["Poste"], errors="coerce").astype("Int64")
 
    cols_emp = [step_col, "Poste", "Temps Prévu"]
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
    mes_emp["Temps_Prevu_td"] = mes_emp["Temps Prévu"].apply(time_to_timedelta)
 
    # Conversion coût horaire
    if hour_col is not None and hour_col in mes_emp.columns:
        mes_emp[hour_col] = (
            mes_emp[hour_col]
            .astype(str)
            .str.replace(",", ".", regex=False)
        )
        mes_emp[hour_col] = pd.to_numeric(mes_emp[hour_col], errors="coerce")
 
    # 4.3 Coût main-d'œuvre par étape
    if hour_col is not None and "Nom_personne" in mes_emp.columns:
        df_emp = mes_emp.dropna(subset=[step_col, "Nom_personne", "Temps_Prevu_td", hour_col])
 
        grouped_emp = (
            df_emp
            .groupby([step_col, "Nom_personne"])
            .agg(
                Duree_totale=("Temps_Prevu_td", lambda x: x.sum()),
                Taux_horaire=(hour_col, "first")
            )
            .reset_index()
        )
        grouped_emp["Heures_totales"] = grouped_emp["Duree_totale"].dt.total_seconds() / 3600
        grouped_emp["Cout_personne"] = grouped_emp["Heures_totales"] * grouped_emp["Taux_horaire"]
 
        # coût main-d'œuvre par étape
        cost_emp_by_step = (
            grouped_emp
            .groupby(step_col)["Cout_personne"]
            .sum()
            .reset_index()
            .rename(columns={"Cout_personne": "Cout_main_oeuvre"})
        )
 
        # nb personnes distinctes par étape
        nb_personnes_by_step = (
            grouped_emp
            .groupby(step_col)["Nom_personne"]
            .nunique()
            .reset_index(name="Nb_personnes")
        )
    else:
        cost_emp_by_step = pd.DataFrame({step_col: [], "Cout_main_oeuvre": []})
        nb_personnes_by_step = pd.DataFrame({step_col: [], "Nb_personnes": []})
 
    # ======================================================
    # 5) FUSION DES INDICATEURS PAR ETAPE
    # ======================================================
 
    summary = (
        cost_pieces_by_step
        .merge(cost_emp_by_step, on=step_col, how="outer")
        .merge(time_by_step[[step_col, "Temps_Prevu_td", "Temps_prevu_heures"]], on=step_col, how="outer")
        .merge(nb_personnes_by_step, on=step_col, how="outer")
        .merge(nb_pieces_by_step, on=step_col, how="outer")
    )
 
    for col in ["Cout_pieces", "Cout_main_oeuvre", "Temps_prevu_heures", "Nb_personnes", "Nb_pieces"]:
        if col in summary.columns:
            summary[col] = summary[col].fillna(0)
 
    summary["Cout_total"] = summary["Cout_pieces"] + summary["Cout_main_oeuvre"]
 
    summary = summary.sort_values("Cout_total", ascending=False).reset_index(drop=True)
 
    # ======================================================
    # 6) FORMATAGE DU TABLEAU POUR AFFICHAGE
    # ======================================================
 
    colonnes_affichage = [
        step_col,
        "Temps_Prevu_td",
        "Temps_prevu_heures",
        "Nb_personnes",
        "Nb_pieces",
        "Cout_pieces",
        "Cout_main_oeuvre",
        "Cout_total",
    ]
    colonnes_affichage = [c for c in colonnes_affichage if c in summary.columns]
    table = summary[colonnes_affichage].copy()
 
    # Temps
    if "Temps_Prevu_td" in table.columns:
        table["Temps_Prevu_td"] = table["Temps_Prevu_td"].astype(str)
    if "Temps_prevu_heures" in table.columns:
        table["Temps_prevu_heures"] = table["Temps_prevu_heures"].apply(lambda x: f"{x:.2f} h")
 
    # Coûts
    for col in ["Cout_pieces", "Cout_main_oeuvre", "Cout_total"]:
        if col in table.columns:
            table[col] = table[col].apply(
                lambda x: f"{x:,.2f} €".replace(",", " ").replace(".", ",")
            )
 
    # Tableau HTML
    table_html = table.to_html(
        index=False,
        escape=False,
        border=1,
        justify="center"
    )
    table_html = style_pandas_table(table_html)
 
    # ======================================================
    # 7) CAMEMBERT REPARTITION DU COUT TOTAL
    # ======================================================
 
    # On repart de summary (numérique) pour le pie
    pie_data = summary[[step_col, "Cout_total"]].copy()
    pie_data["Cout_total"] = pie_data["Cout_total"].fillna(0)
    pie_data = pie_data[pie_data["Cout_total"] > 0]
 
    if pie_data.empty:
        pie_html = "<p>Aucun coût total non nul pour tracer le camembert.</p>"
    else:
        fig_cout = px.pie(
            pie_data,
            names=step_col,
            values="Cout_total",
            title="Répartition du coût TOTAL par étape de production"
        )
        fig_cout.update_traces(textposition="inside", textinfo="percent+label")
        fig_cout.update_layout(height=500)
        pie_html = fig_cout.to_html(full_html=False, include_plotlyjs="cdn")
 
    # ======================================================
    # 8) COMBINAISON TABLEAU + PIE EN HTML
    # ======================================================
 
    html = f"""
<h2>Coût par Étape de production</h2>
<p>
    - <b>{step_col}</b> : nom de l'étape de production (ex. "Assemblage aile gauche")<br>
    - <b>Temps_Prevu_td</b> : temps prévu cumulé (HH:MM:SS)<br>
    - <b>Temps_prevu_heures</b> : temps prévu cumulé en heures<br>
    - <b>Nb_personnes</b> : nombre de personnes ayant travaillé sur l'étape<br>
    - <b>Nb_pieces</b> : nombre de pièces (occurrences) utilisées sur l'étape<br>
    - <b>Cout_pieces</b> : coût total des pièces<br>
    - <b>Cout_main_oeuvre</b> : coût total main-d'œuvre<br>
    - <b>Cout_total</b> : coût global de l'étape (pièces + main-d'œuvre)
</p>
    {table_html}
<br/>
    {pie_html}
    """
 
    return html
 
def html_experience_by_week_step(production_chains: pd.DataFrame) -> str:
    """
    Retourne un tableau HTML :
    Semaine | Étape de production | Expert | Confirmé | Débutant | Total_personnes
 
    - Une personne n'est comptée qu'une seule fois par (Semaine, Étape, Niveau d'expérience)
    - Chaque ligne est colorée :
        * Vert  si >= 1/3 des personnes sont 'Expert'
        * Rouge sinon
    """
 
    # 1) Colonne d'étape de production
    if "Nom" in production_chains.columns:
        step_col = "Nom"
    elif "Nom_operation" in production_chains.columns:
        step_col = "Nom_operation"
    else:
        return "<p>Impossible de trouver la colonne 'Nom' (ou 'Nom_operation') dans production_chains.</p>"
 
    # 2) Vérifier les colonnes nécessaires
    required_cols = ["Semaine", step_col, "Nom_personne", "Niveau d'expérience"]
    missing = [c for c in required_cols if c not in production_chains.columns]
    if missing:
        return f"<p>Colonnes manquantes dans production_chains : {missing}</p>"
 
    # 3) Sous-dataframe propre
    df_exp = (
        production_chains[required_cols]
        .dropna(subset=["Semaine", step_col, "Nom_personne", "Niveau d'expérience"])
        .copy()
    )
 
    df_exp["Semaine"] = pd.to_numeric(df_exp["Semaine"], errors="coerce")
    df_exp = df_exp.dropna(subset=["Semaine"])
    df_exp["Semaine"] = df_exp["Semaine"].astype(int)
 
    df_exp[step_col] = df_exp[step_col].astype(str).str.strip()
    df_exp["Nom_personne"] = df_exp["Nom_personne"].astype(str).str.strip()
    df_exp["Niveau d'expérience"] = df_exp["Niveau d'expérience"].astype(str).str.strip()
 
    if df_exp.empty:
        return "<p>Aucune donnée exploitable pour semaines / étapes / niveaux d'expérience.</p>"
 
    # 4) Comptage des PERSONNES DISTINCTES par (Semaine, Étape, Niveau d'expérience)
    group = (
        df_exp
        .groupby(["Semaine", step_col, "Niveau d'expérience"])["Nom_personne"]
        .nunique()
        .reset_index(name="Nb_personnes")
    )
 
    if group.empty:
        return "<p>Aucune donnée agrégée (groupby vide).</p>"
 
    # 5) Pivot : une ligne = (Semaine, Étape), colonnes = niveaux d'expérience
    pivot = (
        group
        .pivot(index=["Semaine", step_col],
               columns="Niveau d'expérience",
               values="Nb_personnes")
        .fillna(0)
        .astype(int)
    )
 
    # Ordonner les colonnes de niveaux
    ordre_niveaux = ["Expert", "Confirmé", "Débutant"]
    cols_finales = [c for c in ordre_niveaux if c in pivot.columns]
    cols_autres = [c for c in pivot.columns if c not in cols_finales]
    pivot = pivot[cols_finales + cols_autres]
 
    # 6) Total par (Semaine, Étape)
    pivot["Total_personnes"] = pivot.sum(axis=1)
 
    # 7) Flatten index
    result = pivot.reset_index().sort_values(["Semaine", step_col])
    result = result.rename(columns={step_col: "Etape_de_production"})
 
    if result.empty:
        return "<p>Aucune donnée à afficher après agrégation.</p>"
 
    # ===============================
    # 8) Construction du HTML :
    #    - pas de colonne d'index
    #    - Semaine affichée une seule fois (rowspan)
    #    - lignes en vert/rouge selon % d'experts
    # ===============================
 
    html = """
<h3>Nombre de personnes par Semaine, Étape de production et niveau d'expérience</h3>
<table """ + TABLE_STYLE + """>
<tr """ + TABLE_HEADER_STYLE + """>
<td>Semaine</td>
<td>Étape de production</td>
<td>Expert</td>
<td>Confirmé</td>
<td>Débutant</td>
<td>Total_personnes</td>
</tr>
"""
 
    for semaine, df_sem in result.groupby("Semaine"):
        df_sem = df_sem.sort_values("Etape_de_production")
        rowspan = len(df_sem)
        first_row = True
 
        for _, row in df_sem.iterrows():
            expert = int(row["Expert"]) if "Expert" in result.columns else 0
            confirme = int(row["Confirmé"]) if "Confirmé" in result.columns else 0
            debutant = int(row["Débutant"]) if "Débutant" in result.columns else 0
            total = int(row["Total_personnes"])
 
            # Couleur de la ligne
            if total > 0 and expert >= total / 3:
                bgcolor = "background-color:#c6f7c3;"   # vert clair
            else:
                bgcolor = "background-color:#f7c3c3;"   # rouge clair
 
            html += f"<tr style='{bgcolor}'>"
 
            # Semaine affichée une seule fois
            if first_row:
                html += (
                    f"<td rowspan='{rowspan}' "
                    f"style='font-weight:bold;vertical-align:top;'>{semaine}</td>"
                )
                first_row = False
 
            html += f"<td>{row['Etape_de_production']}</td>"
            html += f"<td style='text-align:right;'>{expert}</td>"
            html += f"<td style='text-align:right;'>{confirme}</td>"
            html += f"<td style='text-align:right;'>{debutant}</td>"
            html += f"<td style='text-align:right;font-weight:bold;'>{total}</td>"
 
            html += "</tr>"
 
    html += "</table>"
 
    return html

#erreur a la ligne 290 j'ai enlevé un espace entre les deux points et le mot "reset_index"
def html_costs_by_step(mes: pd.DataFrame,
                       plm: pd.DataFrame,
                       erp: pd.DataFrame) -> str:
    """
    Calcule les coûts par étape de production et renvoie un HTML combinant tableau et graphiques.
    """

    # ======================================================
    # 0) NETTOYAGE PRÉALABLE DES COLONNES (Le Correctif)
    # ======================================================
    # On travaille sur des copies pour ne pas modifier les DF originaux hors de la fonction
    mes = mes.copy()
    plm = plm.copy()
    erp = erp.copy()

    # On supprime les espaces avant/après dans les noms de colonnes
    mes.columns = mes.columns.str.strip()
    plm.columns = plm.columns.str.strip()
    erp.columns = erp.columns.str.strip()
    
    # (Optionnel mais recommandé) On remplace les espaces insécables éventuels (\xa0) par des espaces simples
    mes.columns = mes.columns.str.replace('\xa0', ' ', regex=False)

    # ======================================================
    # 1) Colonne étape de production
    # ======================================================
    if "Nom" in mes.columns:
        step_col = "Nom"
    elif "Nom_operation" in mes.columns:
        step_col = "Nom_operation"
    else:
        # Debug : Affiche les colonnes trouvées pour comprendre l'erreur si elle persiste
        return f"<p>Impossible de trouver la colonne 'Nom'. Colonnes dispos : {list(mes.columns)}</p>"

    # Vérification de sécurité pour la colonne 'Temps Prévu'
    if "Temps Prévu" not in mes.columns:
        return f"<p>Erreur : Colonne 'Temps Prévu' introuvable. Colonnes dispos : {list(mes.columns)}</p>"

    # ======================================================
    # 2) PARTIE PIECES (matière) : MES + PLM
    # ======================================================

    mes_long = mes.copy()
    # Gestion sécurisée si la colonne Référence est vide ou NaN
    mes_long["Référence"] = mes_long["Référence"].astype(str).replace("nan", "")
    
    mes_long["Code_piece"] = mes_long["Référence"].str.split(";")
    mes_long = mes_long.explode("Code_piece")
    mes_long["Code_piece"] = mes_long["Code_piece"].str.strip()
    mes_long = mes_long[mes_long["Code_piece"] != ""]

    # Renommage PLM pour la jointure
    if "Code / Référence" in plm.columns:
        plm_renamed = plm.rename(columns={"Code / Référence": "Code_piece"})
    else:
        # Fallback si le nom est différent dans le PLM
        plm_renamed = plm.copy() 
    
    cols_plm_needed = ["Code_piece", "Coût achat pièce (€)"]
    # On ne garde que les colonnes qui existent vraiment
    cols_plm_needed = [c for c in cols_plm_needed if c in plm_renamed.columns]

    mes_plm_cost = mes_long.merge(
        plm_renamed[cols_plm_needed],
        on="Code_piece",
        how="left"
    )

    # Coût pièce en numérique
    if "Coût achat pièce (€)" in mes_plm_cost.columns:
        mes_plm_cost["Coût achat pièce (€)"] = (
            mes_plm_cost["Coût achat pièce (€)"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.replace("€", "", regex=False) # Au cas où le symbole € est dans la cellule
            .str.strip()
        )
        mes_plm_cost["Coût achat pièce (€)"] = pd.to_numeric(
            mes_plm_cost["Coût achat pièce (€)"], errors="coerce"
        )
    else:
        mes_plm_cost["Coût achat pièce (€)"] = np.nan

    # Coût pièces par étape
    cost_pieces_by_step = (
        mes_plm_cost
        .groupby(step_col)["Coût achat pièce (€)"]
        .sum()
        .reset_index()
        .rename(columns={"Coût achat pièce (€)": "Cout_pieces"})
    )

    # Nombre de pièces (occurrences) par étape
    nb_pieces_by_step = (
        mes_plm_cost
        .groupby(step_col)["Code_piece"]
        .size()
        .reset_index(name="Nb_pieces")
    )

    # ======================================================
    # 3) TEMPS PREVU cumulé par étape (MES)
    # ======================================================

    def time_to_timedelta(x):
        if pd.isna(x) or x == "":
            return pd.NaT
        if isinstance(x, datetime.time):
            return datetime.timedelta(hours=x.hour, minutes=x.minute, seconds=x.second)
        # Gestion du format string "HH:MM:SS" ou iso
        try:
            return pd.to_timedelta(str(x))
        except:
            return pd.NaT

    # Ici, grâce au nettoyage en étape 0, "Temps Prévu" devrait être accessible
    mes_time = mes[[step_col, "Temps Prévu"]].copy()
    mes_time["Temps_Prevu_td"] = mes_time["Temps Prévu"].apply(time_to_timedelta)

    time_by_step = (
        mes_time
        .groupby(step_col)["Temps_Prevu_td"]
        .sum()
        .reset_index()
    )
    # Conversion en heures (float)
    time_by_step["Temps_prevu_heures"] = time_by_step["Temps_Prevu_td"].dt.total_seconds() / 3600

    # ======================================================
    # 4) MAIN-D'ŒUVRE : MES + ERP
    # ======================================================

    # 4.1 Parse de "Rotation" dans ERP
    pattern = re.compile(r"Semaine\s*(\d+)\s*:\s*Poste\s*(\d+)", flags=re.I)
    rotation_rows = []
    
    # Vérification que la colonne Rotation existe
    if "Rotation" in erp.columns:
        for _, row in erp.iterrows():
            rotation = row.get("Rotation")
            if pd.isna(rotation):
                continue
            for semaine, poste in pattern.findall(str(rotation)):
                rec = row.to_dict()
                rec["Semaine"] = int(semaine)
                rec["Poste"] = int(poste)
                rotation_rows.append(rec)
    
    erp_long = pd.DataFrame(rotation_rows)
    
    if erp_long.empty:
        # Structure vide pour éviter plantage
        erp_long["Poste"] = []
        erp_long["Nom_personne"] = []
        erp_long["Coût horaire"] = []
    
    # Identification de la colonne Coût horaire
    hour_cols_erp = [c for c in erp_long.columns if "horaire" in c.lower() or "cout" in c.lower()]
    # On prend la colonne la plus probable qui n'est pas "Coût achat pièce"
    hour_col = None
    for c in hour_cols_erp:
        if "achat" not in c.lower():
            hour_col = c
            break

    # Nom complet
    if {"Prénom", "Nom"}.issubset(erp_long.columns):
        erp_long["Nom_personne"] = (
            erp_long["Prénom"].fillna("").astype(str).str.strip()
            + " "
            + erp_long["Nom"].fillna("").astype(str).str.strip()
        ).str.strip()
    else:
        erp_long["Nom_personne"] = np.nan

    # 4.2 Join MES + ERP_long sur Poste
    mes_emp = mes.copy()
    mes_emp["Poste"] = pd.to_numeric(mes_emp["Poste"], errors="coerce").astype("Int64")
    if not erp_long.empty:
        erp_long["Poste"] = pd.to_numeric(erp_long["Poste"], errors="coerce").astype("Int64")

    cols_emp = [step_col, "Poste", "Temps Prévu"]
    if hour_col:
        cols_emp.append(hour_col)
    if "Nom_personne" in erp_long.columns:
        cols_emp.append("Nom_personne")
    
    # On ne garde que les colonnes qui existent vraiment dans erp_long
    cols_emp_final = [c for c in cols_emp if c in erp_long.columns or c in [step_col, "Temps Prévu"]]
    
    # Pour le merge, il faut que Poste soit dans les deux
    if "Poste" in erp_long.columns:
         mes_emp = mes_emp.merge(
            erp_long[[c for c in cols_emp_final if c in erp_long.columns]],
            on="Poste",
            how="left",
            suffixes=("", "_ERP")
        )

    # Conversion Temps Prévu
    mes_emp["Temps_Prevu_td"] = mes_emp["Temps Prévu"].apply(time_to_timedelta)

    # Conversion coût horaire
    if hour_col and hour_col in mes_emp.columns:
        mes_emp[hour_col] = (
            mes_emp[hour_col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.replace("€/h", "", regex=False)
            .str.strip()
        )
        mes_emp[hour_col] = pd.to_numeric(mes_emp[hour_col], errors="coerce")

    # 4.3 Coût main-d'œuvre par étape
    if hour_col and "Nom_personne" in mes_emp.columns:
        df_emp = mes_emp.dropna(subset=[step_col, "Nom_personne", "Temps_Prevu_td", hour_col])

        grouped_emp = (
            df_emp
            .groupby([step_col, "Nom_personne"])
            .agg(
                Duree_totale=("Temps_Prevu_td", lambda x: x.sum()),
                Taux_horaire=(hour_col, "first")
            )
            .reset_index()
        )
        grouped_emp["Heures_totales"] = grouped_emp["Duree_totale"].dt.total_seconds() / 3600
        grouped_emp["Cout_personne"] = grouped_emp["Heures_totales"] * grouped_emp["Taux_horaire"]

        cost_emp_by_step = (
            grouped_emp
            .groupby(step_col)["Cout_personne"]
            .sum()
            .reset_index()
            .rename(columns={"Cout_personne": "Cout_main_oeuvre"})
        )
        
        nb_personnes_by_step = (
            grouped_emp
            .groupby(step_col)["Nom_personne"]
            .nunique()
            .reset_index(name="Nb_personnes")
        )
    else:
        cost_emp_by_step = pd.DataFrame({step_col: [], "Cout_main_oeuvre": []})
        nb_personnes_by_step = pd.DataFrame({step_col: [], "Nb_personnes": []})

    # ======================================================
    # 5) FUSION DES INDICATEURS PAR ETAPE
    # ======================================================

    summary = (
        cost_pieces_by_step
        .merge(cost_emp_by_step, on=step_col, how="outer")
        .merge(time_by_step[[step_col, "Temps_Prevu_td", "Temps_prevu_heures"]], on=step_col, how="outer")
        .merge(nb_personnes_by_step, on=step_col, how="outer")
        .merge(nb_pieces_by_step, on=step_col, how="outer")
    )

    for col in ["Cout_pieces", "Cout_main_oeuvre", "Temps_prevu_heures", "Nb_personnes", "Nb_pieces"]:
        if col in summary.columns:
            summary[col] = summary[col].fillna(0)

    summary["Cout_total"] = summary["Cout_pieces"] + summary["Cout_main_oeuvre"]
    summary = summary.sort_values("Cout_total", ascending=False).reset_index(drop=True)

    # ======================================================
    # 6) FORMATAGE DU TABLEAU POUR AFFICHAGE
    # ======================================================
    
    colonnes_affichage = [
        step_col,
        "Temps_Prevu_td",
        "Temps_prevu_heures",
        "Nb_personnes",
        "Nb_pieces",
        "Cout_pieces",
        "Cout_main_oeuvre",
        "Cout_total",
    ]
    colonnes_affichage = [c for c in colonnes_affichage if c in summary.columns]
    table = summary[colonnes_affichage].copy()

    # Formatage Temps (suppression des jours si < 1 jour pour propreté)
    if "Temps_Prevu_td" in table.columns:
         table["Temps_Prevu_td"] = table["Temps_Prevu_td"].astype(str).str.replace("0 days ", "")

    if "Temps_prevu_heures" in table.columns:
        table["Temps_prevu_heures"] = table["Temps_prevu_heures"].apply(lambda x: f"{x:.2f} h")
    
    # Formatage Monétaire
    for col in ["Cout_pieces", "Cout_main_oeuvre", "Cout_total"]:
        if col in table.columns:
            table[col] = table[col].apply(
                lambda x: f"{x:,.2f} €".replace(",", " ").replace(".", ",")
            )

    table_html = table.to_html(
        index=False,
        escape=False,
        border=1,
        justify="center",
        classes="table table-striped" # Ajout classe CSS standard si dispo
    )
    table_html = style_pandas_table(table_html)

    # ======================================================
    # 7) CAMEMBERT REPARTITION DU COUT TOTAL
    # ======================================================
    pie_data = summary[[step_col, "Cout_total"]].copy()
    pie_data["Cout_total"] = pie_data["Cout_total"].fillna(0)
    pie_data = pie_data[pie_data["Cout_total"] > 0]

    if pie_data.empty:
        pie_html = "<p>Aucun coût total > 0 pour tracer le camembert.</p>"
    else:
        fig_cout = px.pie(
            pie_data,
            names=step_col,
            values="Cout_total",
            title="Répartition du coût TOTAL par étape"
        )
        fig_cout.update_traces(textposition="inside", textinfo="percent+label")
        fig_cout.update_layout(height=500)
        pie_html = fig_cout.to_html(full_html=False, include_plotlyjs="cdn")

    html = f"""
    <div style="font-family: Arial, sans-serif;">
        <h2>Détail des Coûts par Étape</h2>
        <p><i>Note : Les colonnes ont été nettoyées automatiquement (espaces supprimés).</i></p>
        {table_html}
        <br/>
        <hr>
        {pie_html}
    </div>
    """

    return html

def html_step_workflow(
    production_chains: pd.DataFrame,
    selected_step: str | None = None,
    max_nodes_per_level: int = 50,
) -> str:
    """
    Retourne un graphe Sankey (au format HTML) corrigé pour gérer les caractères URL (%20).
    """

    df = production_chains.copy()

    # ======================================================
    # 0) Nettoyage préventif des colonnes et des données
    # ======================================================
    # Nettoie les noms de colonnes (enlève les espaces invisibles à la fin)
    df.columns = df.columns.str.strip()

    # 1) Choix de la colonne d'étape
    if "Nom" in df.columns:
        step_col = "Nom"
    elif "Nom_operation" in df.columns:
        step_col = "Nom_operation"
    else:
        return f"<p>Impossible de trouver la colonne 'Nom' ou 'Nom_operation'. Colonnes dispos : {list(df.columns)}</p>"

    # On nettoie le contenu de la colonne étape (enlève les espaces autour)
    # pour être sûr que "Assemblage " devienne "Assemblage"
    df[step_col] = df[step_col].astype(str).str.strip()

    # ======================================================
    # 2) Filtre sur une étape (avec DÉCODAGE URL)
    # ======================================================
    if selected_step is not None:
        # CORRECTION : Transforme "Assemblage%20aile%20droite" en "Assemblage aile droite"
        clean_step = unquote(str(selected_step)).strip()
        
        # Filtrage
        df = df[df[step_col] == clean_step]
        
        if df.empty:
            # Debug : Affiche ce qu'on cherchait vs ce qu'il y a dans la colonne
            first_vals = df[step_col].unique()[:3] if not production_chains.empty else "DF vide"
            return (f"<p>Aucune donnée pour l'étape : <b>{clean_step}</b> (reçu : {selected_step})<br>"
                    f"Vérifiez l'orthographe exacte dans le fichier Excel.<br>"
                    f"Exemples de valeurs disponibles : {production_chains[step_col].unique()[:5]}</p>")

    # 3) On garde uniquement les lignes complètes
    # On vérifie d'abord que les colonnes existent
    required_cols = [step_col, "Poste", "Code_piece"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        return f"<p>Colonnes manquantes dans le DataFrame : {missing}</p>"

    df = df.dropna(subset=required_cols)
    
    # Nettoyage des colonnes Poste et Code_piece
    df["Poste"] = df["Poste"].astype(str).str.strip()
    df["Code_piece"] = df["Code_piece"].astype(str).str.strip()

    if df.empty:
        return "<p>Aucune donnée à afficher après nettoyage des valeurs nulles.</p>"

    # Debug : Vérifier les colonnes
    print(f"[DEBUG Sankey] Colonnes du DataFrame : {list(df.columns)}")
    print(f"[DEBUG Sankey] Nombre de lignes : {len(df)}")
    print(f"[DEBUG Sankey] Colonnes requises : {['Nom', 'Poste', 'Code_piece']}")

    # ======================
    # 4. Définition des noeuds
    # =====================

    # Étapes
    steps = df[step_col].unique().tolist()
    # (Logique de limitation des noeuds inchangée)
    if len(steps) > max_nodes_per_level:
        top_steps = (
            df.groupby(step_col)
              .size()
              .sort_values(ascending=False)
              .head(max_nodes_per_level)
              .index.tolist()
        )
        steps = top_steps
        df = df[df[step_col].isin(steps)]
    step_labels = [f"Étape : {s}" for s in steps]

    # Postes
    postes = sorted(df["Poste"].unique())
    print(f"[DEBUG Sankey] Étapes trouvées : {len(steps)} | Postes trouvés : {len(postes)}")
    
    if len(postes) > max_nodes_per_level:
        top_postes = (
            df.groupby("Poste")
              .size()
              .sort_values(ascending=False)
              .head(max_nodes_per_level)
              .index.tolist()
        )
        postes = top_postes
        df = df[df["Poste"].isin(postes)]
    poste_labels = [f"Poste {p}" for p in postes]

    # Pièces
    pieces = df["Code_piece"].unique().tolist()
    if len(pieces) > max_nodes_per_level:
        top_pieces = (
            df.groupby("Code_piece")
              .size()
              .sort_values(ascending=False)
              .head(max_nodes_per_level)
              .index.tolist()
        )
        pieces = top_pieces
        df = df[df["Code_piece"].isin(pieces)]
    piece_labels = [f"Pièce : {c}" for c in pieces]

    # ======================
    # 5. Indexation des noeuds
    # ======================

    labels = step_labels + poste_labels + piece_labels

    idx_step = {s: i for s, i in zip(steps, range(len(step_labels)))}
    offset_poste = len(step_labels)
    idx_poste = {p: offset_poste + i for p, i in zip(postes, range(len(postes)))}
    offset_piece = offset_poste + len(postes)
    idx_piece = {c: offset_piece + i for c, i in zip(pieces, range(len(pieces)))}

    # ======================
    # 6. Construction des liens (edges)
    # ======================

    sources = []
    targets = []
    values = []

    # 6.1 Étape -> Poste
    df_ep = (
        df[df["Poste"].isin(postes) & df[step_col].isin(steps)]
        .groupby([step_col, "Poste"])
        .size()
        .reset_index(name="val")
    )
    for _, row in df_ep.iterrows():
        etape = row[step_col]
        poste = row["Poste"]
        if etape in idx_step and poste in idx_poste:
            sources.append(idx_step[etape])
            targets.append(idx_poste[poste])
            values.append(row["val"])

    # 6.2 Poste -> Pièce
    df_pp = (
        df[df["Poste"].isin(postes) & df["Code_piece"].isin(pieces)]
        .groupby(["Poste", "Code_piece"])
        .size()
        .reset_index(name="val")
    )
    for _, row in df_pp.iterrows():
        poste = row["Poste"]
        piece = row["Code_piece"]
        if poste in idx_poste and piece in idx_piece:
            sources.append(idx_poste[poste])
            targets.append(idx_piece[piece])
            values.append(row["val"])

    print(f"[DEBUG Sankey] Sources : {len(sources)} | Targets : {len(targets)} | Values : {len(values)}")
    
    if not sources:
        return f"<p>Pas de liens à afficher (sources/targets vides).<br>Étapes: {len(steps)}, Postes: {len(postes)}, Pièces: {len(pieces)}</p>"

    # ... (votre code précédent reste identique jusqu'à la fin)

    # 7. Création de la figure Plotly
    # ======================
    link = dict(source=sources, target=targets, value=values)
    node = dict(label=labels, pad=15, thickness=15)

    titre = "Workflow Étape (Nom MES) → Poste → Pièce"
    if selected_step is not None:
        titre += f" — {unquote(str(selected_step))}"

    fig = go.Figure(data=[go.Sankey(node=node, link=link)])
    fig.update_layout(
        title_text=titre, 
        font_size=10,
        height=700,
        margin=dict(l=10, r=10, t=40, b=10), # Marges légèrement ajustées
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # CORRECTION ICI : Passer full_html à True pour générer une page autonome
    # Cela permet à l'iframe (voir étape 2) de charger correctement les scripts
    html = fig.to_html(full_html=True, include_plotlyjs="cdn")
    
    return html