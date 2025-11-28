import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, Image as ImageIcon, Menu, CheckCircle, AlertCircle, X, Download, Maximize2, Minimize2 } from 'lucide-react';
import Chatbot from './components/Chatbot.jsx';

// --- IMPORTATION DU SERVICE API ---
import { fetchFilesFromApi, uploadFileToApi, getFileUrl } from './services/api.js';

// Styles CSS intégrés
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
  width: 380px;
  background-color: #ffffff;
  border-right: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease, padding 0.3s ease;
  flex-shrink: 0;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.05);
}

.sidebar.closed {
  width: 0;
  overflow: hidden;
  border-right: none;
  box-shadow: none;
}

/* --- SIDEBAR DROITE --- */
.sidebar-right {
  width: 350px;
  background-color: #ffffff;
  border-left: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease, transform 0.3s ease;
  flex-shrink: 0;
  box-shadow: -2px 0 5px rgba(0, 0, 0, 0.05);
  z-index: 20;
  position: relative;
}

.sidebar-right.closed {
  width: 0;
  overflow: hidden;
  border-left: none;
  box-shadow: none;
}

.sidebar-right-header {
  padding: 20px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-right-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #495057;
  margin: 0;
}

.sidebar-close-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.5rem;
  color: #868e96;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.sidebar-close-btn:hover {
  background-color: #e9ecef;
  color: #333;
}

.sidebar-right-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.poste-selection-group-sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.poste-selection-group-sidebar label {
  font-weight: 600;
  color: #495057;
  font-size: 0.95rem;
}

.poste-dropdown-sidebar {
  padding: 10px 12px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 0.9rem;
  background-color: white;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
}

.poste-dropdown-sidebar:hover {
  border-color: #4c6ef5;
  background-color: #f8f9fa;
}

.poste-dropdown-sidebar:focus {
  outline: none;
  border-color: #4c6ef5;
  box-shadow: 0 0 0 3px rgba(76, 110, 245, 0.1);
}

.sidebar-action-btn {
  padding: 10px 16px;
  background-color: #e3f2fd;
  color: #1976d2;
  border: 1px solid #90caf9;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.sidebar-action-btn:hover {
  background-color: #bbdefb;
  border-color: #64b5f6;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.2);
}

.sidebar-action-btn:disabled {
  background-color: #adb5bd;
  color: white;
  border-color: #adb5bd;
  cursor: not-allowed;
}

.sidebar-action-btn:active {
  transform: translateY(1px);
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
  color: #4c6ef5;
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
  transition: all 0.2s;
  border: 1px solid transparent;
}

.file-item:hover {
  background-color: #f1f3f5;
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
  min-width: 0;
}

.file-name {
  font-size: 0.9rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 260px;
  word-break: break-all;
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
  height: auto;
  min-height: 140px;
  background-color: #ffffff;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 16px 24px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  z-index: 10;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
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
  box-shadow: 0 2px 4px rgba(76, 110, 245, 0.3);
}

.primary-btn:hover {
  background-color: #3b5bdb;
  box-shadow: 0 4px 8px rgba(76, 110, 245, 0.4);
}

.primary-btn:disabled {
  background-color: #adb5bd;
  cursor: not-allowed;
  box-shadow: none;
}

.primary-btn:disabled:hover {
  background-color: #adb5bd;
  box-shadow: none;
}

.primary-btn[style*="background-color: #27ae60"]:hover {
  background-color: #229954;
  box-shadow: 0 4px 8px rgba(39, 174, 96, 0.4);
}

.primary-btn[style*="background-color: #e67e22"]:hover {
  background-color: #d35400;
  box-shadow: 0 4px 8px rgba(230, 126, 34, 0.4);
}

.primary-btn[style*="background-color: #8e44ad"]:hover {
  background-color: #7a3a8f;
  box-shadow: 0 4px 8px rgba(142, 68, 173, 0.4);
}

.primary-btn:active {
  transform: translateY(1px);
  box-shadow: none;
}

/* Modal Workflow */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  padding: 24px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 16px;
  color: #333;
}

