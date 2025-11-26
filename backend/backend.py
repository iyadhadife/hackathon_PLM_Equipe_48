import os
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- CRUCIAL : Active CORS pour autoriser les requêtes venant de React ---
CORS(app) 

# Configuration
UPLOAD_FOLDER = 'uploads'
# Liste des extensions qu'on accepte de lire comme du texte
TEXT_EXTENSIONS = {
    'txt', 'json', 'xml', 'bpmn', 'csv', 'md', 
    'js', 'ts', 'tsx', 'py', 'html', 'css', 'scss', 'sql', 'yml', 'yaml', 'env', 'xlsx'
}

# 1. Création du dossier d'upload s'il n'existe pas
if not os.path.exists(UPLOAD_FOLDER):
    try:
        os.makedirs(UPLOAD_FOLDER)
        print(f"Dossier '{UPLOAD_FOLDER}' créé.")
    except Exception as e:
        print(f"Erreur création dossier: {e}")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max

def is_text_file(filename):
    """Détermine si on peut afficher le contenu du fichier."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in TEXT_EXTENSIONS

# --- ROUTES API ---

@app.route('/api/files', methods=['GET'])
def list_files():
    """Renvoie la liste des fichiers."""
    files = []
    try:
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                if os.path.isfile(file_path):
                    ext = filename.split('.')[-1].lower() if '.' in filename else 'inconnu'
                    files.append({
                        'id': filename,
                        'name': filename,
                        'size': os.path.getsize(file_path),
                        'type': ext
                    })
        return jsonify(files)
    except Exception as e:
        print(f"Erreur list_files: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Gère l'upload multiple."""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucune partie fichier dans la requête'}), 400
    
    files = request.files.getlist('file')
    saved_count = 0
    errors = []

    for file in files:
        if file.filename == '':
            continue
            
        try:
            # secure_filename nettoie le nom (ex: "dossier/test.txt" -> "test.txt")
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            saved_count += 1
        except Exception as e:
            errors.append(f"Erreur sur {file.filename}: {str(e)}")
    
    return jsonify({
        'message': f'{saved_count} fichiers sauvegardés.',
        'errors': errors
    }), 200

@app.route('/api/files/<filename>', methods=['GET'])
def get_file_content(filename):
    """Lit le contenu d'un fichier."""
    try:
        safe_filename = secure_filename(filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        if not os.path.exists(path):
            return jsonify({'error': 'Fichier introuvable sur le serveur'}), 404
            
        # Si c'est un fichier texte, on essaie de le lire
        if is_text_file(safe_filename):
            try:
                # 'errors="replace"' est CRUCIAL : il remplace les caractères illisibles au lieu de planter
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                return jsonify({
                    'name': safe_filename,
                    'content': content,
                    'type': safe_filename.split('.')[-1].lower(),
                    'isBinary': False
                })
            except Exception as read_error:
                return jsonify({'error': f"Erreur lecture fichier: {str(read_error)}"}), 500
        else:
            # Fichier binaire (Image, PDF, Exe...)
            return jsonify({
                'name': safe_filename,
                'content': "⚠️ Ce fichier est binaire (Image ou exécutable) et ne peut pas être affiché en texte.",
                'type': safe_filename.split('.')[-1].lower(),
                'isBinary': True
            })

    except Exception as e:
        print(f"Erreur globale get_file: {e}")
        return jsonify({'error': f"Erreur serveur: {str(e)}"}), 500

# Route de test simple pour voir si le serveur répond
@app.route('/', methods=['GET'])
def health_check():
    return "Le serveur Flask fonctionne ! Utilisez les routes /api/..."

if __name__ == '__main__':
    # Lance le serveur sur le port 5000
    print("Démarrage du serveur Flask sur http://127.0.0.1:5000")
    app.run(debug=True, port=5000)