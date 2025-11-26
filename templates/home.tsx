import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap, 
  Node, 
  Edge,
  useNodesState, 
  useEdgesState,
  MarkerType
} from 'reactflow';
import { 
  FolderOpen, 
  FileText, 
  Activity, 
  Layers, 
  UploadCloud, 
  AlertCircle, 
  X,
  FileCode,
  Image as ImageIcon
} from 'lucide-react';

// Import indispensable pour React Flow
import 'reactflow/dist/style.css';

// --- TYPES ---
interface FileData {
  id: string;
  name: string;
  size: number;
  type: string;
}

interface FileContent {
  name: string;
  content: string;
  type: string;
}

// --- COMPOSANT SIMULÉ BPMN (Placeholder) ---
// Note: Pour utiliser bpmn-js réel, il faut 'npm install bpmn-js' et un useEffect complexe.
const BpmnPlaceholder: React.FC<{ content: string }> = ({ content }) => {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8 text-center border-2 border-dashed border-orange-200 bg-orange-50 rounded-lg">
      <Activity className="w-16 h-16 text-orange-400 mb-4" />
      <h3 className="text-lg font-bold text-orange-700">Fichier BPMN Détecté</h3>
      <p className="text-sm text-orange-600 mb-4">
        Ce fichier contient une définition de processus métier.
      </p>
      <div className="w-full text-left bg-white p-4 border border-orange-200 rounded overflow-auto max-h-64 text-xs font-mono">
        {content.substring(0, 500)}...
      </div>
    </div>
  );
};

