import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

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

if __name__ == '__main__':
    # Lance le serveur sur le port 5000, qui est la cible de l'API
    app.run(debug=True, port=5000)