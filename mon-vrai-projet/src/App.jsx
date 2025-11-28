import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, Image as ImageIcon, Menu, CheckCircle, AlertCircle, X, Download, Maximize2 } from 'lucide-react';
import Chatbot from './components/Chatbot.jsx';

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
  width: 380px;
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

/* --- SIDEBAR DROITE - ACCÈS RAPIDE --- */
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
  box-shadow: 0 2px 4px rgba(0,0,0,0.05); /* Légère ombre */
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
  box-shadow: 0 2px 4px rgba(76, 110, 245, 0.3); /* Ajout d'une ombre bleue */
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
  transform: translateY(1px); /* Effet de clic */
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

/* Quick Access Section - Volet Déroulant */
.quick-access-section {
  margin-top: 16px;
  border-top: 1px solid #e9ecef;
  padding-top: 12px;
}

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

.quick-access-toggle .arrow {
  display: inline-block;
  transition: transform 0.3s ease;
  font-size: 0.8rem;
}

.quick-access-toggle .arrow.open {
  transform: rotate(180deg);
}

.quick-access-panel {
  margin-top: 12px;
  padding: 12px;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.quick-access-btn {
  padding: 8px 14px;
  background-color: #fff5f5;
  color: #c92a2a;
  border: 1px solid #ffa8a8;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.quick-access-btn:hover {
  background-color: #ffe3e3;
  border-color: #ff8787;
  box-shadow: 0 2px 8px rgba(201, 42, 42, 0.2);
}

.quick-access-btn:disabled {
  background-color: #adb5bd;
  color: white;
  border-color: #adb5bd;
  cursor: not-allowed;
}

.quick-access-btn:active {
  transform: translateY(1px);
}

/* Boutons Container */
.buttons-container {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

/* Poste Selection Group */
.poste-selection-group {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  padding-bottom: 8px;
  border-bottom: 1px solid #dee2e6;
  margin-bottom: 12px;
}

.poste-selection-group label {
  font-weight: 600;
  color: #495057;
  font-size: 0.95rem;
  margin: 0;
  white-space: nowrap;
}

.poste-dropdown-inline {
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 0.9rem;
  background-color: white;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
  flex: 1;
  min-width: 200px;
}

.poste-dropdown-inline:hover {
  border-color: #4c6ef5;
  background-color: #f8f9fa;
}

.poste-dropdown-inline:focus {
  outline: none;
  border-color: #4c6ef5;
  box-shadow: 0 0 0 3px rgba(76, 110, 245, 0.1);
}

.poste-btn {
  background-color: #e3f2fd;
  color: #1976d2;
  border: 1px solid #90caf9;
  white-space: nowrap;
}

.poste-btn:hover {
  background-color: #bbdefb;
  border-color: #64b5f6;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.2);
}

.poste-btn:disabled {
  background-color: #adb5bd;
  color: white;
  border-color: #adb5bd;
  cursor: not-allowed;
}

/* Quick Access Content */
.quick-access-content {
  padding: 12px 0;
}

/* Quick Actions Group */
.quick-actions-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.delays-btn {
  background-color: #fff5f5;
  color: #c92a2a;
  border: 1px solid #ffa8a8;
}

.delays-btn:hover {
  background-color: #ffe3e3;
  border-color: #ff8787;
  box-shadow: 0 2px 8px rgba(201, 42, 42, 0.2);
}

.delays-btn:disabled {
  background-color: #adb5bd;
  color: white;
  border-color: #adb5bd;
  cursor: not-allowed;
}

/* Quick Access Footer */
.quick-access-footer {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #dee2e6;
  margin-top: 12px;
}

.close-btn {
  background-color: #f1f3f5;
  color: #495057;
  border: 1px solid #dee2e6;
  flex: 1;
  margin-left: auto;
}

.close-btn:hover {
  background-color: #e9ecef;
  border-color: #adb5bd;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.close-btn:active {
  transform: translateY(1px);
}

.poste-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: 15px;
}

.poste-dropdown {
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 0.9rem;
  background-color: white;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 250px;
}

.poste-dropdown:hover {
  border-color: #4c6ef5;
  background-color: #f8f9fa;
}

.poste-dropdown:focus {
  outline: none;
  border-color: #4c6ef5;
  box-shadow: 0 0 0 3px rgba(76, 110, 245, 0.1);
}

/* PREVIEW AREA */
.preview-area {
  flex: 1;
  background-color: #f1f3f5;
  overflow: hidden;
  display: flex;
  position: relative;
}

.full-preview-container {
  width: 100%;
  height: 100%;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.floating-toolbar {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  padding: 16px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 100;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background-color: rgba(255,255,255,0.98);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  color: #495057;
  transition: all 0.25s ease;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  white-space: nowrap;
}

.toolbar-btn:hover {
  background-color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.toolbar-btn:active {
  transform: translateY(0);
}

.toolbar-btn.close-btn {
  color: #e03131;
  background-color: rgba(255,245,245,0.98);
}

.toolbar-btn.close-btn:hover {
  background-color: #fff5f5;
  box-shadow: 0 4px 12px rgba(224,49,49,0.25);
}

.result-full-container {
  flex: 1;
  width: 100%;
  padding: 32px 48px;
  background-color: #f8f9fa;
  overflow-y: auto;
  overflow-x: hidden;
}

.preview-card {
  background-color: white;
  width: 90%;
  max-width: 1000px;
  height: 85vh;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #dee2e6;
  margin: auto;
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
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #adb5bd;
  padding: 40px;
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
  margin-bottom: 20px;
  color: #868e96;
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

// Composant pour afficher correctement les graphiques Plotly
const PlotlyRenderer = ({ htmlContent }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current && htmlContent) {
      // Vider le conteneur
      containerRef.current.innerHTML = htmlContent;

      // Exécuter les scripts contenus dans le HTML
      const scripts = containerRef.current.querySelectorAll('script');
      scripts.forEach((oldScript) => {
        const newScript = document.createElement('script');
        
        // Copier tous les attributs
        Array.from(oldScript.attributes).forEach((attr) => {
          newScript.setAttribute(attr.name, attr.value);
        });
        
        // Copier le contenu
        newScript.textContent = oldScript.textContent;
        
        // Remplacer l'ancien script par le nouveau
        oldScript.parentNode.replaceChild(newScript, oldScript);
      });
    }
  }, [htmlContent]);

  return (
    <div 
      ref={containerRef} 
      className="python-result-content"
      style={{ width: '100%', minHeight: '500px' }}
    />
  );
};

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
    // Vérifier qu'un poste est sélectionné
    if (!selectedPoste) {
      setStatus({ type: 'error', message: 'Veuillez sélectionner un poste' });
      return;
    }

    setLoading(true);

    try {
      // Appel avec le poste en paramètre GET
      const reponse = await fetch(`http://localhost:5000/api/poste_piece?poste=${encodeURIComponent(selectedPoste)}`);
      
      if (reponse.ok) {
        // On récupère le texte (HTML)
        const htmlRecu = await reponse.text();
        
        // On met à jour la variable qui est liée à votre DIV existant
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
        setSelectedFile(""); // Vider la sélection fichier
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
        setSelectedFile(""); // Vider la sélection fichier
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
      
      console.log('🔍 Appel Workflow Sankey:', {
        step: step || 'Toutes',
        maxNodes,
        url: url.toString()
      });
      
      const reponse = await fetch(url.toString());
      
      console.log('📥 Réponse reçue:', {
        status: reponse.status,
        contentType: reponse.headers.get('content-type')
      });
      
      if (reponse.ok) {
        const htmlRecu = await reponse.text();
        console.log('✅ HTML reçu:', {
          length: htmlRecu.length,
          containsPlotly: htmlRecu.includes('plotly'),
          containsDiv: htmlRecu.includes('<div'),
          preview: htmlRecu.substring(0, 200)
        });
        setContenuDiv(htmlRecu);
        setStatus({ type: 'success', message: 'Workflow Sankey chargé' });
        setSelectedFile("");
      } else {
        const errorData = await reponse.json();
        console.error('❌ Erreur serveur:', errorData);
        setStatus({ type: 'error', message: errorData.error || 'Erreur serveur' });
      }

    } catch (err) {
      console.error("❌ Le backend est injoignable", err);
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
      // Extraire le nom du fichier du chemin complet
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

      {/* Widget Chatbot */}
      <Chatbot />

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
                className={`file-item ${selectedFile?.id === file.id ? 'selected' : ''}`}
                style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
              >
                <div 
                  onClick={() => {
                    setSelectedFile(file);
                    setContenuDiv("");
                    // Si c'est un fichier .xlsx, charger et afficher le tableau
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
                    fontWeight: 500,
                    transition: 'all 0.2s',
                    hover: { backgroundColor: '#364ec5' }
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
            
            {/* Boutons principaux */}
            <div className="buttons-container">
              <button 
                onClick={afficherExperienceParWeekStep}
                className="primary-btn"
                disabled={loading}
                style={{ backgroundColor: '#27ae60' }}
                title="Affiche l'expérience par semaine et étape"
              >
                {loading ? "Chargement..." : "Expérience Week/Step"}
              </button>
              <button 
                onClick={afficherCostsParStep}
                className="primary-btn"
                disabled={loading}
                style={{ backgroundColor: '#e67e22' }}
                title="Affiche les coûts par étape"
              >
                {loading ? "Chargement..." : "Coûts par étape"}
              </button>
              <button 
                onClick={() => setShowWorkflowModal(true)}
                className="primary-btn"
                disabled={loading}
                style={{ backgroundColor: '#8e44ad' }}
                title="Affiche le workflow Sankey"
              >
                {loading ? "Chargement..." : "Workflow Sankey"}
              </button>
            </div>

            {/* Bouton Retards indépendant */}
            <button 
              onClick={afficherRetards10min}
              className="primary-btn"
              disabled={loading}
              style={{ backgroundColor: '#e74c3c' }}
              title="Affiche les retards > 10 minutes"
            >
              {loading ? "Chargement..." : "⚠️ Retards > 10 min"}
            </button>

            {/* Bouton pour ouvrir la sidebar */}
            <button 
              onClick={() => setIsQuickAccessOpen(!isQuickAccessOpen)}
              className="primary-btn"
              style={{ backgroundColor: '#6c757d' }}
              title="Ouvrir l'accès rapide"
            >
              {isQuickAccessOpen ? "✕ Fermer" : "☰ Accès rapide"}
            </button>
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

        {/* ZONE DE PRÉVISUALISATION (Plein écran optimisé) */}
        <main className="preview-area">
          
          {/* CONDITION PRINCIPALE : Afficher le contenu si un fichier OU du contenu Python est là */}
          {(selectedFile || contenuDiv) ? (
            <div className="full-preview-container">
              
              {/* Barre d'outils flottante pour les résultats Python */}
              {contenuDiv && (
                <div className="floating-toolbar">
                  <button 
                    className="toolbar-btn"
                    onClick={() => {
                      const elem = document.querySelector('.full-preview-container');
                      if (elem.requestFullscreen) {
                        elem.requestFullscreen();
                      } else if (elem.webkitRequestFullscreen) {
                        elem.webkitRequestFullscreen();
                      } else if (elem.msRequestFullscreen) {
                        elem.msRequestFullscreen();
                      }
                    }}
                    title="Mode plein écran"
                  >
                    <Maximize2 size={18} />
                    <span>Plein écran</span>
                  </button>
                  <button 
                    className="toolbar-btn close-btn"
                    onClick={() => setContenuDiv("")}
                    title="Fermer"
                  >
                    <X size={18} />
                    <span>Fermer</span>
                  </button>
                </div>
              )}
              
              {/* --- 1. LE CONTENU HTML DU RÉSULTAT PYTHON --- */}
              {contenuDiv && (
                <div className="result-full-container">
                  {/* Injection du HTML avec style amélioré */}
                  <PlotlyRenderer htmlContent={contenuDiv} />
                </div>
              )}

              {/* --- 2. L'APERÇU DU FICHIER (S'affiche seulement s'il n'y a pas de contenu HTML) --- */}
              {selectedFile && !contenuDiv && (
                <div className="preview-card">
                  {/* EN-TÊTE de la Carte */}
                  <div className="preview-card-header">
                    <span>ID: {selectedFile.id}</span>
                    <span className="file-type-badge">{selectedFile.type}</span>
                  </div>
                  
                  {/* CORPS */}
                  <div className="preview-card-body">
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
                </div>
              )}

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

      {/* --- SIDEBAR DROITE - ACCÈS RAPIDE --- */}
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
          {/* Sélection du poste */}
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
    </div>
  );
}