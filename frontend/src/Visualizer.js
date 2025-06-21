import React, { useEffect, useState } from 'react';
import './Visualizer.css';

const steps = [
  { key: 'received', label: 'Client', icon: '🧑‍💻' },
  { key: 'agent_invoked', label: 'AI Agent', icon: '🤖' },
  { key: 'tool_invoked', label: 'Payment Tool', icon: '💳' },
  { key: 'completed', label: 'Response', icon: '📤' },
];

function Visualizer({ wsUrl = 'ws://localhost:8080/ws' }) {
  const [currentStep, setCurrentStep] = useState(null);
  const [stepLog, setStepLog] = useState([]);

  useEffect(() => {
    const ws = new window.WebSocket(wsUrl);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.step) {
        setCurrentStep(data.step);
        setStepLog((prev) => [...prev, data]);
      }
    };
    ws.onclose = () => setCurrentStep(null);
    return () => ws.close();
  }, [wsUrl]);

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
