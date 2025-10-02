// src/App.jsx (Final Version)
import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  // State for the list of all cases
  const [cases, setCases] = useState([]);
  // State for the currently selected case's data
  const [selectedCase, setSelectedCase] = useState(null);
  const [simulation, setSimulation] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // --- File Upload State ---
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  // --- Detective Agent Chat State ---
  const [chatMessages, setChatMessages] = useState([]); // {role, text}
  const [chatInput, setChatInput] = useState('');
  const [clues, setClues] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);

  // --- Suspect Image Generation State ---
  const [suspectDescription, setSuspectDescription] = useState('');
  const [suspectImageUrl, setSuspectImageUrl] = useState('');
  const [imageLoading, setImageLoading] = useState(false);

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
    // ... (this function remains the same)
    if (!selectedFile) {
      setError('Please select a file first.');
      return;
    }
    setUploading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', selectedFile);
    try {
      await axios.post('http://localhost:8000/upload-case/', formData);
      setSelectedFile(null);
      document.getElementById('file-input').value = null; // Clear file input
      fetchCases();
    } catch (err) {
      setError('File upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleCaseSelect = async (caseItem) => {
    if (caseItem.status !== 'complete') {
      setError('Simulation can only be run on complete cases.');
      return;
    }
    setSelectedCase(caseItem);
    setIsLoading(true);
    setError('');
    try {
      const response = await axios.post(`http://localhost:8000/cases/${caseItem.id}/simulate`);
      setSimulation(response.data.simulation);
    } catch (err) {
      setError('Failed to fetch simulation.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToList = () => {
    setSelectedCase(null);
    setSimulation('');
    setError('');
  };

  // --- Detective Agent Chat Handlers ---
  const handleChatSend = async () => {
    if (!chatInput) return;
    setChatLoading(true);
    setError('');
    // Add user message to chat
    setChatMessages((prev) => [...prev, { role: 'user', text: chatInput }]);
    try {
      const caseText = selectedCase ? selectedCase.filename : '';
      const res = await axios.post('http://localhost:8000/detective/chat', {
        message: chatInput,
        case_file: caseText
      });
      setChatMessages((prev) => [...prev, { role: 'agent', text: res.data.reply }]);
      setClues(res.data.clues || []);
      setChatInput('');
    } catch (err) {
      setError('Detective agent chat failed.');
    } finally {
      setChatLoading(false);
    }
  };

  // --- Suspect Image Generation Handler ---
  const handleGenerateImage = async () => {
    if (!suspectDescription) return;
    setImageLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:8000/detective/suspect-image', {
        description: suspectDescription
      });
      setSuspectImageUrl(res.data.image_url);
    } catch (err) {
      setError('Suspect image generation failed.');
    } finally {
      setImageLoading(false);
    }
  };

  // --- Main Render Logic ---
  return (
    <div className="App">
      <header className="App-header">
        <h1>Cognitive Crime Analysis System</h1>

        {/* If a case is selected, show the detail view. Otherwise, show the dashboard. */}
        {selectedCase ? (
          // --- CASE DETAIL VIEW ---
          <div className="case-detail">
            <button onClick={handleBackToList}>&larr; Back to Dashboard</button>
            <h2>Simulation for Case: {selectedCase.filename}</h2>
            {isLoading && <p>Generating simulation...</p>}
            {error && <p className="error">{error}</p>}
            <pre className="simulation-text">{simulation}</pre>

            {/* Detective Agent Chat Section */}
            <div className="detective-chat">
              <h3>Detective Agent Chat</h3>
              <div className="chat-window">
                {chatMessages.map((msg, idx) => (
                  <div key={idx} className={msg.role === 'user' ? 'chat-user' : 'chat-agent'}>
                    <strong>{msg.role === 'user' ? 'You' : 'Detective'}:</strong> {msg.text}
                  </div>
                ))}
              </div>
              <input
                type="text"
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                placeholder="Ask the detective agent..."
                disabled={chatLoading}
              />
              <button onClick={handleChatSend} disabled={chatLoading || !chatInput}>
                {chatLoading ? 'Sending...' : 'Send'}
              </button>
              {/* Clues Section */}
              {clues.length > 0 && (
                <div className="clues-section">
                  <h4>Generated Clues</h4>
                  <ul>
                    {clues.map((clue, idx) => (
                      <li key={idx}>{clue}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Suspect Image Generation Section */}
            <div className="suspect-image-section">
              <h3>Suspect Image Generator</h3>
              <input
                type="text"
                value={suspectDescription}
                onChange={e => setSuspectDescription(e.target.value)}
                placeholder="Enter suspect description..."
                disabled={imageLoading}
              />
              <button onClick={handleGenerateImage} disabled={imageLoading || !suspectDescription}>
                {imageLoading ? 'Generating...' : 'Generate Image'}
              </button>
              {suspectImageUrl && (
                <div className="suspect-image-result">
                  <h4>Generated Suspect Image</h4>
                  <img src={suspectImageUrl} alt="Suspect" style={{ maxWidth: '300px', border: '1px solid #ccc' }} />
                </div>
              )}
            </div>
          </div>
        ) : (
          // --- DASHBOARD VIEW ---
          <>
            <div className="upload-section">
              <h2>Upload New Case File</h2>
              <input id="file-input" type="file" onChange={handleFileChange} />
              <button onClick={handleUpload} disabled={uploading}>
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
            <h2>Case Dashboard</h2>
            <button onClick={fetchCases} disabled={isLoading}>
              {isLoading ? 'Refreshing...' : 'Refresh List'}
            </button>
            {error && <p className="error">{error}</p>}
            <div className="case-list">
              <ul>
                {cases.map((caseItem) => (
                  <li key={caseItem.id} onClick={() => handleCaseSelect(caseItem)} className={caseItem.status === 'complete' ? 'clickable' : ''}>
                    <strong>File:</strong> {caseItem.filename} | <strong>Status:</strong> {caseItem.status}
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}
      </header>
    </div>
  );
}

export default App;