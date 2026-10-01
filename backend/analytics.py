"""
analytics.py — Analyses croisées MES × PLM × ERP
=================================================

Chaque fonction `html_analyse_*` renvoie une page HTML autonome (Plotly.js via CDN)
affichable dans l'iframe du frontend, comme les autres routes de `scripts.py`.

Modèle de données (clés de jointure) :
    MES.Référence  (liste "A511;A337;…")  ──►  PLM."Code / Référence"   (pièces)
    MES.Poste      (1..56)                ──►  ERP."Poste de montage"   ("Poste N", équipe titulaire)
    MES.Date + Heure Début/Fin            ──►  chronologie réelle

Indicateurs dérivés :
    - dépassement (min / %)        = Temps Réel − Temps Prévu                 (MES)
    - valeur pièces engagées (€)   = Σ coût achat des pièces consommées      (MES × PLM)
    - criticité / délai appro max  = pire pièce consommée par l'opération    (MES × PLM)
    - coût MO réel / surcoût (€)   = Σ coût horaire équipe × durée           (MES × ERP)
    - score expérience équipe      = Débutant=1, Confirmé=2, Expert=3        (ERP)

Aucune dépendance autre que pandas / numpy (les graphiques sont générés en JSON
pour Plotly.js côté navigateur).
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re

import numpy as np
import pandas as pd

# ======================================================
# 0. CONSTANTES DE STYLE (palette validée, mode clair)
# ======================================================

C = {
    "surface": "#fcfcfb",
    "text": "#0b0b0b",
    "text2": "#52514e",
    "muted": "#8a8984",
    "grid": "#e8e7e3",
    "border": "#dedcd6",
    # catégoriel (ordre fixe)
    "s1": "#2a78d6",  # bleu
    "s2": "#eb6834",  # orange
    "s3": "#1baf7a",  # aqua
    # séquentiel bleu
    "seq": ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"],
    "seq_light": "#9ec5f4",
    "seq_dark": "#256abf",
}

# Criticité PLM -> couleur de statut (toujours accompagnée de son libellé)
CRIT_ORDER = ["Basse", "Moyenne", "Haute", "Critique"]
CRIT_COLOR = {"Basse": "#0ca30c", "Moyenne": "#fab219", "Haute": "#ec835a", "Critique": "#d03b3b"}
CRIT_WEIGHT = {"Basse": 1, "Moyenne": 2, "Haute": 3, "Critique": 4}

EXP_SCORE = {"Débutant": 1, "Confirmé": 2, "Expert": 3}

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"

# Catégorisation des aléas industriels (mots-clés -> famille)
ALEA_FAMILLES = [
    ("Environnement atelier", ["température", "thermique", "ventilation", "climatisation", "refroidissement",
                                "surchauffe", "contamination", "pression", "vibration"]),
    ("Systèmes d'information & automatismes", ["logiciel", "réseau", "synchronisation", "désynchronisation",
                                               "communication", "traçabilité", "référencement", "robots",
                                               "automatis", "guidage", "protocoles"]),
    ("Qualité & métrologie", ["qualité", "calibration", "contrôle", "paramètres", "positionnement",
                              "placement", "adhérence", "marquage", "impression"]),
    ("Outillage & usure équipements", ["outillage", "usure", "gabarit", "serrage", "soudure",
                                        "lubrification", "déformation", "supports"]),
    ("Électrique", ["électrique", "connectique"]),
    ("Logistique & manutention", ["manutention", "transport"]),
    ("Maintenance & défaillances majeures", ["maintenance", "défaillance majeure"]),
]

CAUSE_THEMES = [
    ("Maintenance insuffisante / différée", ["maintenance", "intervalles", "planning"]),
    ("Vétusté / obsolescence", ["obsolète", "obsolescence", "vieillissement", "vétusté", "fin de vie",
                                "usé", "usure", "sous-investissement", "dégradé"]),
    ("Procédures / formation", ["procédure", "formation", "non respectées"]),
    ("Systèmes d'information / logiciels", ["système d'information", "logiciel", "bugs", "programmation",
                                            "mise à jour", "protocole", "interfaces", "communication", "réseau"]),
    ("Régulation / environnement", ["régulation", "environnement", "filtration", "filtres", "climatisation",
                                    "isolation", "refroidissement", "thermique", "température", "anti-vibration"]),
    ("Capteurs / étalonnage", ["capteur", "étalonnage", "instruments", "calibration", "dérive"]),
    ("Matériaux / consommables", ["matériaux", "lubrifiant", "oxydation", "qualité matériaux"]),
    ("Cadence / cycles intensifs", ["cycles intensifs", "cycles répétitifs", "contraintes"]),
]


# ======================================================
# 1. CHARGEMENT & CONSTRUCTION DU MODÈLE CROISÉ
# ======================================================

def _to_minutes(x) -> float:
    """datetime.time / timedelta / 'HH:MM:SS' -> minutes (float)."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return np.nan
    if isinstance(x, dt.time):
        return x.hour * 60 + x.minute + x.second / 60
    if isinstance(x, (dt.timedelta, pd.Timedelta)):
        return x.total_seconds() / 60
    try:
        return pd.to_timedelta(str(x)).total_seconds() / 60
    except Exception:
        return np.nan


def _to_time(x):
    if isinstance(x, dt.time):
        return x
    try:
        return pd.to_datetime(str(x)).time()
    except Exception:
        return None


def _parse_delai_max(val) -> float:
    if pd.isna(val):
        return np.nan
    nums = re.findall(r"(\d+(?:[.,]\d+)?)", str(val))
    return max(float(n.replace(",", ".")) for n in nums) if nums else np.nan


def _famille(text: str, familles) -> str:
    t = str(text).lower()
    for name, kws in familles:
        if any(k in t for k in kws):
            return name
    return "Autres"


def _themes(text: str) -> list[str]:
    t = str(text).lower()
    return [name for name, kws in CAUSE_THEMES if any(k in t for k in kws)] or ["Autres"]


def load_sources(folder: str = "uploads"):
    mes = pd.read_excel(os.path.join(folder, "MES_Extraction.xlsx"))
    plm = pd.read_excel(os.path.join(folder, "PLM_DataSet.xlsx"))  # 1ère feuille
    erp = pd.read_excel(os.path.join(folder, "ERP_Equipes_Airplus.xlsx"))
    for df in (mes, plm, erp):
        df.columns = df.columns.str.strip()
    return mes, plm, erp


