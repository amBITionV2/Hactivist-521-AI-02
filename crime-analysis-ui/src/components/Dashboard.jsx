import React from 'react';
import GraphView from './GraphView';
import DetectiveChat from './DetectiveChat';
import SuspectGenerator from './SuspectGenerator';

const Dashboard = ({ selectedCase, simulation, onBack, onImageGenerated }) => {
  if (!selectedCase) return null;

  const isImageCase = selectedCase.image_analysis !== null;
  const API_URL = 'http://localhost:8000';

  return (
    <div className="w-full max-w-7xl mx-auto p-4">
      <button onClick={onBack} className="mb-4 bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded">
        &larr; Back to Case List
      </button>
      <h2 className="text-2xl font-bold text-gray-200 mb-4">Case File #{selectedCase.id}: {selectedCase.filename}</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Column 1: Visuals (Graph or Evidence) */}
        <div className="bg-gray-800 p-4 rounded-lg shadow-lg">
          {isImageCase ? (
            <>
              <h3 className="text-xl font-semibold text-teal-400 mb-2">Visual Evidence</h3>
              <img src={`${API_URL}/${selectedCase.file_path}`} alt={selectedCase.filename} className="w-full h-auto rounded-lg mt-4" />
            </>
          ) : (
            <>
              <h3 className="text-xl font-semibold text-teal-400 mb-2">Knowledge Graph</h3>
              <GraphView caseId={selectedCase.id} />
            </>
          )}
        </div>

        {/* Column 2: Inference Engine (Now with interactive tools) */}
        <div className="bg-gray-800 p-4 rounded-lg shadow-lg">
          <h3 className="text-xl font-semibold text-teal-400 mb-2">Inference Engine</h3>
          {/* Only show chat for text-based cases with a graph */}
          {!isImageCase && <DetectiveChat caseId={selectedCase.id} />}
          <SuspectGenerator 
            caseId={selectedCase.id} 
            existingImageUrl={selectedCase.suspect_image}
            onImageGenerated={onImageGenerated}
          />
        </div>

        {/* Column 3: AI Analysis */}
        <div className="bg-gray-800 p-4 rounded-lg shadow-lg">
          <h3 className="text-xl font-semibold text-teal-400 mb-2">AI Analysis</h3>
          <pre className="mt-2 text-gray-300 whitespace-pre-wrap font-sans text-sm h-96 overflow-y-auto">
            {isImageCase ? selectedCase.image_analysis : (simulation || "Generating text simulation...")}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;