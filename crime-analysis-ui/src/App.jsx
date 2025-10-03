import { useState, useEffect } from 'react';
import axios from 'axios';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [simulation, setSimulation] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const fetchCases = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/cases/');
      const sortedCases = response.data.sort((a, b) => b.id - a.id);
      setCases(sortedCases);
    } catch (err) {
      setError('Failed to fetch cases. Is the backend server running?');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first.');
      return;
    }
    setUploading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', selectedFile);
    try {
      await axios.post('http://localhost:8000/upload-case/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSelectedFile(null);
      document.getElementById('file-input').value = null;
      setTimeout(fetchCases, 1000); 
    } catch (err) {
      setError('File upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleCaseSelect = async (caseItem) => {
    if (caseItem.status !== 'complete') {
      setError('Details can only be viewed for complete cases.');
      return;
    }
    
    const isImageCase = caseItem.filename.match(/\.(jpeg|jpg|png|webp|gif|bmp)$/) != null;

    setSelectedCase(caseItem);
    setError('');

    if (!isImageCase) {
      setIsLoading(true);
      try {
        const response = await axios.post(`http://localhost:8000/cases/${caseItem.id}/simulate`);
        setSimulation(response.data.simulation);
      } catch (err) {
        setError('Failed to fetch simulation.');
      } finally {
        setIsLoading(false);
      }
    } else {
      setSimulation(''); 
    }
  };
  
  const handleBackToList = () => {
    setSelectedCase(null);
    setSimulation('');
    setError('');
  };

  const handleImageGenerated = (imageUrl) => {
    setSelectedCase(prevCase => ({
      ...prevCase,
      suspect_image: imageUrl
    }));
  };

  if (selectedCase) {
    return (
      <Dashboard
        selectedCase={selectedCase}
        simulation={simulation}
        onBack={handleBackToList}
        onImageGenerated={handleImageGenerated}
      />
    );
  }

  return (
    <div className="w-full min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-4xl font-bold text-center mb-2">Cognitive Crime Analysis System</h1>
      <div className="max-w-3xl mx-auto">
        <div className="bg-gray-800 p-6 my-8 rounded-lg shadow-lg">
          <h2 className="text-2xl font-semibold text-teal-400 mb-4">Upload New Case File (Text or Image)</h2>
          <input id="file-input" type="file" onChange={handleFileChange} className="mb-4" />
          <button onClick={handleUpload} disabled={uploading} className="bg-teal-500 hover:bg-teal-400 text-white font-bold py-2 px-4 rounded">
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
        
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
          <h2 className="text-2xl font-semibold text-teal-400 mb-4">Case Dashboard</h2>
          <button onClick={fetchCases} disabled={isLoading} className="mb-4 bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded">
            {isLoading ? 'Refreshing...' : 'Refresh List'}
          </button>
          {error && <p className="text-red-500">{error}</p>}
          <ul className="space-y-2">
            {cases.map((caseItem) => (
              <li key={caseItem.id} onClick={() => handleCaseSelect(caseItem)} className={`p-4 rounded ${caseItem.status === 'complete' ? 'cursor-pointer hover:bg-gray-700' : 'opacity-50'}`}>
                <strong>File:</strong> {caseItem.filename} | <strong>Status:</strong> {caseItem.status}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;