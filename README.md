
# Hackathon PLM Equipe 48

# Configuration du Chatbot avec Gemini

## Variables d'environnement requises

Pour que le chatbot fonctionne, vous devez configurer votre clé API Gemini.

### Option 1 : Variable d'environnement (recommandé)

Créez un fichier `.env` à la racine du dossier `backend/` :

```bash
GEMINI_API_KEY=votre_cle_api_gemini_ici
```

### Option 2 : Modification directe dans backend.py

Modifiez la ligne 23 dans `backend/backend.py` :

```python
GEMINI_API_KEY = 'VOTRE_CLE_API_GEMINI'
```

## Obtenir une clé API Gemini

1. Rendez-vous sur [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Connectez-vous avec votre compte Google
3. Cliquez sur "Get API Key"
4. Copiez votre clé API

## Installation des dépendances

### Backend (Python)

```bash
cd backend
pip install -r requirements.txt
```

### Frontend (React)

```bash
cd mon-vrai-projet
npm install
```

## Lancement de l'application

### 1. Lancer le backend Flask

```bash
cd backend
python backend.py
```

Le backend sera accessible sur `http://localhost:5000`

### 2. Lancer le frontend React

```bash
cd mon-vrai-projet
npm run dev
```

Le frontend sera accessible sur `http://localhost:5173` (ou le port indiqué)

## Utilisation du chatbot

1. Importez des fichiers Excel (.xlsx) via le bouton "Importer"
2. Cliquez sur l'icône de chat en bas à droite
3. Posez vos questions, par exemple :
   - "Quels sont les assemblages qui prennent le plus de temps ?"
   - "Combien y a-t-il de lignes dans le fichier ?"
   - "Montre-moi les 10 premières lignes"
   - "Quelles sont les personnes qui interviendront sur le poste 46 la semaine 2 ?"

## Fonctionnement technique

1. **Frontend** : L'utilisateur pose une question via le composant `Chatbot.jsx`
2. **API** : La question est envoyée à `/api/chat` via `sendChatMessage()` dans `api.js`
3. **Backend** : 
   - Flask charge les fichiers Excel en DataFrames Pandas
   - Construit un prompt avec la structure des données + question
   - Envoie le prompt à Gemini
   - Gemini génère du code Pandas
   - Le code est exécuté sur les DataFrames
   - Le résultat est retourné au frontend
4. **Affichage** : Le chatbot affiche la réponse (texte, tableau HTML, etc.)

## Structure des fichiers modifiés/créés

```
backend/
  ├── backend.py (modifié - ajout de l'endpoint /api/chat)
  └── requirements.txt (modifié - ajout de google-generativeai, openpyxl)

mon-vrai-projet/
  └── src/
      ├── App.jsx (modifié - intégration du composant Chatbot)
      ├── components/
      │   └── Chatbot.jsx (nouveau - widget chatbot)
      └── services/
          └── api.js (modifié - ajout de sendChatMessage)
```

## Dépannage

### Erreur "Module google.generativeai not found"
```bash
pip install google-generativeai
```

### Erreur "API key not valid"
Vérifiez que votre clé API Gemini est correcte dans le fichier `.env` ou `backend.py`

### Le chatbot ne répond pas
- Vérifiez que le backend Flask est bien lancé sur le port 5000
- Ouvrez la console du navigateur pour voir les erreurs réseau
- Vérifiez que des fichiers Excel sont bien uploadés dans `backend/uploads/`

### Erreur CORS
Si vous voyez des erreurs CORS dans la console, vérifiez que `flask-cors` est bien installé et activé dans `backend.py`