def build_model(mes: pd.DataFrame, plm: pd.DataFrame, erp: pd.DataFrame):
    """
    Retourne (ops, pieces, staff) :
      ops    : 1 ligne = 1 opération MES enrichie PLM + ERP
      pieces : 1 ligne = 1 pièce PLM enrichie de sa consommation MES
      staff  : ERP + numéro de poste + score d'expérience
    """
    # ---------- ERP ----------
    staff = erp.copy()
    staff["Poste_num"] = pd.to_numeric(
        staff["Poste de montage"].astype(str).str.extract(r"(\d+)")[0], errors="coerce"
    ).astype("Int64")
    staff["Exp_score"] = staff["Niveau d'expérience"].map(EXP_SCORE)
    staff["Nom_complet"] = (staff["Prénom"].astype(str) + " " + staff["Nom"].astype(str)).str.strip()

    team = staff.groupby("Poste_num").agg(
        Nb_operateurs=("Matricule", "count"),
        Cout_horaire_equipe=("Coût horaire (€)", "sum"),
        Exp_moyenne=("Exp_score", "mean"),
        Nb_debutants=("Niveau d'expérience", lambda s: int((s == "Débutant").sum())),
        Nb_experts=("Niveau d'expérience", lambda s: int((s == "Expert").sum())),
        Age_moyen=("Âge", "mean"),
        Equipe=("Nom_complet", lambda s: ", ".join(s)),
        Niveaux=("Niveau d'expérience", lambda s: ", ".join(s)),
    ).reset_index().rename(columns={"Poste_num": "Poste"})

    # ---------- PLM ----------
    p = plm.rename(columns={"Code / Référence": "Code"}).copy()
    p["Code"] = p["Code"].astype(str).str.strip()
    p["Delai_max_j"] = p["Délai Approvisionnement"].apply(_parse_delai_max)
    p["Crit_w"] = p["Criticité"].map(CRIT_WEIGHT).fillna(0)
    p = p.drop_duplicates("Code")

    # ---------- MES ----------
    ops = mes.copy()
    ops["Prevu_min"] = ops["Temps Prévu"].apply(_to_minutes)
    ops["Reel_min"] = ops["Temps Réel"].apply(_to_minutes)
    ops["Ecart_min"] = ops["Reel_min"] - ops["Prevu_min"]
    ops["Ecart_pct"] = ops["Ecart_min"] / ops["Prevu_min"] * 100
    d = pd.to_datetime(ops["Date"])
    ops["Debut"] = [pd.Timestamp.combine(a.date(), _to_time(b)) if _to_time(b) else pd.NaT
                    for a, b in zip(d, ops["Heure Début"])]
    ops["Fin"] = ops["Debut"] + pd.to_timedelta(ops["Reel_min"], unit="m")
    ops["Famille_alea"] = ops["Aléas Industriels"].apply(lambda t: _famille(t, ALEA_FAMILLES))

    # explosion des références -> 1 ligne par pièce consommée
    long = ops[["Poste", "Nom", "Référence"]].copy()
    long["Code"] = long["Référence"].fillna("").astype(str).str.split(";")
    long = long.explode("Code")
    long["Code"] = long["Code"].str.strip()
    long = long[long["Code"] != ""].merge(p, on="Code", how="left")

    agg = long.groupby("Poste").agg(
        Valeur_pieces=("Coût achat pièce (€)", "sum"),
        Masse_kg=("Masse (kg)", "sum"),
        Crit_max_w=("Crit_w", "max"),
        Delai_max_j=("Delai_max_j", "max"),
        Nb_refs=("Code", "nunique"),
        Nb_pieces_critiques=("Criticité", lambda s: int(s.isin(["Critique", "Haute"]).sum())),
        Temps_CAO_h=("Temps CAO (h)", "sum"),
        Fournisseurs=("Fournisseur", lambda s: ", ".join(sorted(set(s.dropna())))),
        Pieces=("Code", lambda s: ", ".join(f"{c}×{n}" for c, n in s.value_counts().items())),
    ).reset_index()
    inv_w = {v: k for k, v in CRIT_WEIGHT.items()}
    agg["Criticite_max"] = agg["Crit_max_w"].map(inv_w)

    ops = ops.merge(agg, on="Poste", how="left").merge(team, on="Poste", how="left")
    ops["Valeur_pieces"] = ops["Valeur_pieces"].fillna(0)
    ops["Criticite_max"] = ops["Criticite_max"].fillna("Aucune pièce")
    ops["Cout_MO_prevu"] = ops["Cout_horaire_equipe"] * ops["Prevu_min"] / 60
    ops["Cout_MO_reel"] = ops["Cout_horaire_equipe"] * ops["Reel_min"] / 60
    ops["Surcout_retard"] = ops["Cout_MO_reel"] - ops["Cout_MO_prevu"]
    # exposition : valeur immobilisée × heures de retard (€·h)
    ops["Exposition_eur_h"] = ops["Valeur_pieces"] * ops["Ecart_min"] / 60
    ops["Libelle"] = "P" + ops["Poste"].astype(str).str.zfill(2) + " · " + ops["Nom"].astype(str)

    # ---------- Pièces (PLM enrichi MES) ----------
    conso = long.groupby("Code").agg(
        Qte_consommee=("Poste", "size"),
        Nb_postes=("Poste", "nunique"),
        Etapes=("Nom", lambda s: ", ".join(sorted(set(s)))),
    ).reset_index()
    # retard moyen des opérations utilisant la pièce
    ecart_by_code = long.merge(ops[["Poste", "Ecart_pct"]], on="Poste").groupby("Code")["Ecart_pct"].mean()
    pieces = p.merge(conso, on="Code", how="left")
    pieces["Ecart_pct_moy"] = pieces["Code"].map(ecart_by_code)
    pieces[["Qte_consommee", "Nb_postes"]] = pieces[["Qte_consommee", "Nb_postes"]].fillna(0).astype(int)
    pieces["Valeur_consommee"] = pieces["Qte_consommee"] * pieces["Coût achat pièce (€)"]
    dmax = pieces["Delai_max_j"].max() or 1
    npmax = max(pieces["Nb_postes"].max(), 1)
    # Score de risque appro (0-100) : criticité × délai × dépendance (nb postes)
    pieces["Score_risque"] = (
        (pieces["Crit_w"] / 4) * (pieces["Delai_max_j"] / dmax) * (0.5 + 0.5 * pieces["Nb_postes"] / npmax) * 100
    ).round(1)

    return ops, pieces, staff


# ======================================================
# 2. OUTILS DE RENDU
# ======================================================

def _json(obj) -> str:
    def default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return None if np.isnan(o) else float(o)
        if isinstance(o, (pd.Timestamp, dt.datetime)):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(o, np.ndarray):
            return o.tolist()
        if o is pd.NA or o is pd.NaT:
            return None
        return str(o)

    def clean(o):
        if isinstance(o, (pd.Series, pd.Index, np.ndarray)):
            o = list(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (float, np.floating)):
            return None if np.isnan(o) else float(o)
        if o is pd.NA or o is pd.NaT:
            return None
        if isinstance(o, (pd.Timestamp, dt.datetime)):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        return o

    return json.dumps(clean(obj), default=default, ensure_ascii=False).replace("</", "<\\/")


def _layout(**kw) -> dict:
    base = {
        "paper_bgcolor": C["surface"],
        "plot_bgcolor": C["surface"],
        "font": {"family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif",
                 "size": 12, "color": C["text2"]},
        "margin": {"l": 60, "r": 24, "t": 16, "b": 48},
        "separators": ", ",
        "hoverlabel": {"bgcolor": "#ffffff", "bordercolor": C["border"], "font": {"color": C["text"]}},
        "xaxis": {"gridcolor": C["grid"], "zerolinecolor": C["border"], "linecolor": C["border"]},
        "yaxis": {"gridcolor": C["grid"], "zerolinecolor": C["border"], "linecolor": C["border"]},
        "legend": {"orientation": "h", "y": 1.08, "x": 0, "font": {"color": C["text2"]}},
        "showlegend": False,
    }
    for k, v in kw.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = {**base[k], **v}
        else:
            base[k] = v
    return base


