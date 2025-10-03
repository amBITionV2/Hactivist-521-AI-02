import React, { useState } from 'react';
import axios from 'axios';

const SuspectGenerator = ({ caseId, existingImageUrl, onImageGenerated }) => {
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    if (!description) {
      setError('Please provide a description of the suspect.');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      const response = await axios.post(
        `http://localhost:8000/cases/${caseId}/generate-suspect-image`,
        { description: description }
      );
      // Notify the parent component that a new image has been generated
      onImageGenerated(response.data.suspect_image_url);
    } catch (err) {
      setError('Failed to generate suspect image.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mt-4">
      <h4 className="text-lg font-semibold text-gray-300">Suspect Composite Generator</h4>
      <textarea
        className="w-full bg-gray-900 text-white p-2 rounded mt-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
        rows="3"
        placeholder="e.g., male, late 30s, short dark hair, wearing a red jacket, has a scar over his left eye..."
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <button
        onClick={handleGenerate}
        disabled={isLoading}
        className="mt-2 w-full bg-teal-500 hover:bg-teal-400 text-white font-bold py-2 px-4 rounded"
      >
        {isLoading ? 'Generating...' : 'Generate Image'}
      </button>
      {error && <p className="text-red-500 mt-2">{error}</p>}
      
      {existingImageUrl && (
        <div className="mt-4">
          <h5 className="text-md font-semibold text-gray-300">Generated Suspect Image:</h5>
          <img src={existingImageUrl} alt="Generated Suspect" className="w-full h-auto rounded-lg mt-2" />
        </div>
      )}
    </div>
  );
};

export default SuspectGenerator;
