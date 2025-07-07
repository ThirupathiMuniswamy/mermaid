import React from 'react';
import './App.css';

import robotIcon from './chatbot.png';

export default function OrchestrationTile() {
  return (
    <div className="agent-status-tile">
      <div className="agent-status-header">Orchestration</div>
      <div className="agent-status-content">

        <div className="agent-status-ace-col">
          <div className="agent-ace-icon"><img src={robotIcon} alt="Robot" style={{ width: 64, height: 64 }} /></div>
          <div className="agent-ace-label">Expert Orchestration AI Agent</div>
        </div>
      </div>
    </div>
  );
}
