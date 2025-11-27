import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, Image as ImageIcon, Menu, CheckCircle, AlertCircle, X } from 'lucide-react';

// --- CORRECTION : IMPORTATION DU SERVICE API (Ajout de .js pour la résolution du chemin) ---
import { fetchFilesFromApi, uploadFileToApi, getFileUrl } from './services/api.js';

// Styles CSS intégrés pour garantir le fonctionnement en un seul fichier
const cssStyles = `
/* --- RESET & GLOBAL --- */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: #f8f9fa;
  color: #333;
  height: 100vh;
  overflow: hidden;
}

.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* --- SIDEBAR --- */
.sidebar {
  width: 280px;
  background-color: #ffffff;
  border-right: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease, padding 0.3s ease;
  flex-shrink: 0;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.05); /* Ajout d'une légère ombre */
}

.sidebar.closed {
  width: 0;
  overflow: hidden;
  border-right: none;
  box-shadow: none;
}

.sidebar-header {
  height: 64px;
  padding: 0 16px;
  border-bottom: 1px solid #f1f3f5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fafbcb;
}

.sidebar-title {
  font-weight: 700;
  color: #4c6ef5; /* Indigo */
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.file-count {
  background-color: #edf2ff;
  color: #4c6ef5;
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 600;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.empty-state-text {
  text-align: center;
  margin-top: 40px;
  color: #adb5bd;
  font-size: 0.9rem;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 10px;
  margin-bottom: 6px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s; /* Transition sur tous les éléments */
  border: 1px solid transparent;
}

.file-item:hover {
  background-color: #f1f3f5; /* Légère couleur au survol */
  border-color: #e9ecef;
}

.file-item.selected {
  background-color: #edf2ff;
  border-color: #bac8ff;
  color: #364fc7;
}

.file-icon-wrapper {
  margin-right: 12px;
  color: #868e96;
  display: flex;
  align-items: center;
  /* Correction: Assurer la taille et la couleur de l'icone */
  padding: 8px;
  border-radius: 6px;
  background-color: #f1f3f5;
}

.file-item.selected .file-icon-wrapper {
  color: #4c6ef5;
  background-color: #ffffff;
}

.file-info {
  flex: 1;
  min-width: 0; /* Important pour le text-overflow */
}

.file-name {
  font-size: 0.9rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 0.75rem;
  color: #adb5bd;
}

/* --- MAIN CONTENT --- */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  min-width: 0;
}

/* HEADER */
.top-header {
  height: 64px;
  background-color: #ffffff;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05); /* Légère ombre */
  z-index: 10;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  color: #495057;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.icon-btn:hover {
  background-color: #f1f3f5;
}

.page-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #343a40;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 500;
}
.status-badge.loading { background-color: #e7f5ff; color: #1c7ed6; }
.status-badge.success { background-color: #e6fcf5; color: #0ca678; }
.status-badge.error { background-color: #fff5f5; color: #fa5252; }

.hidden-input {
  display: none;
}

.primary-btn {
  background-color: #4c6ef5;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(76, 110, 245, 0.3); /* Ajout d'une ombre bleue */
}

.primary-btn:hover {
  background-color: #3b5bdb;
  box-shadow: 0 4px 8px rgba(76, 110, 245, 0.4);
}

.primary-btn:active {
  transform: translateY(1px); /* Effet de clic */
  box-shadow: none;
}

/* PREVIEW AREA */
.preview-area {
  flex: 1;
  background-color: #f1f3f5;
  padding: 32px;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-card {
  background-color: white;
  width: 100%;
  max-width: 900px;
  height: 100%;
  max-height: 80vh;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #dee2e6;
}

.preview-card-header {
  padding: 12px 20px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  font-family: monospace;
  font-size: 0.8rem;
  color: #868e96;
}

.file-type-badge {
  background-color: #e9ecef;
  padding: 2px 6px;
  border-radius: 4px;
  color: #495057;
}

.preview-card-body {
  flex: 1;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
  /* Pattern subtil */
  background-image: radial-gradient(#dee2e6 1px, transparent 1px);
  background-size: 20px 20px;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.no-preview-box {
  background-color: rgba(255,255,255,0.9);
  padding: 40px;
  border-radius: 12px;
  text-align: center;
  border: 1px solid #fff;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

.icon-circle {
  width: 80px;
  height: 80px;
  background-color: #edf2ff;
  color: #4c6ef5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.no-preview-box h3 {
  margin-bottom: 8px;
  color: #343a40;
}

.no-preview-box p {
  color: #868e96;
  margin-bottom: 24px;
}

.link-btn {
  color: #4c6ef5;
  text-decoration: none;
  font-weight: 500;
  border-bottom: 2px solid transparent;
  transition: border-color 0.2s;
}

.link-btn:hover {
  border-bottom-color: #4c6ef5;
}

.empty-placeholder {
  text-align: center;
  color: #adb5bd;
  /* Correction: Assurer que l'état vide est bien centré et visible */
  padding: 50px; 
}

.empty-placeholder h3 {
    margin-top: 10px;
    font-size: 1.25rem;
    color: #495057;
}

.empty-placeholder p {
    font-size: 0.9rem;
    margin-top: 5px;
}

.empty-icon-circle {
  width: 100px;
  height: 100px;
  background-color: #e9ecef;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  color: #fff;
}
`;

