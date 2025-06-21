import React, { useState, useRef, useEffect } from 'react';
import './ChatbotWidget.css';

const WS_URL = 'ws://localhost:8080/ws';

function ChatbotWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hey, I am your assistant! How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [wsReady, setWsReady] = useState(false);
  const ws = useRef(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (open && !ws.current) {
      ws.current = new window.WebSocket(WS_URL);
      ws.current.onopen = () => {
        setWsReady(true);
        console.log('WebSocket connected');
      };
      ws.current.onclose = () => {
        setWsReady(false);
        console.log('WebSocket closed');
      };
      ws.current.onerror = (err) => {
        setWsReady(false);
        console.error('WebSocket error:', err);
      };
      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setMessages((prev) => [...prev, { sender: 'bot', text: data.message || JSON.stringify(data) }]);
      };
    }
    return () => {
      if (ws.current) {
        ws.current.close();
        ws.current = null;
        setWsReady(false);
      }
    };
    // eslint-disable-next-line
  }, [open]);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, open]);

  const handleSend = () => {
    if (!input.trim()) return;
    if (ws.current && ws.current.readyState === window.WebSocket.OPEN) {
      ws.current.send(input);
      setMessages((prev) => [...prev, { sender: 'user', text: input }]);
      setInput('');
    } else {
      setMessages((prev) => [...prev, { sender: 'user', text: input }]);
      setInput('');
      console.warn('WebSocket not ready, message not sent to backend');
    }
  };

  return (
    <div>
      <div className={`chatbot-fab${open ? ' open' : ''}`} onClick={() => setOpen((o) => !o)}>
        <span role="img" aria-label="chat">💬</span>
      </div>
      {open && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <span>Chatbot</span>
            <button className="chatbot-close" onClick={() => setOpen(false)}>×</button>
          </div>
          <div className="chatbot-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`chatbot-msg ${msg.sender}`}>{msg.text}</div>
            ))}
            <div ref={chatEndRef} />
          </div>
          <div className="chatbot-input-row">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="Type a message..."
            />
            <button onClick={handleSend} disabled={open && !wsReady}>Send</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatbotWidget;
