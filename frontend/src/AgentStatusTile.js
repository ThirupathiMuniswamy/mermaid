import React from 'react';
import './App.css';
import robotIcon from './chatbot.png';

export default function AgentStatusTile() {
  return (
    <div className="agent-status-tile">
      <div className="agent-status-header">Customer Engagement AI Agent</div>
      <div className="agent-status-content">
        <div className="agent-status-steps-col">
          <button className="agent-step-btn agent-step-btn-active">Verify</button>
          <button className="agent-step-btn">Decide</button>
        </div>
        <div className="agent-status-ace-col">
          <div className="agent-ace-icon"><img src={robotIcon} alt="Robot" style={{ width: 64, height: 64 }} /></div>
          <div className="agent-ace-label">ACE<br/>AI Agent</div>
        </div>
      </div>
      <div className="agent-status-outcome-row">
        <div className="agent-status-steps-last-row-col">
        <span className="agent-status-outcome-label">Outcome</span>
        </div>
        <div className="agent-status-steps-last-row-col">
        <button className="agent-step-btn agent-step-btn-insights">Insights</button>
        </div>
      </div>
    </div>
  );
}
