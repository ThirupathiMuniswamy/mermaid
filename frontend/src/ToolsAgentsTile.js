import React from 'react';
import './App.css';

import robotIcon from './chatbot.png';

const tools = [
  {
    label: ['Customer Competitiveness Monitoring'],
  },
  {
    label: ['Customer Acquisition & Marketing'],
  },
  {
    label: ['Customer Competitiveness Monitoring'],
  },
  {
    label: ['Pricing & Placement'],
  },
  {
    label: ['Customer Circle of Protection'],
  },
  {
    label: ['Tasks'],
  },
];



export default function ToolsAgentsTile() {
  return (
    <div className="tools-agents-tile">
      <div className="tools-agents-header">Tools / Experts / Agents</div>
      <div className="tools-agents-list">
        {tools.map((tool, idx) => (
          <div className="tools-agent-card" key={idx}>
            <img src={robotIcon} alt="Robot" style={{ width: 64, height: 64 }} />
            <div className="tools-agent-label">
              {tool.label.map((line, i) => (
                <div key={i}>{line}</div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
