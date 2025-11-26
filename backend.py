import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Active CORS pour permettre à votre frontend React (Home.tsx/App.tsx) 
# de communiquer avec ce backend sur le port 5000.
CORS(app)

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'uploads'
# Extensions que l'on considère comme "Texte" et qu'on peut afficher dans l'éditeur
TEXT_EXTENSIONS = {
    'txt', 'json', 'xml', 'bpmn', 'csv', 'md', 
    'js', 'ts', 'tsx', 'py', 'html', 'css', 'sql', 'yml', 'yaml'
}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max

def is_text_file(filename):
    """Vérifie si le fichier est affichable en tant que texte."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in TEXT_EXTENSIONS

# --- ROUTES API ---

@app.route('/api/files', methods=['GET'])
def list_files():
    """Renvoie la liste des fichiers pour l'explorateur React."""
    files = []
    try:
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                if os.path.isfile(file_path):
                    ext = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
                    files.append({
                        'id': filename, # On utilise le nom comme ID simple
                        'name': filename,
                        'size': os.path.getsize(file_path),
                        'type': ext
                    })
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Gère l'upload venant du bouton 'Ouvrir un Dossier'."""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier reçu'}), 400
    
    files = request.files.getlist('file')
    saved_count = 0
    errors = []

    for file in files:
        if file.filename == '':
            continue
            
        try:
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            saved_count += 1
        except Exception as e:
            errors.append(f"Erreur {file.filename}: {str(e)}")
    
    return jsonify({
        'message': f'{saved_count} fichiers sauvegardés.',
        'errors': errors
    }), 200

@app.route('/api/files/<filename>', methods=['GET'])
def get_file_content(filename):
    """
    Renvoie le contenu du fichier pour l'affichage.
    Gère intelligemment les fichiers binaires (images) pour ne pas faire planter l'app.
    """
    try:
        safe_filename = secure_filename(filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        if not os.path.exists(path):
            return jsonify({'error': 'Fichier introuvable'}), 404
            
        # Si c'est un fichier texte, on lit le contenu
        if is_text_file(safe_filename):
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return jsonify({
                'name': safe_filename,
                'content': content,
                'type': safe_filename.split('.')[-1].lower(),
                'isBinary': False
            })
        else:
            # Si c'est une image ou un binaire, on ne renvoie pas le contenu textuel
            return jsonify({
                'name': safe_filename,
                'content': "[Fichier Binaire/Image - Prévisualisation non disponible en mode texte]",
                'type': safe_filename.split('.')[-1].lower(),
                'isBinary': True
            })

    except Exception as e:
        return jsonify({'error': f"Erreur serveur: {str(e)}"}), 500

# Route optionnelle si vous voulez télécharger le fichier brut
@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], secure_filename(filename))

if __name__ == '__main__':
    # Le serveur écoute sur le port 5000
    app.run(debug=True, port=5000)