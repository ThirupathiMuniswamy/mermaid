import React, { useState, useEffect } from 'react';
import ChatbotWidget from './ChatbotWidget';
import ChatbotHttpWidget from './ChatbotHttpWidget';
import Visualizer from './Visualizer';
import './App.css';
import AgentStatusTile from './AgentStatusTile';
import OrchestrationTile from './OrchestrationTile';
import ToolsAgentsTile from './ToolsAgentsTile';

function App() {
  const [socket, setSocket] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [agentStep, setAgentStep] = useState('verify');
  const [insightsResponse, setInsightsResponse] = useState('');

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
    <div className="app-bg">

      <div className="main-split">
        <div className="agent-panel" style={{ width: '60%' }}>
          <div className="panel-header">Agent View</div>
          <br/>
          <br/>
          <div className="section card">
            <AgentStatusTile currentStep={agentStep} insightsResponse={insightsResponse} />
          </div>
          <div className="section card">
            <OrchestrationTile />
          </div>
          <div className="section card">
            <ToolsAgentsTile />
          </div>
        </div>
        <div className="customer-panel" style={{ width: '40%' }}>
          <div className="panel-header">Customer View</div>
          <ChatbotWidget socket={socket} />
            <div style={{marginTop: 24}} />
            <ChatbotHttpWidget agentStep={agentStep} setAgentStep={setAgentStep} setInsightsResponse={setInsightsResponse} />
        </div>
        
      </div>
    </div>
  );
}

export default App;
