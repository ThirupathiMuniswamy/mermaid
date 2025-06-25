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
      <div className="visualizer-title">Visualizer</div>
      <div className="visualizer-flow">
        {steps.map((step, idx) => (
          <React.Fragment key={step.key}>
            <div className={`visualizer-node${currentStep === step.key ? ' active' : ''}`}>
              <span className="visualizer-icon">{step.icon}</span>
              {step.label}
            </div>
            {idx < steps.length - 1 && <div className="visualizer-edge" />}
          </React.Fragment>
        ))}
      </div>
      <div className="visualizer-log">
        <strong>Step Log</strong>
        <ul style={{ margin: 0, paddingLeft: 18 }}>
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