def _fmt_eur(v: float) -> str:
    if v is None or pd.isna(v):
        return "–"
    return f"{v:,.0f} €".replace(",", " ")


def _fmt_eur_short(v: float) -> str:
    if v is None or pd.isna(v):
        return "–"
    if abs(v) >= 1e6:
        return f"{v / 1e6:.1f} M€".replace(".", ",")
    if abs(v) >= 1e4:
        return f"{v / 1e3:.0f} k€"
    return _fmt_eur(v)


def _fmt_min(m: float) -> str:
    if m is None or pd.isna(m):
        return "–"
    m = int(round(m))
    return f"{m // 60} h {m % 60:02d}" if m >= 60 else f"{m} min"


def _esc(s) -> str:
    return html.escape("" if s is None or (isinstance(s, float) and np.isnan(s)) else str(s))


def _kpis(items: list[tuple[str, str, str]]) -> str:
    """items = [(label, valeur, sous-texte)]"""
    cells = "".join(
        f'<div class="kpi"><div class="kpi-label">{_esc(l)}</div>'
        f'<div class="kpi-value">{_esc(v)}</div><div class="kpi-sub">{_esc(s)}</div></div>'
        for l, v, s in items
    )
    return f'<div class="kpis">{cells}</div>'


def _card(title: str, subtitle: str, div_id: str | None = None, inner: str = "", height: int = 420) -> str:
    chart = f'<div id="{div_id}" class="chart" style="height:{height}px"></div>' if div_id else ""
    sub = f'<p class="card-sub">{subtitle}</p>' if subtitle else ""
    return f'<section class="card"><h3>{_esc(title)}</h3>{sub}{chart}{inner}</section>'


def _insights(lines: list[str]) -> str:
    lis = "".join(f"<li>{l}</li>" for l in lines)
    return f'<section class="insights"><h3>Ce qu\'il faut retenir</h3><ul>{lis}</ul></section>'


