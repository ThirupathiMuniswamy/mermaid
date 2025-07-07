import React, { useState, useRef, useEffect } from 'react';
import './ChatbotWidget.css';
// Use a simple UUID generator if uuid package is not available
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}


export default function ChatbotHttpWidget({ agentStep, setAgentStep, setInsightsResponse }) {
  const sessionIdRef = useRef(uuidv4());
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hey, I am your assistant! How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSend = async () => {
    const message = input.trim();
    if (!message) return;
    setMessages(prev => [...prev, { sender: 'user', text: message }]);
    setInput('');
    setAgentStep('verify'); // Step 1: Verify intent
    setInsightsResponse(''); // Clear previous insights
    setLoading(true);
    setTimeout(() => setAgentStep('decide'), 100); // Simulate intent/decision step
    try {
      const res = await fetch('http://localhost:5001/api/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, sessionId: sessionIdRef.current })
      });
      const data = await res.json();
      setTimeout(() => {
        setAgentStep('insights'); // Step 3: Insights after agent response
        setInsightsResponse(data.reply);
        setMessages(prev => [...prev, { sender: 'bot', text: data.reply }]);
      }, 1000); // 1 second delay
    } catch (err) {
      setAgentStep('insights');
      setInsightsResponse('Error: Could not reach server.');
      setMessages(prev => [...prev, { sender: 'system', text: 'Error: Could not reach server.' }]);
    }
    setLoading(false);
  };

  return (
    <div className="chatbot-window">
      <div className="chatbot-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`chatbot-msg ${msg.sender}`}>{msg.text}</div>
        ))}
        <div ref={chatEndRef} />
      </div>
      <div className="chatbot-input-row">
        <input
          className="chatbot-input"
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Message..."
          disabled={loading}
        />
        <button className="chatbot-send-btn" onClick={handleSend} disabled={loading || !input.trim()}>
          {loading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
}
