import React, { useEffect, useRef } from 'react';
import { AnalysisResult } from '../types/analysis';
import './MapViewer.css';

interface MapViewerProps {
  result: AnalysisResult;
  selectedRounds: Set<number>;
  showPath: boolean;
  showGrenades: boolean;
  grenadeFilter: string | null;
}

export default function MapViewer({
  result,
  selectedRounds,
  showPath,
  showGrenades,
  grenadeFilter,
}: MapViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size to match container
    const container = canvas.parentElement;
    if (container) {
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
    }

    // Draw placeholder - actual radar image would be loaded here
    drawPlaceholder(ctx, canvas.width, canvas.height);

    // Draw paths if enabled
    if (showPath && result.rounds) {
      drawPaths(
        ctx,
        result.rounds.filter((r) => selectedRounds.has(r.roundNumber)),
      );
    }

    // Draw grenades if enabled
    if (showGrenades && result.rounds) {
      drawGrenades(
        ctx,
        result.rounds.filter((r) => selectedRounds.has(r.roundNumber)),
        grenadeFilter,
      );
    }
  }, [result, selectedRounds, showPath, showGrenades, grenadeFilter]);

  return (
    <div className="map-viewer">
      <canvas ref={canvasRef} className="map-canvas" />
      <div className="map-info">
        <p>Radar visualization for {result.meta.map}</p>
      </div>
    </div>
  );
}

function drawPlaceholder(ctx: CanvasRenderingContext2D, width: number, height: number) {
  // Draw background
  ctx.fillStyle = '#f0f0f0';
  ctx.fillRect(0, 0, width, height);

  // Draw grid
  ctx.strokeStyle = '#ddd';
  ctx.lineWidth = 1;

  for (let x = 0; x < width; x += 50) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
  }

  for (let y = 0; y < height; y += 50) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }

  // Draw placeholder text
  ctx.fillStyle = '#999';
  ctx.font = '16px Arial';
  ctx.textAlign = 'center';
  ctx.fillText('de_dust2 Radar', width / 2, height / 2 - 10);
  ctx.font = '12px Arial';
  ctx.fillText('(Radar image not found)', width / 2, height / 2 + 15);
}

function drawPaths(ctx: CanvasRenderingContext2D, rounds: any[]) {
  rounds.forEach((round, idx) => {
    if (!round.path || round.path.length === 0) return;

    // Use different colors for different rounds
    const hue = (idx * 60) % 360;
    ctx.strokeStyle = `hsl(${hue}, 70%, 50%)`;
    ctx.lineWidth = 2;
    ctx.globalAlpha = 0.7;

    ctx.beginPath();
    round.path.forEach((point: any, i: number) => {
      if (i === 0) {
        ctx.moveTo(point.map.x, point.map.y);
      } else {
        ctx.lineTo(point.map.x, point.map.y);
      }
    });
    ctx.stroke();

    ctx.globalAlpha = 1;

    // Draw start point
    if (round.path.length > 0) {
      const start = round.path[0];
      ctx.fillStyle = `hsl(${hue}, 70%, 50%)`;
      ctx.beginPath();
      ctx.arc(start.map.x, start.map.y, 4, 0, Math.PI * 2);
      ctx.fill();
    }

    // Draw end point
    if (round.path.length > 1) {
      const end = round.path[round.path.length - 1];
      ctx.fillStyle = `hsl(${hue}, 70%, 30%)`;
      ctx.beginPath();
      ctx.arc(end.map.x, end.map.y, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  });
}

function drawGrenades(
  ctx: CanvasRenderingContext2D,
  rounds: any[],
  filter: string | null,
) {
  rounds.forEach((round) => {
    if (!round.grenades) return;

    round.grenades.forEach((grenade: any) => {
      if (filter && grenade.type !== filter) return;

      // Draw throw point
      ctx.fillStyle = getGrenadeColor(grenade.type);
      ctx.beginPath();
      ctx.arc(grenade.throwPosition.map.x, grenade.throwPosition.map.y, 3, 0, Math.PI * 2);
      ctx.fill();

      // Draw detonate point
      ctx.strokeStyle = getGrenadeColor(grenade.type);
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(grenade.detonatePosition.map.x, grenade.detonatePosition.map.y, 5, 0, Math.PI * 2);
      ctx.stroke();

      // Draw trajectory if available
      if (grenade.trajectory && grenade.trajectory.length > 1) {
        ctx.strokeStyle = getGrenadeColor(grenade.type);
        ctx.lineWidth = 1;
        ctx.globalAlpha = 0.5;
        ctx.beginPath();
        grenade.trajectory.forEach((point: any, i: number) => {
          if (i === 0) {
            ctx.moveTo(point.map.x, point.map.y);
          } else {
            ctx.lineTo(point.map.x, point.map.y);
          }
        });
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
    });
  });
}

function getGrenadeColor(type: string): string {
  const colors: Record<string, string> = {
    smoke: '#666',
    flash: '#ffc107',
    he: '#dc2626',
    molotov: '#ff6b6b',
    incendiary: '#ff9800',
  };
  return colors[type] || '#999';
}
