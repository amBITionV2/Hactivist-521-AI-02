import React, { useState, useEffect } from 'react';
import { Upload, Search, Brain, Fingerprint, Activity, Lock, Eye, Zap } from 'lucide-react';
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
  
  // New UI state
  const [fileName, setFileName] = useState('No file (no file chosen)');
  const [processText, setProcessText] = useState(true);
  const [processMedia, setProcessMedia] = useState(false);
  const [activeIcon, setActiveIcon] = useState(0);
  const [pulse, setPulse] = useState(true);
  const [scanProgress, setScanProgress] = useState(0);

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

  // New UI animations
  useEffect(() => {
    const iconInterval = setInterval(() => {
      setActiveIcon(prev => (prev + 1) % 3);
    }, 2500);

    const pulseInterval = setInterval(() => {
      setPulse(prev => !prev);
    }, 1500);

    const scanInterval = setInterval(() => {
      setScanProgress(prev => (prev + 1) % 100);
    }, 50);

    return () => {
      clearInterval(iconInterval);
      clearInterval(pulseInterval);
      clearInterval(scanInterval);
    };
  }, []);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
    if (file) {
      setFileName(file.name);
    } else {
      setFileName('No file (no file chosen)');
    }
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
      setFileName('No file (no file chosen)');
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

  // Transform cases data for new UI
  const transformedCases = cases.map((caseItem, index) => {
    let status = 'PENDING';
    let color = 'text-gray-300';
    let icon = Eye;
    
    if (caseItem.status === 'complete') {
      status = 'SOLVED';
      color = 'text-white';
      icon = Lock;
    } else if (caseItem.status === 'processing') {
      status = 'ONGOING';
      color = 'text-gray-400';
      icon = Zap;
    }
    
    return {
      id: `CASE #${String(caseItem.id).padStart(4, '0')}-${String(index + 1).padStart(3, '0')}`,
      name: caseItem.filename,
      status: status,
      color: color,
      icon: icon,
      originalCase: caseItem
    };
  });

  return (
    <div className="min-h-screen bg-black text-white p-8 relative overflow-hidden">
      {/* Animated background gradient mesh - monochrome */}
      <div className="fixed inset-0 opacity-20">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
      </div>

      {/* Grid overlay */}
      <div className="fixed inset-0 opacity-10" style={{
        backgroundImage: `
          linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px)
        `,
        backgroundSize: '50px 50px'
      }}></div>

      {/* Floating particles - monochrome */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {[...Array(30)].map((_, i) => (
          <div
            key={i}
            className="absolute rounded-full bg-white/30"
            style={{
              width: Math.random() * 4 + 1 + 'px',
              height: Math.random() * 4 + 1 + 'px',
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animation: `float ${5 + Math.random() * 15}s ease-in-out infinite`,
              animationDelay: `${Math.random() * 5}s`
            }}
          />
        ))}
      </div>

      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translate(0, 0) rotate(0deg); }
          33% { transform: translate(30px, -30px) rotate(120deg); }
          66% { transform: translate(-20px, 20px) rotate(240deg); }
        }
        @keyframes glow {
          0%, 100% { 
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.2), 
                        0 0 40px rgba(255, 255, 255, 0.1),
                        inset 0 0 20px rgba(255, 255, 255, 0.05);
          }
          50% { 
            box-shadow: 0 0 30px rgba(255, 255, 255, 0.4), 
                        0 0 60px rgba(255, 255, 255, 0.2),
                        inset 0 0 30px rgba(255, 255, 255, 0.1);
          }
        }
        @keyframes scan {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
        @keyframes pulse-ring {
          0% { transform: scale(0.8); opacity: 0.8; }
          100% { transform: scale(2); opacity: 0; }
        }
        @keyframes shimmer {
          0% { background-position: -1000px 0; }
          100% { background-position: 1000px 0; }
        }
        .glow-effect {
          animation: glow 3s ease-in-out infinite;
        }
        .scan-line {
          animation: scan 4s linear infinite;
        }
        .shimmer {
          background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
          background-size: 1000px 100%;
          animation: shimmer 3s infinite;
        }
      `}</style>

      <div className="max-w-6xl mx-auto relative z-10">
        {/* Header with professional styling */}
        <div className="text-center mb-12 relative">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-20 bg-gradient-to-r from-transparent via-white/10 to-transparent blur-xl"></div>
          <h1 className="text-5xl font-bold tracking-wider relative text-white">
            Cognitive Crime Analysis System
          </h1>
          <div className="mt-2 text-gray-400 text-xs tracking-widest font-mono">
            [ NEURAL DETECTIVE INTERFACE v4.7 ]
          </div>
        </div>

        {/* Insert Case File Section */}
        <div className="relative mb-8 group">
          <div className="absolute inset-0 bg-white/5 rounded-lg blur-xl group-hover:blur-2xl transition-all duration-500"></div>
          <div className="relative bg-slate-900/80 backdrop-blur-xl border border-gray-700 rounded-lg p-6 glow-effect">
            {/* Corner decorations */}
            <div className="absolute top-0 left-0 w-6 h-6 border-t-2 border-l-2 border-white/50"></div>
            <div className="absolute top-0 right-0 w-6 h-6 border-t-2 border-r-2 border-white/50"></div>
            <div className="absolute bottom-0 left-0 w-6 h-6 border-b-2 border-l-2 border-white/50"></div>
            <div className="absolute bottom-0 right-0 w-6 h-6 border-b-2 border-r-2 border-white/50"></div>
            
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-white/10 rounded-lg">
                <Upload className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-xl font-semibold text-white">
                Insert Case File
              </h2>
              <div className="flex-1 h-px bg-gradient-to-r from-gray-500 to-transparent"></div>
            </div>
            
            <div className="space-y-4">
              <div className="relative bg-slate-800/50 rounded-lg p-4 border border-cyan-500/20 overflow-hidden group/input">
                <div className="absolute inset-0 shimmer opacity-0 group-hover/input:opacity-100"></div>
                <input
                  type="text"
                  value={fileName}
                  readOnly
                  className="w-full bg-transparent text-gray-300 outline-none relative z-10 font-mono text-sm"
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer group/check">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={processText}
                        onChange={(e) => setProcessText(e.target.checked)}
                        className="w-5 h-5 accent-white opacity-0 absolute"
                      />
                      <div className={`w-5 h-5 border-2 rounded ${processText ? 'border-white bg-white/20' : 'border-gray-500'} transition-all duration-300`}>
                        {processText && <div className="w-full h-full flex items-center justify-center text-white text-xs">✓</div>}
                      </div>
                    </div>
                    <span className="text-sm text-gray-300 group-hover/check:text-white transition-colors">Process Text Only</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer group/check">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={processMedia}
                        onChange={(e) => setProcessMedia(e.target.checked)}
                        className="w-5 h-5 accent-white opacity-0 absolute"
                      />
                      <div className={`w-5 h-5 border-2 rounded ${processMedia ? 'border-white bg-white/20' : 'border-gray-500'} transition-all duration-300`}>
                        {processMedia && <div className="w-full h-full flex items-center justify-center text-white text-xs">✓</div>}
                      </div>
                    </div>
                    <span className="text-sm text-gray-300 group-hover/check:text-white transition-colors">Process Images & Multimedia</span>
                  </label>
                </div>

                <div className="flex gap-3">
                  <label className="relative overflow-hidden bg-slate-800 hover:bg-slate-700 px-6 py-3 rounded-lg cursor-pointer transition-all duration-300 border border-gray-700 hover:border-gray-500 group/btn">
                    <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0 translate-x-[-100%] group-hover/btn:translate-x-[100%] transition-transform duration-1000"></div>
                    <input id="file-input" type="file" onChange={handleFileChange} className="hidden" />
                    <span className="relative z-10 text-white font-semibold text-sm tracking-wide">UPLOAD FILE</span>
                  </label>
                  <button 
                    onClick={handleUpload} 
                    disabled={uploading || !selectedFile} 
                    className="relative overflow-hidden bg-white text-black hover:bg-gray-200 px-6 py-3 rounded-lg font-semibold transition-all duration-300 shadow-lg shadow-white/20 hover:shadow-white/40 group/btn disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-black/10 to-transparent translate-x-[-100%] group-hover/btn:translate-x-[100%] transition-transform duration-700"></div>
                    <span className="relative z-10 text-sm tracking-wide">
                      {uploading ? 'ANALYZING...' : 'ANALYZE CASE'}
                    </span>
                  </button>
                </div>
              </div>
              
              {error && (
                <div className="mt-4 p-3 bg-red-900/50 border border-red-500/30 rounded-lg">
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Criminal Database Section */}
        <div className="relative mb-10 group">
          <div className="absolute inset-0 bg-white/5 rounded-lg blur-xl group-hover:blur-2xl transition-all duration-500"></div>
          <div className="relative bg-slate-900/80 backdrop-blur-xl border border-gray-700 rounded-lg p-6 overflow-hidden">
            {/* Animated scanning effect */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-white to-transparent scan-line opacity-30"></div>
            <div className="absolute bottom-0 right-0 w-20 h-20 bg-white/5 rounded-tl-full"></div>
            
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/10 rounded-lg">
                  <Search className="w-6 h-6 text-white" />
                </div>
                <h2 className="text-xl font-semibold text-white">
                  Criminal Database & Forecast
                </h2>
              </div>
              <button 
                onClick={fetchCases} 
                disabled={isLoading} 
                className="bg-slate-800/50 hover:bg-slate-700/50 px-4 py-2 rounded-lg text-sm transition-all duration-300 border border-gray-700 hover:border-gray-500 text-white disabled:opacity-50"
              >
                <span className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                  {isLoading ? 'Refreshing...' : 'Refresh Data'}
                </span>
              </button>
            </div>

            <div className="space-y-3">
              {transformedCases.map((caseItem, index) => {
                const IconComponent = caseItem.icon;
                return (
                  <div
                    key={index}
                    onClick={() => caseItem.originalCase.status === 'complete' ? handleCaseSelect(caseItem.originalCase) : null}
                    className={`relative bg-slate-800/40 rounded-lg p-5 border border-gray-800 hover:border-gray-600 transition-all duration-500 group/case overflow-hidden ${
                      caseItem.originalCase.status === 'complete' ? 'cursor-pointer' : 'opacity-50'
                    }`}
                  >
                    {/* Hover glow effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/5 to-white/0 opacity-0 group-hover/case:opacity-100 transition-opacity duration-500"></div>
                    
                    <div className="relative flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`p-2 rounded-lg bg-slate-700/50 ${pulse ? 'scale-105' : 'scale-100'} transition-transform duration-500`}>
                          <IconComponent className={`w-5 h-5 ${caseItem.color}`} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-gray-300 font-mono text-sm font-semibold">{caseItem.id}</span>
                            <span className="text-gray-600">•</span>
                            <span className="text-gray-300">{caseItem.name}</span>
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={`${caseItem.color} font-semibold text-xs tracking-wide`}>{caseItem.status}</span>
                            <div className={`w-16 h-1 bg-gray-800 rounded-full overflow-hidden`}>
                              <div className={`h-full bg-white transition-all duration-1000`} style={{width: `${scanProgress}%`}}></div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-white opacity-0 group-hover/case:opacity-100 transition-opacity duration-300 animate-pulse"></div>
                        <div className="text-white/50 opacity-0 group-hover/case:opacity-100 transition-opacity duration-300 text-xs">→</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Processing Pipeline */}
        <div className="relative">
          <div className="absolute top-1/2 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-600 to-transparent"></div>
          
          <div className="flex items-center justify-center gap-16 relative">
            {/* Unsolved */}
            <div className="relative group/icon">
              {activeIcon === 0 && (
                <>
                  <div className="absolute inset-0 rounded-full bg-white/10 animate-ping"></div>
                  <div className="absolute inset-0 rounded-full" style={{ background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)', animation: 'pulse-ring 2s ease-out infinite' }}></div>
                </>
              )}
              <div className={`relative bg-slate-900 p-8 rounded-full border-2 transition-all duration-700 ${activeIcon === 0 ? 'border-white shadow-lg shadow-white/30' : 'border-gray-700'}`}>
                <Fingerprint className={`w-14 h-14 transition-all duration-700 ${activeIcon === 0 ? 'text-white scale-110' : 'text-gray-600'}`} />
              </div>
              <div className={`text-center mt-4 font-semibold transition-colors duration-500 ${activeIcon === 0 ? 'text-white' : 'text-gray-500'}`}>
                Unsolved
              </div>
              <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-1 h-1 bg-white rounded-full opacity-0 group-hover/icon:opacity-100 transition-opacity"></div>
            </div>

            {/* AI CORE */}
            <div className="relative group/icon">
              {activeIcon === 1 && (
                <>
                  <div className="absolute inset-0 rounded-full bg-white/10 animate-ping"></div>
                  <div className="absolute inset-0 rounded-full" style={{ background: 'radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%)', animation: 'pulse-ring 2s ease-out infinite' }}></div>
                </>
              )}
              <div className={`relative bg-slate-900 p-8 rounded-full border-2 transition-all duration-700 ${activeIcon === 1 ? 'border-white shadow-lg shadow-white/30' : 'border-gray-700'}`}>
                <Brain className={`w-14 h-14 transition-all duration-700 ${activeIcon === 1 ? 'text-white scale-110' : 'text-gray-600'}`} />
              </div>
              <div className={`text-center mt-4 font-semibold transition-colors duration-500 ${activeIcon === 1 ? 'text-white' : 'text-gray-500'}`}>
                AI CORE
              </div>
            </div>

            {/* Ongoing */}
            <div className="relative group/icon">
              {activeIcon === 2 && (
                <>
                  <div className="absolute inset-0 rounded-full bg-white/10 animate-ping"></div>
                  <div className="absolute inset-0 rounded-full" style={{ background: 'radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%)', animation: 'pulse-ring 2s ease-out infinite' }}></div>
                </>
              )}
              <div className={`relative bg-slate-900 p-8 rounded-full border-2 transition-all duration-700 ${activeIcon === 2 ? 'border-white shadow-lg shadow-white/30' : 'border-gray-700'}`}>
                <Activity className={`w-14 h-14 transition-all duration-700 ${activeIcon === 2 ? 'text-white scale-110' : 'text-gray-600'}`} />
              </div>
              <div className={`text-center mt-4 font-semibold transition-colors duration-500 ${activeIcon === 2 ? 'text-white' : 'text-gray-500'}`}>
                Ongoing
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Corner HUD elements */}
      <div className="fixed top-8 right-8 w-24 h-24 border-t-2 border-r-2 border-gray-700 pointer-events-none"></div>
      <div className="fixed bottom-8 left-8 w-24 h-24 border-b-2 border-l-2 border-gray-700 pointer-events-none"></div>
      
      {/* Status indicator */}
      <div className="fixed bottom-8 right-8 flex items-center gap-2 text-xs font-mono text-gray-400">
        <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
        SYSTEM ONLINE
      </div>
    </div>
  );
}

export default App;