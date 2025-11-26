import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, Image as ImageIcon, Menu, CheckCircle, AlertCircle, X } from 'lucide-react';
import './App.css'; // Important : Import du fichier CSS

export default function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [status, setStatus] = useState({ type: '', message: '' });
  const fileInputRef = useRef(null);

  // 1. Charger les fichiers au démarrage (Mode API)
  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      // Assurez-vous que votre backend Flask tourne sur le port 5000
      // et que le proxy est configuré dans vite.config.js
      const response = await fetch('/api/files');
      if (response.ok) {
        const data = await response.json();
        setFiles(data);
      }
    } catch (error) {
      console.error("Erreur connexion:", error);
    }
  };

  // 2. Gérer l'upload
  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setStatus({ type: 'loading', message: 'Envoi en cours...' });

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        setStatus({ type: 'success', message: 'Fichier importé !' });
        await fetchFiles(); // Rafraîchir la liste
        
        // Effacer le message après 3 secondes
        setTimeout(() => setStatus({ type: '', message: '' }), 3000);
      } else {
        const err = await response.json();
        setStatus({ type: 'error', message: err.error || "Erreur upload" });
      }
    } catch (error) {
      console.error("Erreur upload:", error);
      setStatus({ type: 'error', message: "Erreur serveur" });
    }
    
    // Reset de l'input
    event.target.value = null;
  };

  return (
    <div className="app-container">
      
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
                onClick={() => setSelectedFile(file)}
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
          </div>
          
          <div className="header-right">
            {/* Messages de statut */}
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

        {/* ZONE DE PRÉVISUALISATION */}
        <main className="preview-area">
          {selectedFile ? (
            <div className="preview-card">
              <div className="preview-card-header">
                 <span>ID: {selectedFile.id}</span>
                 <span className="file-type-badge">{selectedFile.type}</span>
              </div>
              
              <div className="preview-card-body">
                {selectedFile.type.includes('image') ? (
                  <img 
                    src={selectedFile.url} 
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
                      href={selectedFile.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="link-btn"
                    >
                      Ouvrir le fichier
                    </a>
                  </div>
                )}
              </div>
            </div>
          ) : (
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