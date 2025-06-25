import React, { useEffect, useState } from 'react';
import './Visualizer.css';

const steps = [
  { key: 'received', label: 'Client', icon: '🧑‍💻' },
  { key: 'agent_invoked', label: 'AI Agent', icon: '🤖' },
  { key: 'tool_invoked', label: 'Payment Tool', icon: '💳' },
  { key: 'completed', label: 'Response', icon: '📤' },
];

function Visualizer({ socket }) {
  const [currentStep, setCurrentStep] = useState('received');
  const [stepLog, setStepLog] = useState([
    { step: 'received', detail: 'Waiting for message...' }
  ]);

  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Visualizer received:', data); // Debug log
        if (data.target === 'visualizer' && data.step) {
          setCurrentStep(data.step);
          setStepLog(prev => [...prev, data]);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    socket.addEventListener('message', handleMessage);
    
    return () => {
      socket.removeEventListener('message', handleMessage);
    };
  }, [socket]);

  return (
    <div className="visualizer-bg">
      <div className="visualizer-flow-vertical">
        <div className="visualizer-arrow visualizer-arrow-origin" title="Request to Agent">↓</div>
        {steps.map((step, idx) => (
          <React.Fragment key={step.key}>
            <div className={`visualizer-node${currentStep === step.key ? ' active' : ''}`}>
              <span className="visualizer-icon">{step.icon}</span>
              {step.label}
            </div>
            {idx < steps.length - 1 && (
              <div className="visualizer-arrow">↓</div>
            )}
          </React.Fragment>
        ))}
        <div className="visualizer-arrow visualizer-arrow-origin" title="Response to Origin">↑</div>
      </div>
      <div className="visualizer-log-card">
        <div className="visualizer-log-title">Step Log</div>
        <ul className="visualizer-log-list">
          {stepLog.map((log, idx) => (
            <li key={idx}>
              <strong>{log.step}</strong>: {log.detail} {log.tool ? `(Tool: ${log.tool})` : ''}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default Visualizer;
