import React, { useState } from 'react';
import axios from 'axios';

const DetectiveChat = ({ caseId }) => {
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAsk = async () => {
    if (!question) return;

    setIsLoading(true);
    setError('');
    const userQuestion = question;
    setQuestion(''); // Clear input immediately

    try {
      const response = await axios.post(
        `http://localhost:8000/cases/${caseId}/ask`,
        { question: userQuestion }
      );
      
      // Add both the question and answer to the chat history
      setHistory(prev => [
        ...prev,
        { from: 'user', text: userQuestion },
        { from: 'ai', text: response.data.answer }
      ]);

    } catch (err) {
      setError('Failed to get a response from the detective agent.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mt-4">
      <h4 className="text-lg font-semibold text-white">Consult AI Detective</h4>
      <div className="h-64 bg-slate-900/80 backdrop-blur-xl p-2 rounded mt-2 border border-gray-700 overflow-y-auto flex flex-col space-y-2">
        {history.map((entry, index) => (
          <div key={index} className={`p-2 rounded-lg max-w-xs ${entry.from === 'user' ? 'bg-white text-black self-end' : 'bg-slate-800/50 self-start border border-gray-700'}`}>
            <p className="text-sm">{entry.text}</p>
          </div>
        ))}
         {isLoading && <p className="text-gray-400 self-start">Detective is thinking...</p>}
      </div>
       <div className="flex mt-2">
        <input
          type="text"
          className="flex-grow bg-slate-900/80 backdrop-blur-xl text-white p-2 rounded-l border border-gray-700 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-white/50"
          placeholder="Ask a question about the case..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleAsk()}
        />
        <button
          onClick={handleAsk}
          disabled={isLoading}
          className="bg-white text-black hover:bg-gray-200 font-bold py-2 px-4 rounded-r transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Ask
        </button>
      </div>
      {error && <p className="text-red-400 mt-2">{error}</p>}
    </div>
  );
};

export default DetectiveChat;
