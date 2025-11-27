import os
import io
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from scripts import *
import pandas as pd
import google.generativeai as genai
import dotenv

dotenv.load_dotenv(override=True)

# On définit le dossier statique sur 'dist' (le build de Vite)
app = Flask(__name__, static_folder='dist', static_url_path='')

# IMPORTANT : Active CORS pour permettre à React (port différent) de communiquer
CORS(app)

# Configuration du dossier d'upload
UPLOAD_FOLDER = 'uploads'
# Création automatique du dossier s'il n'existe pas
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Extensions autorisées
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'webp', 'xls', 'xlsx'}

# Configuration de Gemini (Remplacez par votre clé API)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
print("Gemini API Key loaded." if GEMINI_API_KEY else "Gemini API Key not found.")

# Dictionnaire pour stocker les DataFrames chargés en mémoire (cache)
loaded_dataframes = {}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROUTE 1 : Servir l'application React ---
# Cette route ne sert que si Flask sert le frontend (après npm run build)
@app.route('/')
def serve():
    if os.path.exists(app.static_folder):
        return send_from_directory(app.static_folder, 'index.html')
    else:
        return "Le dossier 'dist' n'existe pas. Veuillez exécuter 'npm run build' dans votre projet React.", 404

@app.route('/button/poste_pieces', methods=['GET'])
def poste_pieces():
    return None

# --- ROUTE 2 : API pour lister les fichiers (GET /api/files) ---
@app.route('/api/files', methods=['GET'])
def list_files():
    files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            if os.path.isfile(file_path) and not filename.startswith('.'):
                file_type = 'image/jpeg' if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) else 'application/octet-stream'
                
                files.append({
                    'id': filename,
                    'name': filename,
                    'type': file_type,
                    'size': f"{os.path.getsize(file_path) / 1024:.2f} KB",
                    # Chemin relatif que le frontend utilise pour construire l'URL absolue
                    'url': f'/uploads/{filename}' 
                })
    return jsonify(files)

