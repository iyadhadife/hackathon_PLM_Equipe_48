// Fichier: src/pages/Dashboard.jsx
import React, { useState } from 'react';
import Sidebar from '../components/sidebar';
import FlowArea from '../components/flowarea';

const Dashboard = () => {
  // C'est ici qu'on stocke les fichiers choisis pour qu'ils soient accessibles partout
  const [selectedFiles, setSelectedFiles] = useState([]);

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', overflow: 'hidden' }}>
      
      {/* 1. On passe la "mémoire" (state) à la Sidebar */}
      <div style={{ width: '300px', flexShrink: 0, height: '100%' }}>
        <Sidebar 
          selectedFiles={selectedFiles} 
          setSelectedFiles={setSelectedFiles} 
        />
      </div>
      
      {/* 2. On passe aussi les fichiers sélectionnés à la zone de dessin (pour plus tard) */}
      <div style={{ flex: 1, height: '100%', position: 'relative' }}>
        <FlowArea selectedFiles={selectedFiles} />
      </div>

    </div>
  );
};

export default Dashboard;