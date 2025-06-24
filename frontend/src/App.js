import React, { useState, useEffect } from 'react';
import ChatbotWidget from './ChatbotWidget';
import Visualizer from './Visualizer';
import './App.css';

function App() {
  const [socket, setSocket] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8080/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnectionStatus('connected');
      setSocket(ws);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnectionStatus('disconnected');
      setSocket(null);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('error');
    };

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  return (
    <div className="app-container">
      <div 
        className="connection-status" 
        data-status={connectionStatus}
      >
        Status: {connectionStatus}
      </div>
      <div className="components-container">
        <Visualizer socket={socket} />
        <ChatbotWidget socket={socket} />
      </div>
    </div>
  );
}

export default App;