// import { useState } from 'react';

// export default function MonBouton() {
//   // Stocke le HTML reçu du Python
//   const [contenuHtml, setContenuHtml] = useState(null);
//   const [chargement, setChargement] = useState(false);

//   const appelBackend = async () => {
//     setChargement(true);
//     try {
//       // Remplacez l'URL par la vôtre
//       const reponse = await fetch('http://localhost:5000/api/poste_piece');
      
//       if (!reponse.ok) {
//         throw new Error('Erreur réseau');
//       }

//       // 1. On récupère le texte brut (le HTML)
//       const htmlRecu = await reponse.text();
//       setContenuHtml(htmlRecu);

//     } catch (erreur) {
//       console.error("Erreur:", erreur);
//       alert("Impossible de contacter le backend Python");
//     } finally {
//       setChargement(false);
//     }
//   };

//   return (
//     <div style={{ padding: '20px' }}>
      
//       {/* LE BOUTON */}
//       <button 
//         onClick={appelBackend}
//         disabled={chargement}
//         style={{
//           padding: '10px 20px',
//           fontSize: '16px',
//           backgroundColor: '#007bff',
//           color: 'white',
//           border: 'none',
//           borderRadius: '5px',
//           cursor: 'pointer'
//         }}
//       >
//         {chargement ? 'Chargement...' : 'Récupérer le HTML'}
//       </button>

//       {/* L'AFFICHAGE DU HTML */}
//       {contenuHtml && (
//         <div 
//           style={{ marginTop: '20px', border: '1px solid #ddd', padding: '15px' }}
//           // 2. C'est ici qu'on injecte le HTML brut
//           dangerouslySetInnerHTML={{ __html: contenuHtml }}
//         />
//       )}
//     </div>
//   );
// }