.modal-body {
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #555;
  font-size: 0.9rem;
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #4c6ef5;
  box-shadow: 0 0 0 3px rgba(76, 110, 245, 0.1);
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.modal-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.modal-btn-primary {
  background-color: #8e44ad;
  color: white;
}

.modal-btn-primary:hover {
  background-color: #7a3a8f;
}

.modal-btn-secondary {
  background-color: #e9ecef;
  color: #333;
}

.modal-btn-secondary:hover {
  background-color: #dee2e6;
}

/* Quick Access Section */
.quick-access-toggle {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  color: #495057;
  transition: all 0.2s;
}

.quick-access-toggle:hover {
  background-color: #e9ecef;
  border-color: #4c6ef5;
}

/* Boutons Container */
.buttons-container {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
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
  flex-direction: column;
  background-color: #f8f9fa;
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

export default function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [status, setStatus] = useState({ type: '', message: '' });
  const fileInputRef = useRef(null);
  const [contenuDiv, setContenuDiv] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedPoste, setSelectedPoste] = useState("");
  const [showWorkflowModal, setShowWorkflowModal] = useState(false);
  const [workflowStep, setWorkflowStep] = useState("");
  const [workflowMaxNodes, setWorkflowMaxNodes] = useState(50);
  const [isQuickAccessOpen, setIsQuickAccessOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Liste des postes disponibles
  const postes = [
    "Montage train atterissage",
    "Assemblage moteur / fuselage / train atterissage",
    "Assemblage visserie fuselage partie basse",
    "Assemblage visserie train atterissage",
    "Assemblage fuselage centrale",
    "Assemblage queue avion",
    "Assemblage cockpit",
    "Assemblage aile gauche",
    "Assemblage réacteurs",
    "Fixation réacteur aile gauche",
    "Assemblage train atterissage gauche",
    "Fixation aile gauche avion / train atterissage",
    "Assemblage aile droite",
    "Fixation réacteur aile droite",
    "Assemblage train atterissage droit",
    "Fixation aile droit avion / train atterissage",
    "Fixation bout ailes",
    "Passage faisceaux électrique ailes",
    "Fixation lumières bout ailes",
    "Stickers cockpit",
    "Stickers réacteur",
    "Stickers fuselage gauche",
    "Stickers fuselage droit"
  ];

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      const data = await fetchFilesFromApi();
      setFiles(data);
    } catch (error) {
      setStatus({ type: 'error', message: error.message || "Impossible de charger les fichiers." });
    }
  };

  const votreFonctionAppelBackend = async () => {
    if (!selectedPoste) {
      setStatus({ type: 'error', message: 'Veuillez sélectionner un poste' });
      return;
    }
    setLoading(true);
    try {
      const reponse = await fetch(`http://localhost:5000/api/poste_piece?poste=${encodeURIComponent(selectedPoste)}`);
      if (reponse.ok) {
        const htmlRecu = await reponse.text();
        setContenuDiv(htmlRecu);
        setStatus({ type: 'success', message: 'Données chargées avec succès' });
      } else {
        const errorData = await reponse.json();
        setStatus({ type: 'error', message: errorData.error || 'Erreur serveur' });
      }
    } catch (err) {
      console.error("Le backend est injoignable", err);
      setStatus({ type: 'error', message: 'Le backend est injoignable' });
    } finally {
      setLoading(false);
    }
  };

  const afficherExperienceParWeekStep = async () => {
    setLoading(true);
    try {
      const reponse = await fetch('http://localhost:5000/api/experience_week_step');
      if (reponse.ok) {
        const htmlRecu = await reponse.text();
        setContenuDiv(htmlRecu);
        setStatus({ type: 'success', message: 'Expérience par semaine chargée' });
        setSelectedFile("");
      } else {
        const errorData = await reponse.json();
        setStatus({ type: 'error', message: errorData.error || 'Erreur serveur' });
      }
    } catch (err) {
      console.error("Le backend est injoignable", err);
      setStatus({ type: 'error', message: 'Le backend est injoignable' });
    } finally {
      setLoading(false);
    }
  };

  const afficherCostsParStep = async () => {
    setLoading(true);
    try {
      const reponse = await fetch('http://localhost:5000/api/costs_by_step');
      if (reponse.ok) {
        const htmlRecu = await reponse.text();
        setContenuDiv(htmlRecu);
        setStatus({ type: 'success', message: 'Coûts par étape chargés' });
        setSelectedFile("");
      } else {
        const errorData = await reponse.json();
        setStatus({ type: 'error', message: errorData.error || 'Erreur serveur' });
      }
    } catch (err) {
      console.error("Le backend est injoignable", err);
      setStatus({ type: 'error', message: 'Le backend est injoignable' });
    } finally {
      setLoading(false);
    }
  };

  const afficherWorkflowSankey = async (step, maxNodes) => {
    setLoading(true);
    try {
      const url = new URL('http://localhost:5000/api/step_workflow');
      if (step) {
        url.searchParams.append('step', encodeURIComponent(step));
      }
      url.searchParams.append('max_nodes', maxNodes);
      
      const reponse = await fetch(url.toString());
      if (reponse.ok) {
        const htmlRecu = await reponse.text();
        setContenuDiv(htmlRecu);
        setStatus({ type: 'success', message: 'Workflow Sankey chargé' });
        setSelectedFile("");
      } else {
        const errorData = await reponse.json();
        setStatus({ type: 'error', message: errorData.error || 'Erreur serveur' });
      }
    } catch (err) {
      console.error("Le backend est injoignable", err);
      setStatus({ type: 'error', message: 'Le backend est injoignable' });
    } finally {
      setLoading(false);
    }
  };

  const afficherRetards10min = async () => {
    setLoading(true);
    try {
      const reponse = await fetch('http://localhost:5000/api/retards_10min');
      if (reponse.ok) {
        const htmlRecu = await reponse.text();
        setContenuDiv(htmlRecu);
        setStatus({ type: 'success', message: 'Retards > 10 min chargés' });
        setSelectedFile("");
      } else {
        const errorData = await reponse.json();
        setStatus({ type: 'error', message: errorData.error || 'Erreur serveur' });
      }
    } catch (err) {
      console.error("Le backend est injoignable", err);
      setStatus({ type: 'error', message: 'Le backend est injoignable' });
    } finally {
      setLoading(false);
    }
  };

  const handleXlsxFileClick = async (file) => {
    setLoading(true);
    try {
      const filename = file.name || file.url.split('/').pop();
      const reponse = await fetch(`http://localhost:5000/api/excel_table/${encodeURIComponent(filename)}`);
      if (reponse.ok) {
        const htmlRecu = await reponse.text();
        setContenuDiv(htmlRecu);
        setStatus({ type: 'success', message: `Tableau ${filename} chargé` });
      } else {
        const errorData = await reponse.json();
        setStatus({ type: 'error', message: errorData.error || 'Erreur lors du chargement du fichier' });
      }
    } catch (err) {
      console.error("Erreur lors du chargement du fichier Excel", err);
      setStatus({ type: 'error', message: 'Erreur lors du chargement du fichier Excel' });
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    setStatus({ type: 'loading', message: 'Envoi en cours...' });
    try {
      await uploadFileToApi(file);
      setStatus({ type: 'success', message: 'Fichier importé !' });
      await loadFiles();
      setTimeout(() => setStatus({ type: '', message: '' }), 3000);
    } catch (error) {
      const errorMessage = error.message.includes('Failed to fetch') 
        ? "Erreur réseau : Le backend est-il lancé sur le port 5000 ?" 
        : error.message;
      setStatus({ type: 'error', message: errorMessage });
    }
    event.target.value = null;
  };

  return (
    <div className="app-container">
      <style>{cssStyles}</style>
      <Chatbot />

      {/* Mode plein écran du contenu */}
      {isFullscreen && contenuDiv && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: '#f8f9fa',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            padding: '20px'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '10px', gap: '10px' }}>
            <button 
              onClick={() => setIsFullscreen(false)}
              style={{
                padding: '8px 16px',
                backgroundColor: '#e74c3c',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '14px',
                fontWeight: 500
              }}
              title="Quitter le plein écran"
            >
              <Minimize2 size={16} />
              Quitter
            </button>
          </div>
          <div 
            style={{
              flex: 1,
              backgroundColor: '#fff',
              borderRadius: '8px',
              overflow: 'hidden', // Correction: iframe gère le scroll
              padding: '0px'
            }}
          >
            {/* Iframe Plein Ecran */}
            <iframe
              title="Résultat Plein Ecran"
              srcDoc={contenuDiv}
              style={{
                width: '100%',
                height: '100%',
                border: 'none',
                backgroundColor: '#fff'
              }}
              sandbox="allow-scripts allow-same-origin allow-popups"
            />
          </div>
        </div>
      )}

      {/* --- SIDEBAR --- */}
      {!isFullscreen && (
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
                className={`file-item ${selectedFile?.id === file.id ? 'selected' : ''}`}
                style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
              >
                <div 
                  onClick={() => {
                    setSelectedFile(file);
                    setContenuDiv("");
                    if (file.name.endsWith('.xlsx')) {
                      handleXlsxFileClick(file);
                    }
                  }}
                  style={{ flex: 1, display: 'flex', alignItems: 'center', cursor: 'pointer' }}
                >
                  <div className="file-icon-wrapper">
                    {file.type.includes('image') ? <ImageIcon size={18}/> : <FileText size={18}/>}
                  </div>
                  <div className="file-info">
                    <p className="file-name">{file.name}</p>
                    <p className="file-size">{file.size}</p>
                  </div>
                </div>
                <a 
                  href={getFileUrl(file.url)} 
                  download={file.name}
                  onClick={(e) => e.stopPropagation()}
                  style={{
                    padding: '6px 10px',
                    marginRight: '8px',
                    backgroundColor: '#4c6ef5',
                    color: 'white',
                    borderRadius: '4px',
                    border: 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    textDecoration: 'none',
                    fontSize: '12px',
                    fontWeight: 500
                  }}
                  title="Télécharger le fichier"
                >
                  <Download size={14} />
                </a>
              </div>
            ))
          )}
        </div>
      </div>
      )}

      {/* --- CONTENU PRINCIPAL --- */}
      {!isFullscreen && (
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
            
            <div className="buttons-container">
              <button 
                onClick={afficherExperienceParWeekStep}
                className="primary-btn"
                disabled={loading}
                style={{ backgroundColor: '#27ae60' }}
              >
                {loading ? "Chargement..." : "Expérience Week/Step"}
              </button>
              <button 
                onClick={afficherCostsParStep}
                className="primary-btn"
                disabled={loading}
                style={{ backgroundColor: '#e67e22' }}
              >
                {loading ? "Chargement..." : "Coûts par étape"}
              </button>
              <button 
                onClick={() => setShowWorkflowModal(true)}
                className="primary-btn"
                disabled={loading}
                style={{ backgroundColor: '#8e44ad' }}
              >
                {loading ? "Chargement..." : "Workflow Sankey"}
              </button>
            </div>

            <button 
              onClick={afficherRetards10min}
              className="primary-btn"
              disabled={loading}
              style={{ backgroundColor: '#e74c3c' }}
            >
              {loading ? "Chargement..." : "⚠️ Retards > 10 min"}
            </button>

            <button 
              onClick={() => setIsQuickAccessOpen(!isQuickAccessOpen)}
              className="primary-btn"
              style={{ backgroundColor: '#6c757d' }}
            >
              {isQuickAccessOpen ? "✕ Fermer" : "☰ Accès rapide"}
            </button>
          </div>

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

        {/* ZONE DE PRÉVISUALISATION */}
        <main className="preview-area">
          {(selectedFile || contenuDiv) ? (
            <div className="preview-card">
              
              {contenuDiv && (
                <div 
                  style={{ 
                    width: '100%', 
                    backgroundColor: '#e7f5ff',
                    borderBottom: '3px solid #4c6ef5',
                    padding: '18px 20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <h3 style={{ margin: 0, color: '#1971c2', fontSize: '1.1rem', fontWeight: 700 }}>
                    📊 Résultat de l'action
                  </h3>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <button 
                      onClick={() => setIsFullscreen(true)} 
                      style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', color: '#4c6ef5', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: '4px', transition: 'all 0.2s' }}
                      title="Afficher en plein écran"
                    >
                      <Maximize2 size={18} />
                    </button>
                    <button 
                      onClick={() => setContenuDiv("")} 
                      style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.5rem', color: '#666', padding: '4px 8px' }}
                    >
                      ✖
                    </button>
                  </div>
                </div>
              )}
              
              <div className="preview-card-header">
                  {selectedFile ? (
                    <>
                        <span>ID: {selectedFile.id}</span>
                        <span className="file-type-badge">{selectedFile.type}</span>
                    </>
                  ) : contenuDiv ? null : (
                    <span>Aperçu</span>
                  )}
              </div>
              
              <div className="preview-card-body" style={{ flexDirection: 'column', display: 'flex' }}>
                
                {/* --- 1. LE CONTENU HTML DU RÉSULTAT PYTHON (CORRIGÉ AVEC IFRAME) --- */}
                {contenuDiv && (
                  <div 
                    style={{ 
                      width: '100%', 
                      flex: 1, // Force le conteneur à prendre l'espace restant
                      backgroundColor: '#fff',
                      borderBottom: selectedFile ? '1px solid #eee' : 'none',
                      padding: '0', // Pas de padding pour ne pas écraser l'iframe
                      marginTop: '12px',
                      display: 'flex',
                      flexDirection: 'column',
                      minHeight: '500px' // Hauteur minimum de sécurité
                    }}
                  >
                    <iframe
                      title="Visualisation"
                      srcDoc={contenuDiv}
                      style={{
                        width: '100%',
                        flex: 1, // L'iframe prend 100% de la hauteur du parent
                        minHeight: '500px', // Hauteur minimum si le flex échoue
                        border: 'none',
                        display: 'block'
                      }}
                      sandbox="allow-scripts allow-same-origin allow-popups"
                    />
                  </div>
                )}

                {/* --- 2. L'APERÇU DU FICHIER --- */}
                {selectedFile && !contenuDiv && (
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
            <div className="empty-placeholder">
              <div className="empty-icon-circle">
                <Upload size={40} />
              </div>
              <h3>Aucun fichier sélectionné</h3>
              <p>Sélectionnez un document ou importez-en un nouveau.</p>
            </div>
          )}
        </main>

        {/* Modal Workflow */}
        {showWorkflowModal && (
          <div className="modal-overlay" onClick={() => setShowWorkflowModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">Configuration du Workflow Sankey</div>
              <div className="modal-body">
                <div className="form-group">
                  <label>Étape (optionnel - laisser vide pour toutes les étapes)</label>
                  <select 
                    value={workflowStep} 
                    onChange={(e) => setWorkflowStep(e.target.value)}
                  >
                    <option value="">-- Toutes les étapes --</option>
                    {postes.map((poste, index) => (
                      <option key={index} value={poste}>{poste}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Nombre maximum de nœuds par niveau</label>
                  <input 
                    type="number" 
                    min="5" 
                    max="200" 
                    value={workflowMaxNodes}
                    onChange={(e) => setWorkflowMaxNodes(parseInt(e.target.value) || 50)}
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button 
                  className="modal-btn modal-btn-secondary"
                  onClick={() => setShowWorkflowModal(false)}
                >
                  Annuler
                </button>
                <button 
                  className="modal-btn modal-btn-primary"
                  onClick={() => {
                    afficherWorkflowSankey(workflowStep || null, workflowMaxNodes);
                    setShowWorkflowModal(false);
                  }}
                  disabled={loading}
                >
                  {loading ? "Chargement..." : "Afficher"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
      )}

      {/* --- SIDEBAR DROITE --- */}
      {!isFullscreen && (
      <div className={`sidebar-right ${isQuickAccessOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-right-header">
          <h2 className="sidebar-right-title">Accès rapide</h2>
          <button 
            onClick={() => setIsQuickAccessOpen(false)}
            className="sidebar-close-btn"
            title="Fermer"
          >
            ✕
          </button>
        </div>

        <div className="sidebar-right-content">
          <div className="poste-selection-group-sidebar">
            <label htmlFor="poste-select-sidebar">Sélectionner un poste :</label>
            <select 
              id="poste-select-sidebar"
              value={selectedPoste} 
              onChange={(e) => setSelectedPoste(e.target.value)}
              className="poste-dropdown-sidebar"
            >
              <option value="">-- Sélectionner un poste --</option>
              {postes.map((poste, index) => (
                <option key={index} value={poste}>{poste}</option>
              ))}
            </select>
            <button 
              onClick={() => {
                votreFonctionAppelBackend();
                setSelectedFile("");
              }} 
              className="sidebar-action-btn"
              disabled={loading || !selectedPoste}
              title={!selectedPoste ? "Veuillez sélectionner un poste" : ""}
            >
              {loading ? "Chargement..." : "📊 Poste par pièces"}
            </button>
          </div>
        </div>
      </div>
      )}
    </div>
  );
}