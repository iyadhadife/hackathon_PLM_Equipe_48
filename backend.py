import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'json', 'xml', 'bpmn', 'csv', 'md', 'xlsx', 'py', 'java', 'js', 'html', 'css'}

# Création du dossier d'upload s'il n'existe pas
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Sert la page principale."""
    return render_template('home.html')

@app.route('/api/files', methods=['GET'])
def list_files():
    """Renvoie la liste des fichiers dans le dossier uploads."""
    files = []
    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                files.append({
                    'name': filename,
                    'size': os.path.getsize(file_path)
                })
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Gère l'upload de fichier."""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier envoyé'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'message': 'Fichier uploadé avec succès', 'filename': filename}), 200
    else:
        return jsonify({'error': 'Type de fichier non autorisé'}), 400

@app.route('/api/files/<filename>', methods=['GET'])
def get_file_content(filename):
    """Renvoie le contenu d'un fichier texte pour l'affichage."""
    try:
        safe_filename = secure_filename(filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        # Lecture simple pour la démo (on suppose des fichiers texte/code/json)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return jsonify({
            'name': safe_filename,
            'content': content,
            'path': path
        })
    except Exception as e:
        return jsonify({'error': f"Impossible de lire le fichier: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)