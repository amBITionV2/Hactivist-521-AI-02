import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network/standalone';
import 'vis-network/styles/vis-network.css';
import axios from 'axios';

const GraphView = ({ caseId }) => {
  const graphRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!caseId) return;

    const fetchAndDrawGraph = async () => {
      setIsLoading(true);
      setError('');
      try {
        const response = await axios.get(`http://localhost:8000/cases/${caseId}/graph`);
        const graphData = response.data;

        if (graphRef.current) {
          const options = {
            nodes: {
              shape: 'dot',
              size: 18, // Slightly smaller nodes
              font: {
                size: 12,
                color: '#ffffff'
            },
             borderWidth: 2,
          },
          edges: {
            width: 2,
            color: '#a0aec0', // Softer edge color
            arrows: 'to',
            font: {
              color: '#ffffff',
              size: 10,
              align: 'middle',
              strokeWidth: 0,
            },
            smooth: { // This makes the edges curved
              type: 'curvedCW',
              roundness: 0.2
            }
          },
          physics: {
            // We still use physics, but for the hierarchical layout
            enabled: true,
            hierarchicalRepulsion: {
              nodeDistance: 150, // Increase distance between nodes
            },
          },
          layout: {
            // This is the key change to make the graph hierarchical
            hierarchical: {
            enabled: true,
            sortMethod: 'directed', // Sorts from the source of the arrows
            direction: 'LR', // Layout from Left to Right
            },
          },
          interaction: {
            hover: true,
            tooltipDelay: 200,
          },
        };

          new Network(graphRef.current, graphData, options);
        }
      } catch (err) {
        setError('Failed to load graph data.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAndDrawGraph();
  }, [caseId]);

  if (error) return <p className="error">{error}</p>;

  return (
    <div className="graph-container">
      {isLoading && <p>Loading graph...</p>}
      <div ref={graphRef} style={{ height: '500px', width: '100%', border: '1px solid #4a5568', borderRadius: '8px', backgroundColor: '#1a202c' }} />
    </div>
  );
};

export default GraphView;