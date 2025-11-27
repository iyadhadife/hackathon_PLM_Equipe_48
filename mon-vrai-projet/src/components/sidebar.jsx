import React, { useState, useRef } from 'react';
import { Upload, FileText, Image as ImageIcon, X, Menu, File, ChevronRight } from 'lucide-react';

// Composant principal de l'application
export default function App() {
  // État pour stocker les fichiers (Dans une vraie app, cela viendrait du backend)
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  // Référence pour l'input de fichier caché
  const fileInputRef = useRef(null);

  // Fonction déclenchée lors du clic sur le bouton "Importer"
  const handleUploadClick = () => {
    fileInputRef.current.click();
  };

  // Fonction de traitement du fichier sélectionné
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // SIMULATION BACKEND :
    // Ici, normalement vous feriez un :
    // const formData = new FormData();
    // formData.append('file', file);
    // await fetch('http://localhost:5000/upload', { method: 'POST', body: formData });
    
    // Pour la démo, on crée une URL locale pour afficher le fichier
    const newFile = {
      id: Date.now(),
      name: file.name,
      type: file.type,
      size: (file.size / 1024).toFixed(2) + ' KB',
      url: URL.createObjectURL(file), // Simulation d'URL
      content: "Contenu simulé pour l'aperçu..." // Simulation de contenu
    };

    setFiles(prev => [...prev, newFile]);
    setSelectedFile(newFile);
    
    // Reset de l'input pour permettre de ré-uploader le même fichier si besoin
    event.target.value = null; 
  };

  // Sélectionner un fichier dans la sidebar
  const handleSelectFile = (file) => {
    setSelectedFile(file);
  };

  // Supprimer un fichier (Optionnel mais utile)
  const handleDeleteFile = (e, id) => {
    e.stopPropagation(); // Empêche la sélection du fichier lors du clic sur supprimer
    setFiles(files.filter(f => f.id !== id));
    if (selectedFile && selectedFile.id === id) {
      setSelectedFile(null);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans text-gray-800">
      
      {/* --- SIDEBAR --- */}
      <div 
        className={`${isSidebarOpen ? 'w-72' : 'w-0'} transition-all duration-300 bg-white border-r border-gray-200 flex flex-col`}
      >
        <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gray-50">
          <h2 className="font-bold text-lg text-indigo-600 truncate">Mes Documents</h2>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {files.length === 0 ? (
            <div className="text-center mt-10 text-gray-400 text-sm">
              <File className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>Aucun fichier</p>
            </div>
          ) : (
            <ul className="space-y-1">
              {files.map(file => (
                <li 
                  key={file.id}
                  onClick={() => handleSelectFile(file)}
                  className={`
                    group flex items-center p-3 rounded-lg cursor-pointer transition-colors text-sm
                    ${selectedFile && selectedFile.id === file.id ? 'bg-indigo-50 text-indigo-700 border border-indigo-100' : 'hover:bg-gray-100 text-gray-700'}
                  `}
                >
                  {/* Icône basée sur le type */}
                  <span className="mr-3 text-gray-400 group-hover:text-indigo-500">
                    {file.type.startsWith('image/') ? <ImageIcon size={18} /> : <FileText size={18} />}
                  </span>
                  
                  <div className="flex-1 min-w-0">
                    <p className="truncate font-medium">{file.name}</p>
                    <p className="text-xs text-gray-400">{file.size}</p>
                  </div>

                  <button 
                    onClick={(e) => handleDeleteFile(e, file.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 hover:text-red-600 rounded transition-all"
                    title="Supprimer"
                  >
                    <X size={14} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        
        {/* Footer Sidebar */}
        <div className="p-4 border-t border-gray-100 text-xs text-gray-400 text-center">
          {files.length} fichier(s) stocké(s)
        </div>
      </div>

      {/* --- CONTENU PRINCIPAL --- */}
      <div className="flex-1 flex flex-col h-full relative">
        
        {/* HEADER (Top Bar) */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm z-10">
          <div className="flex items-center">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 rounded-md hover:bg-gray-100 text-gray-600 mr-4 focus:outline-none"
            >
              <Menu size={20} />
            </button>
            <h1 className="text-xl font-semibold text-gray-800">
              {selectedFile ? selectedFile.name : 'Tableau de bord'}
            </h1>
          </div>

          {/* BOUTON D'IMPORTATION (En haut à droite) */}
          <div>
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              className="hidden" 
              accept="image/*,.pdf,.txt,.doc,.docx" // Ajoutez vos types acceptés ici
            />
            <button 
              onClick={handleUploadClick}
              className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors shadow-sm active:transform active:scale-95"
            >
              <Upload size={18} />
              <span>Importer un fichier</span>
            </button>
          </div>
        </header>

        {/* ZONE D'AFFICHAGE */}
        <main className="flex-1 overflow-auto bg-gray-50 p-8 flex items-center justify-center">
          {selectedFile ? (
            <div className="bg-white shadow-lg rounded-xl overflow-hidden max-w-4xl w-full border border-gray-200 flex flex-col h-[80vh]">
              {/* En-tête de la visionneuse */}
              <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                 <span className="text-sm font-medium text-gray-500 uppercase tracking-wider">Aperçu</span>
                 <span className="text-xs px-2 py-1 bg-gray-200 rounded text-gray-600">{selectedFile.type || 'Fichier inconnu'}</span>
              </div>
              
              {/* Contenu */}
              <div className="flex-1 overflow-auto p-6 flex items-center justify-center bg-gray-100/50">
                {selectedFile.type.startsWith('image/') ? (
                  <img 
                    src={selectedFile.url} 
                    alt="Aperçu" 
                    className="max-w-full max-h-full object-contain shadow-md rounded" 
                  />
                ) : (
                  <div className="text-center p-10 bg-white rounded-lg shadow-sm border border-gray-200 max-w-lg">
                    <FileText size={48} className="mx-auto text-indigo-300 mb-4" />
                    <p className="text-gray-600 mb-2">Aperçu non disponible pour ce type de fichier.</p>
                    <p className="text-sm text-gray-400">Le fichier a été téléchargé avec succès sur le serveur.</p>
                    <div className="mt-6 p-4 bg-gray-50 rounded text-left text-xs font-mono text-gray-500 overflow-hidden">
                      {JSON.stringify(selectedFile, null, 2)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* État vide (Aucun fichier sélectionné) */
            <div className="text-center text-gray-400 max-w-md">
              <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
                 <ChevronRight size={40} className="text-gray-400 ml-1" />
              </div>
              <h3 className="text-xl font-medium text-gray-600 mb-2">Aucun fichier sélectionné</h3>
              <p>Sélectionnez un fichier dans la barre latérale ou cliquez sur "Importer un fichier" pour commencer.</p>
            </div>
          )}
        </main>

      </div>
    </div>
  );
}