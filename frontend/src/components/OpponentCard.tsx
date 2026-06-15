import React from 'react';
import { AnalysisResult } from '../types/analysis';
import './OpponentCard.css';

interface OpponentCardProps {
  result: AnalysisResult;
}

export default function OpponentCard({ result }: OpponentCardProps) {
  const { meta, summary } = result;

  return (
    <div className="opponent-card">
      <div className="card-header">
        <h3>{meta.targetName}</h3>
      </div>

      <div className="card-body">
        <div className="stat-row">
          <span className="label">Steam64:</span>
          <code className="value">{meta.targetSteam64}</code>
        </div>

        <div className="stat-row">
          <span className="label">Map:</span>
          <span className="value">{meta.map}</span>
        </div>

        <div className="stat-row">
          <span className="label">Analysis Window:</span>
          <span className="value">{meta.windowSeconds}s after freeze</span>
        </div>

        <div className="divider"></div>

        <div className="stat-row">
          <span className="label">Total Rounds:</span>
          <span className="value">{summary.totalRounds}</span>
        </div>

        <div className="stat-row">
          <span className="label">Valid Rounds:</span>
          <span className="value">{summary.validRounds}</span>
        </div>

        <div className="stat-row">
          <span className="label">T Rounds:</span>
          <span className="value">{summary.tRounds}</span>
        </div>

        <div className="stat-row">
          <span className="label">CT Rounds:</span>
          <span className="value">{summary.ctRounds}</span>
        </div>

        <div className="divider"></div>

        <h4>Grenade Stats</h4>
        <div className="grenade-stats">
          {summary.grenades.smoke > 0 && (
            <div className="grenade-stat">
              <span className="grenade-type smoke">Smoke</span>
              <span className="grenade-count">{summary.grenades.smoke}</span>
            </div>
          )}
          {summary.grenades.flash > 0 && (
            <div className="grenade-stat">
              <span className="grenade-type flash">Flash</span>
              <span className="grenade-count">{summary.grenades.flash}</span>
            </div>
          )}
          {summary.grenades.he > 0 && (
            <div className="grenade-stat">
              <span className="grenade-type he">HE</span>
              <span className="grenade-count">{summary.grenades.he}</span>
            </div>
          )}
          {summary.grenades.molotov > 0 && (
            <div className="grenade-stat">
              <span className="grenade-type molotov">Molotov</span>
              <span className="grenade-count">{summary.grenades.molotov}</span>
            </div>
          )}
          {summary.grenades.incendiary > 0 && (
            <div className="grenade-stat">
              <span className="grenade-type incendiary">Incendiary</span>
              <span className="grenade-count">{summary.grenades.incendiary}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
