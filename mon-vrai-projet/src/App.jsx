import React from 'react';
import Sidebar from './components/Sidebar';
import { ReactFlow, Background } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Quelques noeuds de démo pour React Flow
const initialNodes = [
  { id: '1', position: { x: 200, y: 200 }, data: { label: 'Zone de visualisation' } },
];

function App() {
  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <Sidebar />
      <div style={{ flex: 1 }}>
        <ReactFlow nodes={initialNodes}>
          <Background />
        </ReactFlow>
      </div>
    </div>
  );
}

export default App;