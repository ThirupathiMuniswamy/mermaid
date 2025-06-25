import React, { useState, useRef, useEffect } from 'react';
import './ChatbotWidget.css';

function ChatbotWidget({ socket }) {

  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hey, I am your assistant! How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [wsReady, setWsReady] = useState(false);
  const chatEndRef = useRef(null);

  // Handle WebSocket messages
  useEffect(() => {
    if (!socket) return;

    // Always show chat window as a panel
    // No open/close logic needed

    const handleMessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Chatbot received:', data); // Debug log
        if (data.target === 'chatbot') {
          setMessages(prev => [
            ...prev, 
            { 
              sender: 'bot', 
              text: data.message || data.detail || JSON.stringify(data) 
            }
          ]);
        }
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };

    const handleOpen = () => {
      console.log('Chatbot: WebSocket connected');
      setWsReady(true);
    };

    const handleClose = () => {
      console.log('Chatbot: WebSocket disconnected');
      setWsReady(false);
    };

    const handleError = (error) => {
      console.error('Chatbot WebSocket error:', error);
      setWsReady(false);
    };

    socket.addEventListener('message', handleMessage);
    socket.addEventListener('open', handleOpen);
    socket.addEventListener('close', handleClose);
    socket.addEventListener('error', handleError);

    return () => {
      socket.removeEventListener('message', handleMessage);
      socket.removeEventListener('open', handleOpen);
      socket.removeEventListener('close', handleClose);
      socket.removeEventListener('error', handleError);
    };
  }, [socket]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSend = () => {
    const message = input.trim();
    if (!message) return;
    
    // Add user message to chat
    setMessages(prev => [...prev, { sender: 'user', text: message }]);
    setInput('');

    // Send message through WebSocket if available
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(message);
    } else {
      console.warn('WebSocket not ready, message not sent to backend');
      // Add a warning message to chat
      setMessages(prev => [
        ...prev, 
        { 
          sender: 'system', 
          text: 'Warning: Could not send message. Please check your connection.' 
        }
      ]);
    }
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
        />
        <button className="chatbot-send-btn" onClick={handleSend} disabled={!wsReady}>Send</button>
      </div>
    </div>
  );
}

export default ChatbotWidget;
