// Fichier: src/components/Sidebar.jsx
import React, { useEffect, useState } from 'react';
import api from '../services/api'; // On utilise notre service
import { Folder, File, Upload, RefreshCw } from 'lucide-react';

const Sidebar = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const response = await api.get('/files');
      setFiles(response.data);
    } catch (error) {
      console.error("Erreur de connexion:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post('/upload', formData);
      fetchFiles(); // Rafraichir la liste après upload
    } catch (error) {
      alert("Erreur lors de l'upload");
    }
  };

  return (
    <div style={{ width: '260px', borderRight: '1px solid #e0e0e0', display: 'flex', flexDirection: 'column', height: '100%', background: '#f9f9f9' }}>
      
      {/* En-tête Sidebar */}
      <div style={{ padding: '15px', borderBottom: '1px solid #e0e0e0' }}>
        <h3 style={{ margin: '0 0 15px 0' }}>Explorateur</h3>
        
        <label style={{ 
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            background: '#007bff', color: 'white', padding: '8px', borderRadius: '5px', cursor: 'pointer' 
          }}>
          <Upload size={18} /> 
          <span>Upload Fichier</span>
          <input type="file" style={{ display: 'none' }} onChange={handleUpload} />
        </label>
      </div>

      {/* Liste des fichiers */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
        {loading ? <p>Chargement...</p> : files.map((item, index) => (
          <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px', borderBottom: '1px solid #eee' }}>
            {item.type === 'folder' 
              ? <Folder size={18} color="#FFC107" /> 
              : <File size={18} color="#6c757d" />
            }
            <span style={{ fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {item.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Sidebar;