export default function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [status, setStatus] = useState({ type: '', message: '' });
  const fileInputRef = useRef(null);
  const [contenuDiv, setContenuDiv] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadFiles(); // Utilisation de la nouvelle fonction loadFiles
  }, []);

  // Fonction wrapper pour charger les fichiers via le service
  const loadFiles = async () => {
    try {
      const data = await fetchFilesFromApi(); // APPEL AU SERVICE API
      setFiles(data);
    } catch (error) {
      // Le service gère déjà les erreurs de connexion et de parsing
      setStatus({ type: 'error', message: error.message || "Impossible de charger les fichiers." });
    }
  };

  const votreFonctionAppelBackend = async () => {
    // Optionnel : état de chargement
    setLoading(true); 

    try {
      // En GET, on appelle juste l'URL directement
      // Si vous devez passer un ID, ça se fait dans l'URL (ex: .../api/poste_piece?id=12)
      const reponse = await fetch('http://localhost:5000/api/poste_piece');
      
      if (reponse.ok) {
        // On récupère le texte (HTML)
        const htmlRecu = await reponse.text();
        
        // On met à jour la variable qui est liée à votre DIV existant
        setContenuDiv(htmlRecu);
      } else {
        console.error("Erreur serveur");
      }

    } catch (err) {
      console.error("Le backend est injoignable", err);
    } finally {
      setLoading(false);
    }
  };

  // Gérer l'upload en utilisant le service
  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setStatus({ type: 'loading', message: 'Envoi en cours...' });

    try {
      // APPEL AU SERVICE API POUR L'UPLOAD
      await uploadFileToApi(file);
      
      setStatus({ type: 'success', message: 'Fichier importé !' });
      await loadFiles(); // Recharger la liste après succès
      setTimeout(() => setStatus({ type: '', message: '' }), 3000);

    } catch (error) {
      // Le service API renvoie un objet Error avec le message formaté
      const errorMessage = error.message.includes('Failed to fetch') 
        ? "Erreur réseau : Le backend est-il lancé sur le port 5000 ?" 
        : error.message;

      setStatus({ type: 'error', message: errorMessage });
    }
    
    event.target.value = null;
  };

  return (
    <div className="app-container">
      {/* Injection des styles CSS */}
      <style>{cssStyles}</style>

      {/* --- SIDEBAR --- */}
      <div className={`sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <span className="sidebar-title">Mes Documents</span>
          <span className="file-count">{files.length}</span>
        </div>
        
        <div className="file-list">
          {files.length === 0 ? (
            <div className="empty-state-text">Aucun fichier</div>
          ) : (
            files.map(file => (
              <div 
                key={file.id}
                onClick={() => {
                  setSelectedFile(file);
                  setContenuDiv("");
                }}
                className={`file-item ${selectedFile?.id === file.id ? 'selected' : ''}`}
              >
                <div className="file-icon-wrapper">
                  {file.type.includes('image') ? <ImageIcon size={18}/> : <FileText size={18}/>}
                </div>
                <div className="file-info">
                  <p className="file-name">{file.name}</p>
                  <p className="file-size">{file.size}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* --- CONTENU PRINCIPAL --- */}
      <div className="main-content">
        
        {/* HEADER */}
        <header className="top-header">
          
          {/* PARTIE GAUCHE (Menu + Titre + Bouton Python) */}
          <div className="header-left">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="icon-btn"
            >
              <Menu size={20}/>
            </button>
            <h1 className="page-title">
              {selectedFile ? selectedFile.name : 'Tableau de bord'}
            </h1>
            
            {/* Bouton Python */}
            <div style={{ marginLeft: '15px' }}>
                <button 
                  onClick={() => {
                    votreFonctionAppelBackend();
                    setSelectedFile("");
                  }} 
                  className="primary-btn"
                >
                  Poste par pièces
                </button>
            </div>
          </div>

          {/* PARTIE DROITE (Status + Upload) */}
          <div className="header-right">
            {status.message && (
              <div className={`status-badge ${status.type}`}>
                {status.type === 'error' ? <AlertCircle size={14}/> : 
                 status.type === 'success' ? <CheckCircle size={14}/> : null}
                {status.message}
              </div>
            )}

            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              className="hidden-input" 
            />
            <button 
              onClick={() => fileInputRef.current.click()}
              className="primary-btn"
            >
              <Upload size={18} /> 
              <span>Importer</span>
            </button>
          </div>
          
        </header>

        {/* ZONE DE PRÉVISUALISATION (Logique Corrigée) */}
        <main className="preview-area">
          
          {/* CONDITION PRINCIPALE : Afficher la carte si un fichier OU du contenu Python est là */}
          {(selectedFile || contenuDiv) ? (
            <div className="preview-card">
              
              {/* EN-TÊTE de la Carte */}
              <div className="preview-card-header">
                  {selectedFile ? (
                    <>
                        <span>ID: {selectedFile.id}</span>
                        <span className="file-type-badge">{selectedFile.type}</span>
                    </>
                  ) : (
                    // Titre générique si seul le résultat Python est affiché
                    <span>Résultat de l'action</span>
                  )}
              </div>
              
              {/* CORPS : Utilise flex-column pour empiler les éléments */}
              <div className="preview-card-body" style={{ flexDirection: 'column', display: 'flex' }}>
                
                {/* --- 1. LE RÉSULTAT PYTHON (Toujours en haut s'il est présent) --- */}
                {contenuDiv && (
                    <div 
                      className="python-result-box"
                      style={{ 
                        width: '100%', 
                        backgroundColor: '#fff',
                        borderBottom: selectedFile ? '1px solid #eee' : 'none',
                        padding: '20px',
                        flexShrink: 0
                      }}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                            <h3 style={{ margin: 0, color: '#007bff', fontSize: '1rem' }}>Réponse du Backend</h3>
                            <button 
                                onClick={() => setContenuDiv("")} 
                                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', color: '#999' }}
                            >
                                ✖
                            </button>
                        </div>
                        {/* Injection du HTML */}
                        <div dangerouslySetInnerHTML={{ __html: contenuDiv }} />
                    </div>
                )}

                {/* --- 2. L'APERÇU DU FICHIER (S'affiche en dessous s'il est présent) --- */}
                {selectedFile && (
                    <div style={{ flex: 1, padding: '20px', display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%' }}>
                        {selectedFile.type.includes('image') ? (
                          <img 
                            src={getFileUrl(selectedFile.url)} 
                            alt="Preview" 
                            className="preview-image" 
                          />
                        ) : (
                          <div className="no-preview-box">
                            <div className="icon-circle">
                              <FileText size={40} />
                            </div>
                            <h3>{selectedFile.name}</h3>
                            <p>L'aperçu n'est pas disponible.</p>
                            <a 
                              href={getFileUrl(selectedFile.url)} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="link-btn"
                            >
                              Ouvrir le fichier
                            </a>
                          </div>
                        )}
                    </div>
                )}

              </div>
            </div>
          ) : (
            // --- CAS VIDE : Si selectedFile est null ET contenuDiv est vide ---
            <div className="empty-placeholder">
              <div className="empty-icon-circle">
                <Upload size={40} />
              </div>
              <h3>Aucun fichier sélectionné</h3>
              <p>Sélectionnez un document ou importez-en un nouveau.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}