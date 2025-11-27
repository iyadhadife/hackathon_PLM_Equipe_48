// Fichier: src/components/FlowArea.jsx
import React, { useCallback } from 'react';
import { ReactFlow, Background, Controls, useNodesState, useEdgesState, addEdge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const initialNodes = [
  { id: '1', position: { x: 100, y: 100 }, data: { label: 'Début du projet' } },
  { id: '2', position: { x: 100, y: 200 }, data: { label: 'Analyse Backend' } },
];
const initialEdges = [{ id: 'e1-2', source: '1', target: '2' }];

const FlowArea = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  // Dans src/components/FlowArea.jsx
    return (
    // J'ajoute background: 'red' pour voir si le carré apparait
    <div style={{ width: '100%', height: '500px', backgroundColor: 'red' }}>
        <ReactFlow
        nodes={nodes}
        // ... le reste
        >
        <Controls />
        <Background />
        </ReactFlow>
    </div>
    );
};

export default FlowArea;