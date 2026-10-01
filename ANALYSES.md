# Analyses croisées MES × PLM × ERP

Module : `backend/analytics.py`, route `GET /api/analyse/<nom>`, bouton **🔗 Analyses croisées** dans le frontend.

## 1. Comment les 3 fichiers sont reliés

| Clé | MES_Extraction | PLM_DataSet | ERP_Equipes_Airplus |
|---|---|---|---|
| Pièce | `Référence` (liste `A511;A337;…`, éclatée en 1 ligne par pièce) | `Code / Référence` | – |
| Poste | `Poste` (1 à 56) | – | `Poste de montage` (« Poste N » = équipe titulaire, 2 à 3 personnes) |
| Temps | `Date`, `Heure Début`, `Temps Prévu`, `Temps Réel` | `Délai Approvisionnement`, `Temps CAO` | `Coût horaire (€)` |

Indicateurs calculés pour chaque opération MES :

- **Dépassement** (min et %) = Temps Réel − Temps Prévu
- **Valeur des pièces engagées** (€) = somme des coûts d'achat PLM des pièces consommées
- **Criticité max et délai d'appro max** = la pire pièce consommée par l'opération
- **Coût de main-d'œuvre réel et surcoût** (€) = coût horaire cumulé de l'équipe ERP × durée
- **Score d'expérience de l'équipe** : Débutant = 1, Confirmé = 2, Expert = 3
- **Exposition** (€·h) = valeur des pièces immobilisées × heures de retard
- **Famille d'aléa** et **thèmes de causes racines**, obtenus par mots-clés sur le texte libre du MES

## 2. Stratégies d'analyse retenues

| # | Analyse (`/api/analyse/…`) | Question métier | Méthode |
|---|---|---|---|
| 1 | `synthese` | Où en est la ligne ? | KPI, **courbe en S** prévu/réel cumulé, retard par étape, top des opérations par exposition € |
| 2 | `matrice` | Quels postes traiter en premier ? | **Matrice de priorisation** dépassement × valeur des pièces (axe log), bulles = minutes perdues, couleur = criticité, quadrants sur les médianes, score de priorité |
| 3 | `pareto` | Quels incidents coûtent le plus ? | **Pareto 80/20** des familles d'aléas, heatmap famille × étape, fréquence des causes racines |
| 4 | `experience` | L'expérience des équipes joue-t-elle ? | Nuage de points + **régression linéaire et r de Pearson**, boîtes par composition d'équipe, coût horaire par niveau |
| 5 | `supply` | Quelles pièces peuvent arrêter la ligne ? | **Matrice de risque pièces** délai × coût × consommation, exposition par fournisseur, score de risque (criticité × délai × dépendance) |
| 6 | `chronologie` | Comment le retard se propage-t-il ? | **Gantt** prévu vs réel coloré par criticité, avec l'équipe et l'aléa au survol |

## 3. Premiers enseignements sur le jeu de données

- Les 56 opérations dépassent toutes leur temps prévu : +41 % au total, soit environ 9 h de dérive. Le retard est systémique.
- 4 familles d'aléas sur 7 font environ 80 % des minutes perdues : environnement atelier, SI/automatismes, qualité/métrologie et outillage. La cause racine la plus citée est la vétusté/obsolescence.
- Aucun lien net entre l'expérience des équipes titulaires et le retard (r ≈ 0,04). Il faut agir sur les équipements avant de réaffecter les équipes.
- Le surcoût direct de main-d'œuvre est faible (moins de 1 000 €). En revanche, les retards immobilisent des pièces de forte valeur : le poste 27 (réacteurs) bloque environ 10 M€ de pièces.
- 6 références critiques ont un délai ≥ 25 jours (D142, D088, D234, A437, A423, A623). Elles sont candidates à un stock de sécurité ou à un double sourcing. Safran Engines porte à lui seul environ 47 % de la valeur consommée.

## 4. Générer les rapports sans lancer le frontend

```bash
cd backend
python analytics.py   # écrit backend/analyses_html/*.html
```

## 5. Pistes d'évolution

- Utiliser la colonne `Rotation` de l'ERP (semaine × poste) pour savoir qui a réellement travaillé chaque jour, au lieu de l'équipe titulaire.
- Remplacer la catégorisation par mots-clés par une classification par LLM. Gemini est déjà branché pour le chatbot.
- Ajouter un coût de portage du stock (taux annuel) pour convertir l'exposition €·h en coût financier.
- Ajouter une analyse de goulots avec un temps de cycle par étape et un calcul du chemin critique.
