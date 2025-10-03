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
      <h4 className="text-lg font-semibold text-gray-300">Consult AI Detective</h4>
      <div className="h-64 bg-gray-900 p-2 rounded mt-2 border border-gray-600 overflow-y-auto flex flex-col space-y-2">
        {history.map((entry, index) => (
          <div key={index} className={`p-2 rounded-lg max-w-xs ${entry.from === 'user' ? 'bg-teal-800 self-end' : 'bg-gray-700 self-start'}`}>
            <p className="text-sm text-white">{entry.text}</p>
          </div>
        ))}
         {isLoading && <p className="text-gray-400 self-start">Detective is thinking...</p>}
      </div>
       <div className="flex mt-2">
        <input
          type="text"
          className="flex-grow bg-gray-900 text-white p-2 rounded-l border border-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
          placeholder="Ask a question about the case..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleAsk()}
        />
        <button
          onClick={handleAsk}
          disabled={isLoading}
          className="bg-teal-500 hover:bg-teal-400 text-white font-bold py-2 px-4 rounded-r"
        >
          Ask
        </button>
      </div>
      {error && <p className="text-red-500 mt-2">{error}</p>}
    </div>
  );
};

export default DetectiveChat;
