import pandas as pd
import numpy as np
import re
import plotly.express as px
import datetime

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
    fig.update_layout(xaxis_tickangle=-45)
 
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
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
<tr style="background-color:#f2f2f2;font-weight:bold;text-align:center;">
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
    Retourne un tableau HTML avec toutes les lignes où
    (Temps Réel - Temps Prévu) > 10 minutes.
    Les valeurs sont affichées en rouge.
    Retourne : string HTML
    """
 
    df = production_chains.copy()
 
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
 
    # Colonnes utiles
    cols = ["Poste", "Nom", "Temps Prévu", "Temps Réel", "Ecart_min", "Référence"]
    cols = [c for c in cols if c in retards.columns]
    retards = retards[cols]
 
    # Tri par poste puis par retard
    retards = (
        retards
        .sort_values(["Poste", "Ecart_min"], ascending=[True, False])
        .reset_index(drop=True)
    )
 
    # Construction HTML manuelle (rouge)
    html = """
<h2 style="color:red;">Postes avec un retard supérieur à 10 minutes</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
<tr style="background-color:#ffe5e5;font-weight:bold;text-align:center;">
<td>Poste</td>
<td>Opération</td>
<td>Temps prévu</td>
<td>Temps réel</td>
<td>Écart (min)</td>
<td>Références</td>
</tr>
    """
 
    for _, row in retards.iterrows():
        html += f"""
<tr style="color:red;">
<td><b>{row['Poste']}</b></td>
<td>{row['Nom']}</td>
<td>{row['Temps Prévu']}</td>
<td>{row['Temps Réel']}</td>
<td><b>{row['Ecart_min']:.1f}</b></td>
<td>{row.get('Référence', '')}</td>
</tr>
        """
 
    html += "</table>"
 
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
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;font-size:13px;">
    <tr style="background:#f2f2f2;font-weight:bold;text-align:center;">
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