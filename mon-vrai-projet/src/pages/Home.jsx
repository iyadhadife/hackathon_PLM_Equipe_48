// Fichier: src/pages/Home.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';

const Home = () => {
  const navigate = useNavigate();

  return (
    <div style={{ 
      height: '100vh', display: 'flex', flexDirection: 'column', 
      alignItems: 'center', justifyContent: 'center', background: '#f4f4f4' 
    }}>
      <h1 style={{ fontSize: '3rem', color: '#333' }}>Projet Hackathon PLM</h1>
      <p style={{ fontSize: '1.2rem', color: '#666' }}>Gestion de fichiers et Diagrammes interactifs</p>
      
      <button 
        onClick={() => navigate('/app')}
        style={{ 
          marginTop: '30px', padding: '15px 30px', fontSize: '18px', 
          backgroundColor: '#007bff', color: 'white', border: 'none', 
          borderRadius: '8px', cursor: 'pointer', boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}
      >
        Accéder au Workspace
      </button>
    </div>
  );
};

export default Home;