def _table(df: pd.DataFrame, formats: dict | None = None, bar_col: str | None = None) -> str:
    formats = formats or {}
    head = "".join(f"<th>{_esc(c)}</th>" for c in df.columns)
    vmax = df[bar_col].max() if bar_col and len(df) else None
    rows = []
    for _, r in df.iterrows():
        tds = []
        for c in df.columns:
            v = r[c]
            txt = formats[c](v) if c in formats else _esc(v)
            if c == "Criticité" or c == "Criticité max":
                col = CRIT_COLOR.get(str(v))
                if col:
                    txt = f'<span class="badge"><i style="background:{col}"></i>{_esc(v)}</span>'
            if c == bar_col and vmax:
                w = max(2, 100 * float(v) / float(vmax)) if pd.notna(v) else 0
                txt = f'<div class="cellbar"><span style="width:{w:.0f}%"></span><em>{txt}</em></div>'
            num = isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool)
            tds.append(f'<td class="{"num" if num else ""}">{txt}</td>')
        rows.append("<tr>" + "".join(tds) + "</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


CSS = f"""
*{{box-sizing:border-box}}
body{{margin:0;padding:24px;background:#f4f3f0;color:{C['text']};
 font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;font-size:14px}}
header.page h2{{margin:0 0 4px;font-size:22px}}
header.page p{{margin:0 0 20px;color:{C['text2']};max-width:900px;line-height:1.5}}
.sources{{display:inline-flex;gap:6px;margin-bottom:16px;flex-wrap:wrap}}
.sources span{{font-size:11px;font-weight:600;padding:3px 8px;border-radius:999px;background:#fff;
 border:1px solid {C['border']};color:{C['text2']}}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:16px}}
.kpi{{background:{C['surface']};border:1px solid {C['border']};border-radius:10px;padding:14px 16px}}
.kpi-label{{font-size:12px;color:{C['text2']}}}
.kpi-value{{font-size:26px;font-weight:650;margin:4px 0;font-variant-numeric:tabular-nums}}
.kpi-sub{{font-size:12px;color:{C['muted']}}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:16px}}
.card{{background:{C['surface']};border:1px solid {C['border']};border-radius:10px;padding:16px;margin-bottom:16px;min-width:0}}
.card h3{{margin:0 0 4px;font-size:15px}}
.card-sub{{margin:0 0 8px;color:{C['text2']};font-size:12.5px;line-height:1.45}}
.insights{{background:#eef5fd;border:1px solid #cde2fb;border-radius:10px;padding:14px 18px;margin-bottom:16px}}
.insights h3{{margin:0 0 6px;font-size:14px;color:#184f95}}
.insights ul{{margin:0;padding-left:18px;line-height:1.6}}
.table-wrap{{overflow-x:auto;margin-top:8px}}
table{{border-collapse:collapse;width:100%;font-size:12.5px}}
th{{text-align:left;color:{C['text2']};font-weight:600;border-bottom:1px solid {C['border']};padding:8px;white-space:nowrap}}
td{{border-bottom:1px solid {C['grid']};padding:7px 8px;vertical-align:top}}
td.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
tr:hover td{{background:#f7f6f3}}
.badge{{display:inline-flex;align-items:center;gap:6px;white-space:nowrap}}
.badge i{{width:9px;height:9px;border-radius:50%;display:inline-block}}
.cellbar{{position:relative;min-width:110px}}
.cellbar span{{position:absolute;left:0;top:2px;bottom:2px;background:#cde2fb;border-radius:0 4px 4px 0}}
.cellbar em{{position:relative;font-style:normal;padding-left:4px}}
.note{{font-size:11.5px;color:{C['muted']};margin-top:6px}}
"""


def _page(title: str, intro: str, sources: list[str], body: str, figs: dict[str, dict]) -> str:
    calls = "\n".join(
        f"Plotly.newPlot('{fid}', {_json(f['data'])}, {_json(f['layout'])}, "
        f"{{responsive:true, displaylogo:false, modeBarButtonsToRemove:['lasso2d','select2d']}});"
        for fid, f in figs.items()
    )
    badges = "".join(f"<span>{_esc(s)}</span>" for s in sources)
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<script src="{PLOTLY_CDN}"></script>
<style>{CSS}</style></head>
<body>
<header class="page"><h2>{_esc(title)}</h2><div class="sources">{badges}</div><p>{intro}</p></header>
{body}
<script>
{calls}
</script>
</body></html>"""


def _bubble_sizes(values, max_px: float = 46):
    v = np.asarray(pd.Series(values).fillna(0).clip(lower=0), dtype=float)
    ref = 2.0 * (v.max() or 1) / (max_px ** 2)
    return v.tolist(), ref


# ======================================================
# 3. ANALYSES
# ======================================================

# ---------- 3.1 Synthèse 360° ----------
def html_analyse_synthese(ops: pd.DataFrame, pieces: pd.DataFrame, staff: pd.DataFrame) -> str:
    o = ops.sort_values("Debut").copy()
    tot_prev, tot_reel = o["Prevu_min"].sum(), o["Reel_min"].sum()
    depass = (tot_reel / tot_prev - 1) * 100
    surcout = o["Surcout_retard"].sum()
    valeur = o["Valeur_pieces"].sum()
    n_late = int((o["Ecart_min"] > 0).sum())
    ops_crit = int((o["Criticite_max"].isin(["Critique", "Haute"])).sum())

    kpis = _kpis([
        ("Temps réel vs prévu", _fmt_min(tot_reel), f"prévu {_fmt_min(tot_prev)} · +{depass:.0f} %"),
        ("Opérations en retard", f"{n_late}/{len(o)}", f"{n_late / len(o) * 100:.0f} % des opérations MES"),
        ("Surcoût main-d'œuvre", _fmt_eur(surcout), "ERP coût horaire × minutes de retard"),
        ("Valeur pièces engagées", _fmt_eur_short(valeur), "PLM coût achat × références MES"),
        ("Opérations à pièce critique", f"{ops_crit}", "criticité Haute ou Critique (PLM)"),
        ("Effectif mobilisé", f"{int(o['Nb_operateurs'].sum())}", f"{len(staff)} personnes dans l'ERP"),
    ])

    # Courbe en S cumulée prévu vs réel (même unité -> un seul axe)
    o["cum_prev"] = o["Prevu_min"].cumsum() / 60
    o["cum_reel"] = o["Reel_min"].cumsum() / 60
    x = list(range(1, len(o) + 1))
    hover = [f"{_esc(l)}<br>{d:%d/%m %H:%M}" for l, d in zip(o["Libelle"], o["Debut"])]
    fig_s = {
        "data": [
            {"type": "scatter", "mode": "lines", "name": "Cumul prévu", "x": x, "y": o["cum_prev"],
             "line": {"color": C["s1"], "width": 2}, "customdata": hover,
             "hovertemplate": "%{customdata}<br>Prévu cumulé : %{y:.1f} h<extra></extra>"},
            {"type": "scatter", "mode": "lines", "name": "Cumul réel", "x": x, "y": o["cum_reel"],
             "line": {"color": C["s2"], "width": 2}, "customdata": hover,
             "hovertemplate": "%{customdata}<br>Réel cumulé : %{y:.1f} h<extra></extra>"},
        ],
        "layout": _layout(showlegend=True, hovermode="x unified",
                          xaxis={"title": {"text": "Opérations dans l'ordre chronologique (MES)"}},
                          yaxis={"title": {"text": "Heures cumulées"}},
                          annotations=[{"x": x[-1], "y": o["cum_reel"].iloc[-1], "xanchor": "right", "yanchor": "bottom",
                                        "text": f"+{(o['cum_reel'].iloc[-1] - o['cum_prev'].iloc[-1]):.1f} h de dérive",
                                        "showarrow": False, "font": {"color": C["text"], "size": 12}}]),
    }

    # Par étape : minutes de retard (MES) + valeur pièces (PLM) + surcoût (ERP)
    st = o.groupby("Nom").agg(Retard=("Ecart_min", "sum"), Prevu=("Prevu_min", "sum"),
                              Valeur=("Valeur_pieces", "sum"), Surcout=("Surcout_retard", "sum"),
                              Ops=("Poste", "count")).reset_index()
    st["Retard_pct"] = st["Retard"] / st["Prevu"] * 100
    st = st.sort_values("Retard")
    fig_e = {
        "data": [{"type": "bar", "orientation": "h", "y": st["Nom"], "x": st["Retard"],
                  "marker": {"color": C["s1"], "line": {"color": C["surface"], "width": 1}},
                  "customdata": np.stack([st["Retard_pct"], st["Valeur"], st["Surcout"], st["Ops"]], axis=1),
                  "hovertemplate": "<b>%{y}</b><br>%{x:.0f} min de retard (+%{customdata[0]:.0f} %)"
                                   "<br>%{customdata[3]} opération(s)<br>Valeur pièces : %{customdata[1]:,.0f} €"
                                   "<br>Surcoût MO : %{customdata[2]:,.0f} €<extra></extra>"}],
        "layout": _layout(margin={"l": 280}, xaxis={"title": {"text": "Minutes de retard cumulées"}},
                          yaxis={"automargin": True}, bargap=0.25),
    }

    top = o.sort_values("Exposition_eur_h", ascending=False).head(8)
    t = pd.DataFrame({
        "Poste": top["Poste"], "Étape": top["Nom"], "Retard": top["Ecart_min"],
        "Valeur pièces": top["Valeur_pieces"], "Criticité max": top["Criticite_max"],
        "Équipe (ERP)": top["Niveaux"], "Exposition (€·h)": top["Exposition_eur_h"],
    })
    table = _table(t, {"Retard": _fmt_min, "Valeur pièces": _fmt_eur,
                       "Exposition (€·h)": lambda v: f"{v:,.0f}".replace(",", " ")}, bar_col="Exposition (€·h)")

    worst = st.sort_values("Retard", ascending=False).iloc[0]
    top_exp = top.iloc[0]
    ins = _insights([
        f"La ligne cumule <b>{_fmt_min(tot_reel - tot_prev)}</b> de dérive (+{depass:.0f} %) : "
        f"<b>{n_late} opérations sur {len(o)}</b> dépassent leur temps prévu — le retard est systémique, pas ponctuel.",
        f"L'étape <b>{_esc(worst['Nom'])}</b> concentre le plus de minutes perdues ({worst['Retard']:.0f} min).",
        f"Le surcoût direct de main-d'œuvre reste faible ({_fmt_eur(surcout)}), mais les retards immobilisent "
        f"des pièces de forte valeur : le poste <b>{int(top_exp['Poste'])}</b> ({_esc(top_exp['Nom'])}) bloque "
        f"{_fmt_eur(top_exp['Valeur_pieces'])} de pièces pendant {_fmt_min(top_exp['Ecart_min'])} de retard.",
    ])

    body = (kpis + ins + '<div class="grid">'
            + _card("Courbe en S : temps cumulé prévu vs réel",
                    "L'écart entre les deux courbes = dérive de planning accumulée sur la ligne.", "fig_s")
            + _card("Retard par étape d'assemblage", "Survolez une barre : valeur des pièces (PLM) et surcoût MO (ERP).",
                    "fig_e", height=max(420, 22 * len(st)))
            + "</div>"
            + _card("Top 8 des opérations à plus forte exposition",
                    "Exposition = valeur des pièces immobilisées (PLM) × heures de retard (MES). "
                    "C'est là qu'un retard coûte le plus en trésorerie bloquée.", inner=table))
    return _page("Synthèse 360° — MES × PLM × ERP",
                 "Vue d'ensemble qui relie l'exécution réelle (MES), la valeur et la criticité des pièces (PLM) "
                 "et les équipes et leurs coûts (ERP).",
                 ["MES", "PLM", "ERP"], body, {"fig_s": fig_s, "fig_e": fig_e})


# ---------- 3.2 Matrice de priorisation des postes ----------
def html_analyse_matrice(ops: pd.DataFrame, pieces: pd.DataFrame, staff: pd.DataFrame) -> str:
    o = ops.copy()
    o["Valeur_plot"] = o["Valeur_pieces"].clip(lower=10)
    sizes, ref = _bubble_sizes(o["Ecart_min"])
    xm, ym = float(o["Ecart_pct"].median()), float(o["Valeur_plot"].median())

    data = []
    for crit in CRIT_ORDER + ["Aucune pièce"]:
        sub = o[o["Criticite_max"] == crit]
        if sub.empty:
            continue
        s, _ = _bubble_sizes(sub["Ecart_min"])
        data.append({
            "type": "scatter", "mode": "markers", "name": f"Criticité {crit.lower()}" if crit != "Aucune pièce" else crit,
            "x": sub["Ecart_pct"], "y": sub["Valeur_plot"],
            "marker": {"size": s, "sizemode": "area", "sizeref": ref, "sizemin": 6,
                       "color": CRIT_COLOR.get(crit, C["muted"]), "opacity": 0.85,
                       "line": {"color": C["surface"], "width": 2}},
            "customdata": np.stack([sub["Libelle"], sub["Ecart_min"], sub["Valeur_pieces"],
                                    sub["Niveaux"].fillna("–"), sub["Aléas Industriels"].fillna("–"),
                                    sub["Surcout_retard"]], axis=1),
            "hovertemplate": "<b>%{customdata[0]}</b><br>Dépassement : +%{x:.0f} % (%{customdata[1]:.0f} min)"
                             "<br>Valeur pièces : %{customdata[2]:,.0f} €<br>Surcoût MO : %{customdata[5]:,.0f} €"
                             "<br>Équipe : %{customdata[3]}<br>Aléa : %{customdata[4]}<extra></extra>",
        })
    xmax = float(o["Ecart_pct"].max()) * 1.05
    fig = {
        "data": data,
        "layout": _layout(
            showlegend=True,
            xaxis={"title": {"text": "Dépassement du temps prévu (%) — MES"}, "range": [float(o["Ecart_pct"].min()) * 0.95, xmax]},
            yaxis={"title": {"text": "Valeur des pièces engagées (€, échelle log) — PLM"}, "type": "log"},
            shapes=[
                {"type": "line", "x0": xm, "x1": xm, "yref": "paper", "y0": 0, "y1": 1,
                 "line": {"color": C["muted"], "width": 1, "dash": "dot"}},
                {"type": "line", "xref": "paper", "x0": 0, "x1": 1, "y0": ym, "y1": ym,
                 "line": {"color": C["muted"], "width": 1, "dash": "dot"}},
            ],
            annotations=[
                {"xref": "paper", "yref": "paper", "x": 1, "y": 1, "xanchor": "right", "yanchor": "top",
                 "text": "<b>PRIORITÉ 1</b> · retard fort + forte valeur", "showarrow": False,
                 "font": {"color": "#d03b3b", "size": 11}},
                {"xref": "paper", "yref": "paper", "x": 0, "y": 1, "xanchor": "left", "yanchor": "top",
                 "text": "Valeur élevée, sous contrôle", "showarrow": False, "font": {"color": C["muted"], "size": 11}},
                {"xref": "paper", "yref": "paper", "x": 1, "y": 0, "xanchor": "right", "yanchor": "bottom",
                 "text": "Retard fort, faible enjeu pièces", "showarrow": False, "font": {"color": C["muted"], "size": 11}},
            ]),
    }

    # score de priorité : rang percentile du dépassement × rang percentile de la valeur
    o["Score"] = (o["Ecart_pct"].rank(pct=True) * 0.5 + o["Valeur_pieces"].rank(pct=True) * 0.3
                  + o["Criticite_max"].map(CRIT_WEIGHT).fillna(0) / 4 * 0.2) * 100
    q1 = o[(o["Ecart_pct"] >= xm) & (o["Valeur_plot"] >= ym)].sort_values("Score", ascending=False)
    top = o.sort_values("Score", ascending=False).head(10)
    t = pd.DataFrame({
        "Poste": top["Poste"], "Étape": top["Nom"], "Dépassement": top["Ecart_pct"],
        "Valeur pièces": top["Valeur_pieces"], "Criticité max": top["Criticite_max"],
        "Aléa (MES)": top["Aléas Industriels"], "Exp. équipe (1-3)": top["Exp_moyenne"],
        "Score priorité": top["Score"],
    })
    table = _table(t, {"Dépassement": lambda v: f"+{v:.0f} %", "Valeur pièces": _fmt_eur,
                       "Exp. équipe (1-3)": lambda v: f"{v:.1f}" if pd.notna(v) else "–",
                       "Score priorité": lambda v: f"{v:.0f}"}, bar_col="Score priorité")

    ins = _insights([
        f"<b>{len(q1)} postes</b> sont dans le quadrant « Priorité 1 » (dépassement ≥ {xm:.0f} % et valeur pièces ≥ "
        f"{_fmt_eur(ym)}) : {', '.join('P' + str(int(p)) for p in q1['Poste'].head(8))}.",
        "La taille des bulles = minutes de retard ; la couleur = la pièce la plus critique consommée (PLM).",
        "Score de priorité = 50 % rang du dépassement + 30 % rang de la valeur pièces + 20 % criticité.",
    ])
    body = (ins + _card("Matrice de priorisation des postes",
                        "Chaque bulle est une opération MES. Les lignes pointillées sont les médianes.", "fig_m", height=560)
            + _card("Top 10 des postes à traiter en premier", "", inner=table))
    return _page("Matrice risque × valeur des postes", "Croise le retard d'exécution (MES) avec la valeur et la criticité "
                 "des pièces consommées (PLM) et le profil de l'équipe (ERP) pour savoir <b>où agir d'abord</b>.",
                 ["MES", "PLM", "ERP"], body, {"fig_m": fig})


# ---------- 3.3 Pareto des aléas & causes racines ----------
def html_analyse_pareto(ops: pd.DataFrame, pieces: pd.DataFrame, staff: pd.DataFrame) -> str:
    o = ops.copy()
    fam = o.groupby("Famille_alea").agg(Minutes=("Ecart_min", "sum"), Nb=("Poste", "count"),
                                        Surcout=("Surcout_retard", "sum"),
                                        Valeur=("Valeur_pieces", "sum")).reset_index()
    fam = fam.sort_values("Minutes", ascending=False).reset_index(drop=True)
    fam["Cum_pct"] = fam["Minutes"].cumsum() / fam["Minutes"].sum() * 100
    # "vital few" : familles nécessaires pour atteindre 80 %
    n_vital = int((fam["Cum_pct"] < 80).sum()) + 1
    fam["Vital"] = fam.index < n_vital
    colors = [C["seq_dark"] if v else C["seq_light"] for v in fam["Vital"]]
    fig_p = {
        "data": [{"type": "bar", "x": fam["Famille_alea"], "y": fam["Minutes"],
                  "marker": {"color": colors, "line": {"color": C["surface"], "width": 2}},
                  "text": [f"{c:.0f} % cumulé" for c in fam["Cum_pct"]], "textposition": "outside",
                  "textfont": {"color": C["text2"], "size": 11}, "cliponaxis": False,
                  "customdata": np.stack([fam["Nb"], fam["Surcout"], fam["Valeur"]], axis=1),
                  "hovertemplate": "<b>%{x}</b><br>%{y:.0f} min perdues · %{customdata[0]} opérations"
                                   "<br>Surcoût MO : %{customdata[1]:,.0f} €<br>Pièces impactées : "
                                   "%{customdata[2]:,.0f} €<extra></extra>"}],
        "layout": _layout(margin={"b": 120, "t": 30}, yaxis={"title": {"text": "Minutes perdues (MES)"}},
                          xaxis={"tickangle": -20, "automargin": True}, bargap=0.3),
    }

    # Heatmap famille d'aléa × étape (minutes)
    pv = o.pivot_table(index="Famille_alea", columns="Nom", values="Ecart_min", aggfunc="sum", fill_value=0)
    pv = pv.loc[fam["Famille_alea"]]
    fig_h = {
        "data": [{"type": "heatmap", "z": pv.values.round(1), "x": list(pv.columns), "y": list(pv.index),
                  "colorscale": [[i / (len(C["seq"]) - 1), c] for i, c in enumerate(C["seq"])],
                  "xgap": 2, "ygap": 2, "colorbar": {"title": {"text": "min"}, "thickness": 10},
                  "hovertemplate": "<b>%{y}</b><br>%{x}<br>%{z:.0f} min perdues<extra></extra>"}],
        "layout": _layout(margin={"l": 250, "b": 170, "t": 10}, xaxis={"tickangle": -40, "gridcolor": "rgba(0,0,0,0)"},
                          yaxis={"autorange": "reversed", "gridcolor": "rgba(0,0,0,0)"}),
    }

    # Thèmes de causes racines (texte libre "Cause Potentielle")
    rows = []
    for _, r in o.iterrows():
        for th in _themes(r["Cause Potentielle"]):
            rows.append({"Theme": th, "Minutes": r["Ecart_min"], "Poste": r["Poste"]})
    th = pd.DataFrame(rows).groupby("Theme").agg(Minutes=("Minutes", "sum"), Nb=("Poste", "count")).reset_index()
    th = th.sort_values("Minutes")
    fig_c = {
        "data": [{"type": "bar", "orientation": "h", "y": th["Theme"], "x": th["Nb"],
                  "marker": {"color": C["s1"], "line": {"color": C["surface"], "width": 2}},
                  "customdata": th["Minutes"],
                  "hovertemplate": "<b>%{y}</b><br>Citée dans %{x} opérations<br>%{customdata:.0f} min de retard associées<extra></extra>"}],
        "layout": _layout(margin={"l": 240}, xaxis={"title": {"text": "Nombre d'opérations où la cause est citée"}},
                          yaxis={"automargin": True}, bargap=0.3),
    }

    vital = fam[fam["Vital"]]
    top_theme = th.sort_values("Nb", ascending=False).iloc[0]
    ins = _insights([
        f"<b>{len(vital)} familles d'aléas sur {len(fam)}</b> expliquent ~80 % des minutes perdues : "
        + ", ".join(f"<b>{_esc(f)}</b>" for f in vital["Famille_alea"]) + ".",
        f"Cause racine la plus citée : <b>{_esc(top_theme['Theme'])}</b> ({int(top_theme['Nb'])} opérations). "
        "Un plan de maintenance préventive / modernisation ciblé aurait l'effet le plus large.",
        "La heatmap montre si une famille d'aléa est localisée sur une étape (action locale) ou diffuse (action transverse).",
    ])
    body = (ins + _card("Pareto des familles d'aléas (minutes perdues)",
                        "Barres foncées = les familles qui font 80 % du retard (« vital few »). "
                        "Les aléas texte libre du MES sont regroupés par mots-clés.", "fig_p", height=440)
            + '<div class="grid">'
            + _card("Où se produisent les aléas ? (famille × étape)", "Minutes perdues par famille et étape.", "fig_h", height=480)
            + _card("Causes racines récurrentes", "Thèmes extraits de la colonne « Cause Potentielle ».", "fig_c", height=480)
            + "</div>")
    return _page("Pareto des aléas & causes racines", "Identifie les quelques familles d'incidents qui génèrent "
                 "l'essentiel du retard (loi 80/20), puis leurs causes racines, avec l'impact en € (ERP) et "
                 "en valeur de pièces (PLM).", ["MES", "PLM", "ERP"], body,
                 {"fig_p": fig_p, "fig_h": fig_h, "fig_c": fig_c})


# ---------- 3.4 Expérience des équipes vs performance ----------
def html_analyse_experience(ops: pd.DataFrame, pieces: pd.DataFrame, staff: pd.DataFrame) -> str:
    o = ops.dropna(subset=["Exp_moyenne", "Ecart_pct"]).copy()
    x, y = o["Exp_moyenne"].astype(float).values, o["Ecart_pct"].astype(float).values
    r = float(np.corrcoef(x, y)[0, 1]) if len(o) > 2 else float("nan")
    a, b = np.polyfit(x, y, 1) if len(o) > 2 else (0, 0)
    xs = [float(x.min()), float(x.max())]
    jitter = np.random.default_rng(7).uniform(-0.03, 0.03, len(o))

    fig_s = {
        "data": [
            {"type": "scatter", "mode": "markers", "name": "Opérations", "x": x + jitter, "y": y,
             "marker": {"size": 10, "color": C["s1"], "opacity": 0.8, "line": {"color": C["surface"], "width": 2}},
             "customdata": np.stack([o["Libelle"], o["Niveaux"], o["Cout_horaire_equipe"], x], axis=1),
             "hovertemplate": "<b>%{customdata[0]}</b><br>Dépassement : +%{y:.0f} %<br>Équipe : %{customdata[1]}"
                              "<br>Score moyen : %{customdata[3]:.2f}<br>Coût équipe : %{customdata[2]:.2f} €/h<extra></extra>"},
            {"type": "scatter", "mode": "lines", "name": "Tendance", "x": xs, "y": [a * v + b for v in xs],
             "line": {"color": C["s2"], "width": 2, "dash": "dash"}, "hoverinfo": "skip"},
        ],
        "layout": _layout(showlegend=True,
                          xaxis={"title": {"text": "Score d'expérience moyen de l'équipe (1 = Débutant · 3 = Expert) — ERP"}},
                          yaxis={"title": {"text": "Dépassement du temps prévu (%) — MES"}},
                          annotations=[{"xref": "paper", "yref": "paper", "x": 1, "y": 1, "xanchor": "right",
                                        "showarrow": False, "text": f"r de Pearson = {r:.2f}",
                                        "font": {"color": C["text"], "size": 12}}]),
    }

    # Comparaison par composition d'équipe
    def profil(row):
        if row["Nb_debutants"] > 0:
            return "Avec ≥1 débutant"
        if row["Nb_experts"] >= row["Nb_operateurs"] / 2:
            return "Majorité d'experts"
        return "Confirmés / mixte"
    o["Profil"] = o.apply(profil, axis=1)
    order = ["Avec ≥1 débutant", "Confirmés / mixte", "Majorité d'experts"]
    colors = [C["s1"], C["s2"], C["s3"]]
    data_b = []
    for pname, col in zip(order, colors):
        sub = o[o["Profil"] == pname]
        if sub.empty:
            continue
        data_b.append({"type": "box", "name": f"{pname} (n={len(sub)})", "y": sub["Ecart_pct"], "boxpoints": "all",
                       "jitter": 0.4, "pointpos": 0, "marker": {"color": col, "size": 7},
                       "line": {"color": col, "width": 2}, "fillcolor": "rgba(0,0,0,0)",
                       "customdata": sub["Libelle"],
                       "hovertemplate": "%{customdata}<br>+%{y:.0f} %<extra></extra>"})
    fig_b = {"data": data_b, "layout": _layout(yaxis={"title": {"text": "Dépassement (%)"}})}

    # Coût horaire vs niveau (ERP) + productivité
    lvl = staff.groupby("Niveau d'expérience").agg(Cout=("Coût horaire (€)", "mean"), N=("Matricule", "count"),
                                                   Age=("Âge", "mean")).reindex(["Débutant", "Confirmé", "Expert"])
    fig_l = {
        "data": [{"type": "bar", "x": list(lvl.index), "y": lvl["Cout"].round(2),
                  "marker": {"color": C["s1"], "line": {"color": C["surface"], "width": 2}},
                  "text": [f"{v:.2f} €/h" for v in lvl["Cout"]], "textposition": "outside", "cliponaxis": False,
                  "textfont": {"color": C["text2"]},
                  "customdata": np.stack([lvl["N"], lvl["Age"]], axis=1),
                  "hovertemplate": "<b>%{x}</b><br>%{y:.2f} €/h en moyenne<br>%{customdata[0]} personnes · "
                                   "%{customdata[1]:.0f} ans en moyenne<extra></extra>"}],
        "layout": _layout(margin={"t": 30}, yaxis={"title": {"text": "Coût horaire moyen (€)"},
                                                   "range": [0, float(lvl["Cout"].max()) * 1.2]}, bargap=0.45),
    }

    med = o.groupby("Profil")["Ecart_pct"].median()
    force = "faible" if abs(r) < 0.3 else ("modérée" if abs(r) < 0.6 else "forte")
    sens = "baisse" if r < 0 else "hausse"
    if force == "faible":
        first = (f"<b>Pas de lien net</b> entre expérience et retard (r = {r:.2f}, pente {a:+.1f} pts de % par niveau) : "
                 "l'expérience de l'équipe titulaire n'explique pas les dépassements — le retard vient surtout des aléas "
                 "(voir le Pareto).")
    else:
        first = (f"Corrélation <b>{force}</b> (r = {r:.2f}) : quand l'expérience moyenne augmente, le dépassement a "
                 f"tendance à être en {sens} ({a:+.1f} points de % par niveau d'expérience).")
    lines = [first]
    if len(med) > 1:
        lines.append("Dépassement médian par profil : " + " · ".join(f"{_esc(k)} <b>+{v:.0f} %</b>" for k, v in med.items()) + ".")
    lines.append("Avec 56 opérations, l'expérience n'explique qu'une partie du retard : croisez avec le Pareto des aléas "
                 "(équipements, environnement) avant de décider d'une réaffectation des équipes.")
    lines.append("Équipe titulaire = colonne « Poste de montage » de l'ERP (les rotations hebdomadaires sont ignorées ici).")
    body = (_insights(lines)
            + _card("Expérience de l'équipe vs dépassement", "Chaque point = une opération MES ; l'équipe vient de l'ERP.", "fig_s", height=460)
            + '<div class="grid">'
            + _card("Dépassement selon la composition de l'équipe", "Boîtes = médiane et quartiles ; points = opérations.", "fig_b", height=420)
            + _card("Coût horaire moyen par niveau (ERP)", "À comparer au gain de performance pour arbitrer le staffing.", "fig_l", height=420)
            + "</div>")
    return _page("Expérience des équipes vs performance", "Les équipes plus expérimentées tiennent-elles mieux les "
                 "temps ? Croise le profil des opérateurs (ERP) avec les écarts mesurés (MES).", ["MES", "ERP"], body,
                 {"fig_s": fig_s, "fig_b": fig_b, "fig_l": fig_l})


# ---------- 3.5 Risque approvisionnement ----------
def html_analyse_supply(ops: pd.DataFrame, pieces: pd.DataFrame, staff: pd.DataFrame) -> str:
    p = pieces[pieces["Qte_consommee"] > 0].copy()
    sizes, ref = _bubble_sizes(p["Qte_consommee"], 40)
    data = []
    for crit in CRIT_ORDER:
        sub = p[p["Criticité"] == crit]
        if sub.empty:
            continue
        s, _ = _bubble_sizes(sub["Qte_consommee"], 40)
        data.append({
            "type": "scatter", "mode": "markers+text", "name": f"Criticité {crit.lower()}",
            "x": sub["Delai_max_j"], "y": sub["Coût achat pièce (€)"],
            "text": [c if (cw >= 3) else "" for c, cw in zip(sub["Code"], sub["Crit_w"])],
            "textposition": "top center", "textfont": {"size": 10, "color": C["text2"]},
            "marker": {"size": s, "sizemode": "area", "sizeref": ref, "sizemin": 6,
                       "color": CRIT_COLOR[crit], "opacity": 0.85, "line": {"color": C["surface"], "width": 2}},
            "customdata": np.stack([sub["Code"], sub["Désignation"], sub["Fournisseur"], sub["Qte_consommee"],
                                    sub["Nb_postes"], sub["Délai Approvisionnement"]], axis=1),
            "hovertemplate": "<b>%{customdata[0]} · %{customdata[1]}</b><br>Fournisseur : %{customdata[2]}"
                             "<br>Délai : %{customdata[5]}<br>Coût unitaire : %{y:,.0f} €"
                             "<br>Consommée %{customdata[3]}× sur %{customdata[4]} poste(s)<extra></extra>",
        })
    fig_r = {"data": data, "layout": _layout(
        showlegend=True, xaxis={"title": {"text": "Délai d'approvisionnement max (jours) — PLM"}},
        yaxis={"title": {"text": "Coût unitaire (€, échelle log) — PLM"}, "type": "log"})}

    # Exposition par fournisseur (valeur consommée en MES)
    f = p.groupby("Fournisseur").agg(Valeur=("Valeur_consommee", "sum"), Delai=("Delai_max_j", "max"),
                                      Refs=("Code", "nunique"), Postes=("Nb_postes", "sum")).reset_index()
    f = f.sort_values("Valeur")
    total = f["Valeur"].sum()
    fig_f = {
        "data": [{"type": "bar", "orientation": "h", "y": f["Fournisseur"], "x": f["Valeur"],
                  "marker": {"color": C["s1"], "line": {"color": C["surface"], "width": 2}},
                  "text": [f"{v / total * 100:.0f} %" for v in f["Valeur"]], "textposition": "outside",
                  "cliponaxis": False, "textfont": {"color": C["text2"], "size": 11},
                  "customdata": np.stack([f["Delai"], f["Refs"], f["Postes"]], axis=1),
                  "hovertemplate": "<b>%{y}</b><br>%{x:,.0f} € consommés<br>Délai max : %{customdata[0]:.0f} j"
                                   "<br>%{customdata[1]} réf. · %{customdata[2]} postes dépendants<extra></extra>"}],
        "layout": _layout(margin={"l": 200, "r": 50}, xaxis={"title": {"text": "Valeur consommée sur la ligne (€) — PLM × MES"},
                                                            "type": "log"}, yaxis={"automargin": True}, bargap=0.3),
    }

    top = p.sort_values("Score_risque", ascending=False).head(10)
    t = pd.DataFrame({
        "Réf.": top["Code"], "Désignation": top["Désignation"], "Fournisseur": top["Fournisseur"],
        "Criticité": top["Criticité"], "Délai max (j)": top["Delai_max_j"], "Postes dépendants": top["Nb_postes"],
        "Retard moyen des postes": top["Ecart_pct_moy"], "Score risque": top["Score_risque"],
    })
    table = _table(t, {"Délai max (j)": lambda v: f"{v:.0f}",
                       "Retard moyen des postes": lambda v: f"+{v:.0f} %" if pd.notna(v) else "–",
                       "Score risque": lambda v: f"{v:.0f}"}, bar_col="Score risque")

    big = f.sort_values("Valeur", ascending=False).iloc[0]
    crit_long = p[(p["Crit_w"] >= 3) & (p["Delai_max_j"] >= 25)]
    ins = _insights([
        f"<b>{_esc(big['Fournisseur'])}</b> représente {big['Valeur'] / total * 100:.0f} % de la valeur consommée "
        f"avec un délai jusqu'à {big['Delai']:.0f} jours : forte concentration du risque sur un seul fournisseur.",
        f"<b>{len(crit_long)} références</b> cumulent criticité Haute/Critique et délai ≥ 25 jours : "
        + ", ".join(f"{_esc(c)}" for c in crit_long["Code"]) + " → stock de sécurité ou double sourcing recommandé.",
        "Score risque = criticité × délai relatif × nombre de postes qui dépendent de la pièce (0-100).",
    ])
    body = (ins + _card("Matrice de risque des pièces", "Taille = quantité consommée dans le MES ; couleur = criticité PLM. "
                        "En haut à droite : pièces chères, longues à approvisionner.", "fig_r", height=520)
            + _card("Top 10 des pièces à sécuriser", "", inner=table)
            + _card("Exposition par fournisseur", "Part de la valeur des pièces consommées (échelle log).", "fig_f",
                    height=max(420, 26 * len(f))))
    return _page("Risque approvisionnement & fournisseurs", "Relie les attributs pièces (criticité, délai, coût, fournisseur — PLM) "
                 "à leur usage réel sur la ligne (MES) pour cibler les pièces qui peuvent arrêter la production.",
                 ["PLM", "MES"], body, {"fig_r": fig_r, "fig_f": fig_f})


# ---------- 3.6 Chronologie (Gantt) ----------
def html_analyse_chronologie(ops: pd.DataFrame, pieces: pd.DataFrame, staff: pd.DataFrame) -> str:
    o = ops.dropna(subset=["Debut"]).sort_values("Debut").copy()
    o["Prevu_fin"] = o["Debut"] + pd.to_timedelta(o["Prevu_min"], unit="m")
    labels = o["Libelle"].tolist()
    dur_prev = (o["Prevu_min"] * 60000).tolist()
    dur_reel = (o["Reel_min"] * 60000).tolist()
    starts = [d.strftime("%Y-%m-%d %H:%M:%S") for d in o["Debut"]]
    cd = np.stack([o["Prevu_min"], o["Reel_min"], o["Ecart_pct"], o["Criticite_max"], o["Niveaux"].fillna("–"),
                   o["Aléas Industriels"].fillna("–"), o["Pieces"].fillna("–")], axis=1)
    hover = ("<b>%{y}</b><br>Prévu %{customdata[0]:.0f} min · Réel %{customdata[1]:.0f} min (+%{customdata[2]:.0f} %)"
             "<br>Criticité max : %{customdata[3]}<br>Pièces : %{customdata[6]}<br>Équipe : %{customdata[4]}"
             "<br>Aléa : %{customdata[5]}<extra></extra>")
    fig = {
        "data": [
            {"type": "bar", "orientation": "h", "name": "Durée prévue", "y": labels, "x": dur_prev, "base": starts,
             "marker": {"color": C["seq"][0], "line": {"color": C["seq"][2], "width": 1}}, "width": 0.8,
             "customdata": cd, "hovertemplate": hover},
            {"type": "bar", "orientation": "h", "name": "Durée réelle", "y": labels, "x": dur_reel, "base": starts,
             "marker": {"color": [CRIT_COLOR.get(c, C["muted"]) for c in o["Criticite_max"]]}, "width": 0.38,
             "customdata": cd, "hovertemplate": hover},
        ],
        "layout": _layout(showlegend=False, barmode="overlay", margin={"l": 330, "t": 10},
                          xaxis={"type": "date", "tickformat": "%d/%m %Hh", "side": "top"},
                          yaxis={"autorange": "reversed", "automargin": True, "tickfont": {"size": 10.5}}),
    }
    legend = ('<p class="note">Barre claire = durée prévue (MES) · barre fine = durée réelle, colorée par la criticité '
              'max des pièces (PLM) : ' + " ".join(
                  f'<span class="badge"><i style="background:{CRIT_COLOR[c]}"></i>{c}</span>' for c in CRIT_ORDER)
              + '. Survolez pour voir l\'équipe (ERP) et l\'aléa.</p>')

    by_day = o.groupby(o["Debut"].dt.date).agg(Ops=("Poste", "count"), Prevu=("Prevu_min", "sum"),
                                                Reel=("Reel_min", "sum")).reset_index()
    ins = _insights([
        "Jour le plus chargé : <b>" + by_day.sort_values("Reel", ascending=False).iloc[0]["Debut"].strftime("%d/%m")
        + "</b>. " + " · ".join(f"{r['Debut']:%d/%m} : {r['Ops']} ops, +{(r['Reel'] / r['Prevu'] - 1) * 100:.0f} %"
                                for _, r in by_day.iterrows()),
        "Les opérations s'enchaînent en série : chaque minute de retard décale toutes les suivantes "
        "(voir la courbe en S de la synthèse).",
    ])
    body = ins + _card("Chronologie des opérations (Gantt prévu vs réel)", "", "fig_g", height=max(600, 19 * len(o) + 60),
                       inner=legend)
    return _page("Chronologie de production", "Diagramme de Gantt reliant l'exécution (MES), la criticité des pièces "
                 "(PLM) et les équipes (ERP), opération par opération.", ["MES", "PLM", "ERP"], body, {"fig_g": fig})


# ======================================================
# 4. POINT D'ENTRÉE UNIQUE
# ======================================================

ANALYSES = {
    "synthese": html_analyse_synthese,
    "matrice": html_analyse_matrice,
    "pareto": html_analyse_pareto,
    "experience": html_analyse_experience,
    "supply": html_analyse_supply,
    "chronologie": html_analyse_chronologie,
}


def render_analyse(name: str, folder: str = "uploads") -> str:
    if name not in ANALYSES:
        raise KeyError(f"Analyse inconnue : {name}. Disponibles : {', '.join(ANALYSES)}")
    mes, plm, erp = load_sources(folder)
    ops, pieces, staff = build_model(mes, plm, erp)
    return ANALYSES[name](ops, pieces, staff)


if __name__ == "__main__":  # génération hors-ligne : python analytics.py
    out = "analyses_html"
    os.makedirs(out, exist_ok=True)
    for k in ANALYSES:
        with open(os.path.join(out, f"{k}.html"), "w", encoding="utf-8") as fh:
            fh.write(render_analyse(k))
        print("OK", k)
