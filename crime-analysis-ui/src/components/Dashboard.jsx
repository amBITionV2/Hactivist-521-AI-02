import React from 'react';
import GraphView from './GraphView';

const Dashboard = ({ selectedCase, simulation, onBack }) => {
  if (!selectedCase) return null;

  return (
    <div className="w-full max-w-7xl mx-auto p-4">
      <button onClick={onBack} className="mb-4 bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded">
        &larr; Back to Dashboard
      </button>
      <h2 className="text-2xl font-bold text-gray-200 mb-4">Case File #{selectedCase.id}: {selectedCase.filename}</h2>

      {/* This is the 3-column grid layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Column 1: Knowledge Graph */}
        <div className="bg-gray-800 p-4 rounded-lg shadow-lg">
          <h3 className="text-xl font-semibold text-teal-400 mb-2">Unified Case File (Knowledge Graph)</h3>
          <GraphView caseId={selectedCase.id} />
        </div>

        {/* Column 2: Inference Engine (Placeholder) */}
        <div className="bg-gray-800 p-4 rounded-lg shadow-lg">
          <h3 className="text-xl font-semibold text-teal-400 mb-2">Inference Engine (AI Detective)</h3>
          <p className="text-gray-400">Future home for key patterns, anomalies, and suspect composites.</p>
        </div>

        {/* Column 3: Simulation Engine */}
        <div className="bg-gray-800 p-4 rounded-lg shadow-lg">
          <h3 className="text-xl font-semibold text-teal-400 mb-2">Predictive & Simulation Engine</h3>
          <h4 className="text-lg font-semibold text-gray-300 mt-4">Crime Simulation (Narrative)</h4>
          <pre className="mt-2 text-gray-300 whitespace-pre-wrap font-sans text-sm h-96 overflow-y-auto">
            {simulation || "Generating simulation..."}
          </pre>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