export default function App() {
  // État global
  const [files, setFiles] = useState<FileData[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileContent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'text' | 'flow'>('text');

  // État ReactFlow
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // URL du Backend Flask
  const API_URL = 'http://127.0.0.1:5000/api';

  // 1. Récupérer la liste des fichiers
  const fetchFiles = async () => {
    try {
      const res = await fetch(`${API_URL}/files`);
      if (!res.ok) throw new Error("Erreur réseau");
      const data = await res.json();
      setFiles(data);
      updateFlowGraph(data);
    } catch (err) {
      console.error(err);
      setError("Impossible de charger les fichiers. Vérifiez que le serveur Python (app.py) est lancé.");
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  // 2. Transformer les fichiers en Graphe (Nœuds ReactFlow)
  const updateFlowGraph = useCallback((fileList: FileData[]) => {
    if (fileList.length === 0) return;

    // Création d'un nœud central "Dossier"
    const rootNode: Node = {
      id: 'root',
      type: 'input',
      data: { label: 'Uploads' },
      position: { x: 250, y: 0 },
      style: { background: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', width: 100, textAlign: 'center' }
    };

    // Création des nœuds fichiers
    const fileNodes: Node[] = fileList.map((file, index) => ({
      id: file.id,
      data: { label: file.name },
      position: { 
        x: (index % 4) * 180, 
        y: 150 + Math.floor(index / 4) * 100 
      },
      style: { 
        border: '1px solid #e2e8f0', 
        padding: '10px', 
        borderRadius: '6px', 
        fontSize: '12px',
        background: file.type === 'bpmn' ? '#fff7ed' : 'white',
        borderColor: file.type === 'bpmn' ? '#fdba74' : '#e2e8f0'
      }
    }));

    // Création des liens (Root -> Fichiers)
    const fileEdges: Edge[] = fileList.map(file => ({
      id: `e-root-${file.id}`,
      source: 'root',
      target: file.id,
      animated: true,
      style: { stroke: '#cbd5e1' },
    }));

    setNodes([rootNode, ...fileNodes]);
    setEdges(fileEdges);
  }, [setNodes, setEdges]);

  // 3. Upload de Dossier
  const handleFolderUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = event.target.files;
    if (!fileList || fileList.length === 0) return;

    const formData = new FormData();
    // On convertit la FileList en Array pour itérer
    Array.from(fileList).forEach(file => {
      formData.append('file', file);
    });

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      
      if (res.ok) {
        await fetchFiles(); // Rafraîchir la liste
      } else {
        setError(data.error || "Erreur lors de l'upload");
      }
    } catch (err) {
      setError("Erreur de connexion au serveur.");
    } finally {
      setLoading(false);
      // Reset l'input pour permettre de réuploader le même dossier si besoin
      event.target.value = '';
    }
  };

  // 4. Charger le contenu d'un fichier
  const handleFileClick = async (file: FileData) => {
    setError(null);
    try {
      const res = await fetch(`${API_URL}/files/${file.name}`);
      if (!res.ok) throw new Error("Fichier introuvable");
      const data = await res.json();
      setSelectedFile(data);
      // Si on est en mode flow, on bascule automatiquement en mode text pour voir le contenu
      if (viewMode === 'flow') setViewMode('text');
    } catch (err) {
      setError("Impossible de lire le fichier.");
    }
  };

  // Icône dynamique selon le type
  const getFileIcon = (type: string) => {
    switch(type) {
      case 'bpmn': return <Activity className="w-4 h-4 text-orange-500" />;
      case 'py':
      case 'js':
      case 'ts':
      case 'tsx': return <FileCode className="w-4 h-4 text-blue-500" />;
      case 'png':
      case 'jpg': return <ImageIcon className="w-4 h-4 text-purple-500" />;
      default: return <FileText className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="flex h-screen w-screen bg-gray-50 text-slate-800 font-sans overflow-hidden">
      
      {/* --- SIDEBAR --- */}
      <aside className="w-80 bg-white border-r border-gray-200 flex flex-col shadow-lg z-10 flex-shrink-0">
        <div className="p-5 border-b border-gray-100 bg-slate-50">
          <h1 className="text-xl font-bold text-slate-700 flex items-center gap-2">
            <Layers className="w-6 h-6 text-blue-600" /> 
            Projet Workflow
          </h1>
          <p className="text-xs text-gray-400 mt-1">Python Backend • React Frontend</p>
        </div>

        {/* Zone d'Upload */}
        <div className="p-4">
          <label className="group flex flex-col items-center justify-center w-full h-28 border-2 border-blue-200 border-dashed rounded-xl cursor-pointer bg-blue-50/50 hover:bg-blue-50 hover:border-blue-400 transition-all">
            <div className="flex flex-col items-center justify-center pt-2 pb-3">
              {loading ? (
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              ) : (
                <>
                  <UploadCloud className="w-8 h-8 text-blue-500 mb-2 group-hover:scale-110 transition-transform" />
                  <p className="text-sm text-blue-700 font-semibold">Ouvrir un Dossier</p>
                  <p className="text-xs text-blue-400">Glissez ou cliquez</p>
                </>
              )}
            </div>
            <input 
              type="file" 
              className="hidden" 
              // @ts-ignore : L'attribut webkitdirectory n'existe pas dans les types React standard mais fonctionne
              webkitdirectory="" 
              directory="" 
              multiple 
              onChange={handleFolderUpload}
            />
          </label>
        </div>

        {/* Liste des fichiers */}
        <div className="flex-1 overflow-y-auto px-3 py-2 scrollbar-thin">
          <div className="flex items-center justify-between mb-2 px-2">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Explorateur</h2>
            <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{files.length}</span>
          </div>
          
          <ul className="space-y-1">
            {files.map(file => (
              <li 
                key={file.id}
                onClick={() => handleFileClick(file)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer text-sm transition-all border border-transparent
                  ${selectedFile?.name === file.name 
                    ? 'bg-blue-50 text-blue-700 border-blue-100 shadow-sm font-medium' 
                    : 'hover:bg-gray-100 text-slate-600'
                  }`}
              >
                {getFileIcon(file.type)}
                <span className="truncate flex-1">{file.name}</span>
                <span className="text-xs text-gray-300">{(file.size / 1024).toFixed(0)}kb</span>
              </li>
            ))}
            {files.length === 0 && (
              <div className="text-center py-8 px-4 text-gray-400 text-sm italic border-2 border-dashed border-gray-100 rounded-lg m-2">
                Aucun fichier chargé.<br/>Utilisez le bouton ci-dessus.
              </div>
            )}
          </ul>
        </div>
        
        {/* Toggle Mode */}
        <div className="p-4 border-t border-gray-100 bg-white">
           <div className="grid grid-cols-2 bg-gray-100 p-1 rounded-lg">
             <button 
               onClick={() => setViewMode('text')} 
               className={`py-1.5 text-xs font-semibold rounded-md transition-all flex items-center justify-center gap-2
                 ${viewMode === 'text' ? 'bg-white text-slate-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
             >
               <FileText className="w-3 h-3" /> Fichier
             </button>
             <button 
               onClick={() => setViewMode('flow')} 
               className={`py-1.5 text-xs font-semibold rounded-md transition-all flex items-center justify-center gap-2
                 ${viewMode === 'flow' ? 'bg-white text-slate-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
             >
               <Activity className="w-3 h-3" /> Vue Graph
             </button>
           </div>
        </div>
      </aside>

      {/* --- MAIN CONTENT --- */}
      <main className="flex-1 flex flex-col relative h-full bg-slate-50/50">
        
        {/* Header Content */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm flex-shrink-0">
           <div className="flex items-center gap-3">
             {selectedFile ? (
               <>
                <div className="p-2 bg-blue-50 rounded-lg">{getFileIcon(selectedFile.type)}</div>
                <div>
                  <h2 className="font-semibold text-slate-800">{selectedFile.name}</h2>
                  <p className="text-xs text-slate-500">Mode Lecture Seule</p>
                </div>
               </>
             ) : (
               <div className="flex items-center gap-2 text-slate-400">
                 <FolderOpen className="w-5 h-5" />
                 <span>Tableau de bord</span>
               </div>
             )}
           </div>

           {error && (
             <div className="flex items-center gap-2 bg-red-50 text-red-600 px-4 py-2 rounded-full text-sm border border-red-100 animate-pulse">
               <AlertCircle className="w-4 h-4"/> 
               {error}
               <button onClick={() => setError(null)}><X className="w-3 h-3 ml-2 hover:text-red-800"/></button>
             </div>
           )}
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden relative p-6">
          
          {/* VUE 1: GRAPH VIEW (ReactFlow) */}
          {viewMode === 'flow' && (
            <div className="w-full h-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <ReactFlow 
                nodes={nodes} 
                edges={edges} 
                onNodesChange={onNodesChange} 
                onEdgesChange={onEdgesChange} 
                fitView
                attributionPosition="bottom-right"
              >
                <Background color="#f1f5f9" gap={16} />
                <Controls />
                <MiniMap style={{height: 100}} zoomable pannable />
              </ReactFlow>
            </div>
          )}

          {/* VUE 2: FILE VIEWER */}
          {viewMode === 'text' && (
            <div className="w-full h-full">
              {!selectedFile ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-400 bg-white/50 rounded-xl border-2 border-dashed border-gray-200">
                  <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                    <FolderOpen className="w-10 h-10 text-gray-300" />
                  </div>
                  <p className="font-medium">Aucun fichier sélectionné</p>
                  <p className="text-sm mt-1">Sélectionnez un fichier dans la barre latérale pour l'afficher.</p>
                </div>
              ) : (
                <div className="bg-white border border-gray-200 rounded-xl shadow-sm h-full flex flex-col overflow-hidden">
                  {/* Contenu selon le type */}
                  <div className="flex-1 overflow-auto p-0">
                    {selectedFile.type === 'bpmn' ? (
                      <BpmnPlaceholder content={selectedFile.content} />
                    ) : (
                      <div className="min-h-full">
                        <div className="bg-gray-50 border-b border-gray-100 px-4 py-2 text-xs text-gray-500 font-mono select-none">
                          1 &nbsp; // Contenu du fichier: {selectedFile.name}
                        </div>
                        <pre className="p-6 text-sm font-mono text-slate-700 whitespace-pre-wrap leading-relaxed">
                          {selectedFile.content}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

        </div>
      </main>
    </div>
  );
}