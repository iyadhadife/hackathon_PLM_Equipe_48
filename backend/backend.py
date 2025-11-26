import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Autorise React à accéder au serveur

UPLOAD_FOLDER = './uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 1. Route pour lister les fichiers (Sidebar)
@app.route('/files', methods=['GET'])
def list_files():
    files_list = []
    # On scanne le dossier uploads
    for root, dirs, files in os.walk(UPLOAD_FOLDER):
        for name in files:
            # On crée une structure simple
            files_list.append({"name": name, "type": "file", "path": os.path.join(root, name)})
        for name in dirs:
            files_list.append({"name": name, "type": "folder", "path": os.path.join(root, name)})
    return jsonify(files_list)

# 2. Route pour upload un fichier
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    return jsonify({"message": "File uploaded successfully"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)