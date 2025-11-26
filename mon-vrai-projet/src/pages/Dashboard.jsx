// Fichier: src/pages/Dashboard.jsx
import React from 'react';
import Sidebar from '../components/sidebar';
import FlowArea from '../components/flowarea';

const Dashboard = () => {
  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* Partie Gauche : Sidebar */}
      <Sidebar />
      
      {/* Partie Droite : React Flow */}
      <div style={{ flex: 1, height: '100%' }}>
        <FlowArea />
      </div>
    </div>
  );
};

export default Dashboard;