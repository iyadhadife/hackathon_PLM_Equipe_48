import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Folder, File, Upload } from 'lucide-react'; // Icônes

const Sidebar = () => {
  const [files, setFiles] = useState([]);

  // Fonction pour récupérer la liste depuis Python
  const fetchFiles = async () => {
    try {
      const response = await axios.get('http://localhost:5000/files');
      setFiles(response.data);
    } catch (error) {
      console.error("Erreur backend:", error);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  // Fonction d'upload simple
  const handleUpload = async (event) => {
    const file = event.target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    await axios.post('http://localhost:5000/upload', formData);
    fetchFiles(); // On rafraichit la liste après upload
  };

  return (
    <div style={{ width: '250px', borderRight: '1px solid #ccc', padding: '10px', height: '100vh' }}>
      <h3>Explorateur</h3>
      
      {/* Bouton Upload */}
      <div style={{ marginBottom: '20px' }}>
        <input type="file" id="upload" style={{ display: 'none' }} onChange={handleUpload} />
        <label htmlFor="upload" style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px', color: 'blue' }}>
          <Upload size={16} /> Upload Fichier
        </label>
      </div>

      {/* Liste des fichiers */}
      <div className="file-list">
        {files.map((item, index) => (
          <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '5px' }}>
            {item.type === 'folder' ? <Folder size={16} /> : <File size={16} />}
            <span>{item.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Sidebar;