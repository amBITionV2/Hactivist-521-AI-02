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
              size: 20,
              font: {
                size: 12,
                color: '#ffffff'
              },
              borderWidth: 2,
            },
            edges: {
              width: 2,
              color: '#ffffff',
              arrows: 'to',
              font: {
                size: 10,
                align: 'middle',
                color: '#ffffff',
                strokeWidth: 0
              }
            },
            physics: {
              enabled: true,
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