# --- ROUTE 3 : API pour uploader un fichier (POST /api/upload) ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        # Retourne un message d'erreur clair si Flask ne reçoit pas de fichier
        return jsonify({'error': 'Aucun fichier dans la requête (clé "file" manquante)'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        
        # --- CORRECTION APPORTÉE ICI ---
        # Le statut 201 est explicitement renvoyé en plus du JSON
        return jsonify({
            'message': 'Fichier uploadé avec succès', 
            'filename': filename,
            'url': f'/uploads/{filename}'
        }), 201
    
    return jsonify({'error': 'Type de fichier non autorisé'}), 400

# --- ROUTE 4 : Servir les fichiers uploadés (GET /uploads/<filename>) ---
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # Sert le fichier depuis le dossier 'uploads'
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- ROUTE 5 : API Chatbot pour interroger les fichiers Excel (POST /api/chat) ---
@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Endpoint du chatbot qui :
    1. Reçoit une question utilisateur
    2. Charge les fichiers Excel disponibles dans 'uploads/'
    3. Construit un prompt avec la structure des données + question
    4. Envoie le prompt à Gemini
    5. Récupère le code Pandas généré
    6. Exécute le code sur les DataFrames
    7. Retourne le résultat au frontend
    """
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        
        if not user_question:
            return jsonify({'error': 'Aucune question fournie'}), 400
        
        # 1. Charger tous les fichiers Excel disponibles
        excel_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                      if f.endswith(('.xlsx', '.xls'))]
        
        if not excel_files:
            return jsonify({
                'answer': "Aucun fichier Excel n'est disponible. Veuillez d'abord importer des fichiers .xlsx",
                'error': True
            }), 200
        
        # 2. Charger les DataFrames (avec cache pour optimiser)
        dataframes_info = []
        for filename in excel_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Utiliser le cache si déjà chargé
            if filename not in loaded_dataframes:
                try:
                    loaded_dataframes[filename] = pd.read_excel(file_path)
                except Exception as e:
                    continue  # Ignorer les fichiers corrompus
            
            df = loaded_dataframes[filename]
            
            # Collecter les informations sur la structure du DataFrame
            df_info = {
                'filename': filename,
                'columns': list(df.columns),
                'shape': df.shape,
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'sample': df.head(3).to_dict('records')
            }
            dataframes_info.append(df_info)
        
        # 3. Construire le prompt pour Gemini
        prompt = f"""Tu es un assistant intelligent qui aide les utilisateurs à analyser leurs fichiers Excel.

DONNÉES DISPONIBLES :
{format_dataframes_description(dataframes_info)}

QUESTION DE L'UTILISATEUR :
{user_question}

TON RÔLE :
1. Analyser la question et les données disponibles
2. Générer du code Python/Pandas pour extraire l'information demandée
3. Formatter le résultat de manière CLAIRE, CONCISE et LISIBLE pour un humain NON-TECHNIQUE

RÈGLES CRITIQUES DE FORMATAGE :
- Réponds en FRANÇAIS naturel et conversationnel
- Convertis TOUS les timedelta en format lisible : "2h 7min" au lieu de "0 days 02:07:45"
- Arrondis les nombres décimaux à 2 chiffres maximum
- Utilise des puces (•) ou numérotation (1., 2., 3.)
- Limite à 5-10 résultats maximum (sauf si demandé autrement)
- Structure : Titre ➜ Liste concise ➜ Insight si pertinent

INSTRUCTIONS TECHNIQUES :
- DataFrames dans 'dataframes' dictionnaire (clé = nom fichier)
- Résultat final dans variable 'result' (string formatée)
- Importe ce dont tu as besoin (datetime, timedelta, etc.)

EXEMPLES DE BON FORMATAGE :

Exemple 1 - Conversion de timedelta :
```python
df = dataframes['fichier.xlsx']
top_items = df.nlargest(5, 'temps_reel')

result = "🏆 Top 5 des assemblages les plus longs :\\n\\n"
for i, (idx, row) in enumerate(top_items.iterrows(), 1):
    # Convertir timedelta en format lisible
    td = row['temps_reel']
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    
    result += f"{{i}}. {{row['nom_poste']}}\\n"
    result += f"   ⏱️  Temps réel : {{hours}}h {{minutes}}min\\n"
    if 'temps_prevu' in row:
        td_prevu = row['temps_prevu']
        h_prevu = td_prevu.seconds // 3600
        m_prevu = (td_prevu.seconds % 3600) // 60
        result += f"   📋 Temps prévu : {{h_prevu}}h {{m_prevu}}min\\n"
    result += "\\n"
```

Exemple 2 - Réponse simple et claire :
```python
df = dataframes['fichier.xlsx']
personnes = df[df['poste'] == 46][['nom', 'fonction']]
count = len(personnes)

result = f"👥 {{count}} personne(s) interviendront sur le poste 46 :\\n\\n"
for i, (_, p) in enumerate(personnes.iterrows(), 1):
    result += f"{{i}}. {{p['nom']}} - {{p['fonction']}}\\n"
```

Exemple 3 - Avec insight/analyse :
```python
df = dataframes['fichier.xlsx']
retards = df[df['temps_reel'] > df['temps_prevu']]
pct_retard = (len(retards) / len(df)) * 100

result = f"⚠️ Analyse des retards :\\n\\n"
result += f"• {{len(retards)}} assemblages en retard sur {{len(df)}} ({{pct_retard:.1f}}%)\\n"
result += f"• Retard moyen : {{retards['difference'].mean().seconds // 60}} minutes\\n"
```

Exemple 4 - Tableau synthétique :
```python
df = dataframes['fichier.xlsx']
summary = df.groupby('poste').agg({{'temps': 'mean', 'quantite': 'sum'}}).round(2)
top5 = summary.nlargest(5, 'temps')

result = "📊 Résumé par poste (top 5) :\\n\\n"
for poste, row in top5.iterrows():
    result += f"• Poste {{poste}} : {{row['temps']:.1f}}h en moyenne, {{int(row['quantite'])}} pièces\\n"
```

GÉNÈRE MAINTENANT LE CODE (sans explications, juste le code) :
"""
        
        # 4. Appeler Gemini
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        generated_code = response.text.strip()
        
        # Nettoyer le code (retirer les balises markdown si présentes)
        if generated_code.startswith('```python'):
            generated_code = generated_code.split('```python')[1]
        if generated_code.startswith('```'):
            generated_code = generated_code.split('```')[1]
        if generated_code.endswith('```'):
            generated_code = generated_code.rsplit('```', 1)[0]
        generated_code = generated_code.strip()
        
        # 5. Préparer l'environnement d'exécution avec tous les imports nécessaires
        from datetime import datetime, timedelta
        import numpy as np
        
        dataframes = {filename: loaded_dataframes[filename] for filename in excel_files}
        exec_globals = {
            'dataframes': dataframes, 
            'pd': pd, 
            'np': np,
            'datetime': datetime,
            'timedelta': timedelta,
            'result': None
        }
        
        # 6. Exécuter le code généré
        try:
            exec(generated_code, exec_globals)
            result = exec_globals.get('result')
            
            # Formater le résultat pour l'affichage (optimisé pour la lisibilité humaine)
            if result is None:
                answer = "⚠️ Le code s'est exécuté mais n'a retourné aucun résultat."
            elif isinstance(result, str):
                # Si c'est déjà une chaîne formatée, l'utiliser directement
                answer = result
            elif isinstance(result, pd.DataFrame):
                # Formater les DataFrames de manière lisible
                if len(result) == 0:
                    answer = "ℹ️ Aucun résultat ne correspond à votre recherche."
                elif len(result) <= 20:
                    answer = "✅ Voici les résultats :\n\n" + result.to_string(index=False)
                else:
                    answer = f"✅ J'ai trouvé {len(result)} résultats. Voici les 20 premiers :\n\n"
                    answer += result.head(20).to_string(index=False)
                    answer += f"\n\n... et {len(result) - 20} résultats supplémentaires."
            elif isinstance(result, (list, dict)):
                answer = format_result_as_human_readable(result)
            elif isinstance(result, (int, float)):
                answer = f"✅ Résultat : {result:,}".replace(',', ' ')
            else:
                answer = f"✅ Résultat : {str(result)}"
            #print("Answer :", answer)
            return jsonify({
                'answer': answer,
                'code': generated_code,
                'error': False
            })
            
        except Exception as exec_error:
            return jsonify({
                'answer': f"Erreur lors de l'exécution du code : {str(exec_error)}",
                'code': generated_code,
                'error': True
            }), 200
    
    except Exception as e:
        return jsonify({
            'answer': f"Erreur serveur : {str(e)}",
            'error': True
        }), 500


def format_dataframes_description(dataframes_info):
    """Formate la description des DataFrames pour le prompt"""
    description = ""
    for df_info in dataframes_info:
        description += f"\n📊 Fichier : {df_info['filename']}\n"
        description += f"   - Dimensions : {df_info['shape'][0]} lignes × {df_info['shape'][1]} colonnes\n"
        description += f"   - Colonnes : {', '.join(df_info['columns'])}\n"
        description += f"   - Types : {df_info['dtypes']}\n"
        description += f"   - Échantillon (3 premières lignes) :\n{df_info['sample']}\n"
    return description


def format_result_as_human_readable(result):
    """Formate un résultat liste/dict de manière claire et lisible pour un humain"""
    if isinstance(result, list):
        if len(result) == 0:
            return "ℹ️ Aucun résultat trouvé."
        
        if isinstance(result[0], dict):
            # Liste de dictionnaires - formater comme une liste numérotée
            output = f"✅ J'ai trouvé {len(result)} résultat(s) :\n\n"
            for i, row in enumerate(result[:20], 1):  # Limiter à 20 pour la lisibilité
                output += f"{i}. "
                items = []
                for key, value in row.items():
                    # Formatter les nombres avec des espaces pour la lisibilité
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        items.append(f"{key}: {value:,}".replace(',', ' '))
                    else:
                        items.append(f"{key}: {value}")
                output += " | ".join(items) + "\n"
            
            if len(result) > 20:
                output += f"\n... et {len(result) - 20} résultat(s) supplémentaire(s)."
            return output
        else:
            # Liste simple
            output = f"✅ J'ai trouvé {len(result)} élément(s) :\n\n"
            for i, item in enumerate(result[:20], 1):
                output += f"{i}. {item}\n"
            if len(result) > 20:
                output += f"\n... et {len(result) - 20} élément(s) supplémentaire(s)."
            return output
    
    elif isinstance(result, dict):
        # Dictionnaire simple - formater en paires clé-valeur
        output = "✅ Résultat :\n\n"
        for key, value in result.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                output += f"• {key}: {value:,}".replace(',', ' ') + "\n"
            else:
                output += f"• {key}: {value}\n"
        return output
    
    return str(result)


# @app.route('/api/poste_piece', methods=['GET'])
# def poste_piece():
#     df = build_production_chains('uploads/MES_Extraction.xlsx', 
#                                  'uploads/PLM_DataSet.xlsx', 
#                                  'uploads/ERP_Equipes_Airplus.xlsx')
#     return html_poste_pieces(df)

if __name__ == '__main__':
    # Lance le serveur sur le port 5000, qui est la cible de l'API
    app.run(debug=True, port=5000)

