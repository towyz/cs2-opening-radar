import { Pause, Play, RotateCcw } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Filters } from "./FilterPanel";
import { GrenadeLayer } from "./GrenadeLayer";
import { PlaybackLayer } from "./PlaybackLayer";
import { TrajectoryLayer } from "./TrajectoryLayer";
import type { AnalysisResult, RoundAnalysis } from "../types/analysis";
import type { ViewMode } from "./FilterPanel";

const localRadarSrc = "/maps/de_dust2/radar.png";
const simpleRadarDust2Src =
  "https://cdn.prod.website-files.com/5d5ab0de3f2789196e87264e/5f9999ea1057522149823f0a_de_dust2_radar_Pano0Pat1Buy1Spec0.png";

export function MapViewer({
  results,
  filters,
  viewMode
}: {
  results: AnalysisResult[];
  filters: Filters;
  viewMode: ViewMode;
}) {
  const rounds = useMemo(
    () =>
      results.flatMap((result, demoIndex) => {
        const selectedDemo = filters.demoIndices.includes(demoIndex);
        if (!selectedDemo) return [];
        return result.rounds
          .filter((round) => {
            if (!round.valid) return false;
            if (filters.side !== "ALL" && round.side !== filters.side) return false;
            return true;
          })
          .map((round) => ({
            ...round,
            roundKey: roundKey(demoIndex, round.roundNumber),
            demoIndex,
            demoLabel: demoLabel(result, demoIndex)
          }));
      }),
    [filters.demoIndices, filters.side, results]
  );
  const overviewRounds = useMemo(
    () =>
      rounds.filter((round) => filters.roundKey === "ALL" || round.roundKey === filters.roundKey),
    [filters.roundKey, rounds]
  );
  const playbackRounds = useMemo(
    () =>
      rounds.filter((round) => filters.playbackRoundKeys.includes(round.roundKey)),
    [filters.playbackRoundKeys, rounds]
  );
  const duration = Math.min(Math.max(...results.map((result) => result.meta.windowSeconds), 30), 30);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [radarSrc, setRadarSrc] = useState(localRadarSrc);
  const lastFrameRef = useRef<number | null>(null);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    setCurrentTime(0);
    setIsPlaying(false);
  }, [filters.playbackRoundKeys, results, viewMode]);

  useEffect(() => {
    if (!isPlaying || viewMode !== "playback" || playbackRounds.length === 0) {
      lastFrameRef.current = null;
      if (animationRef.current !== null) {
        window.cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
      return;
    }

    const step = (timestamp: number) => {
      if (lastFrameRef.current === null) {
        lastFrameRef.current = timestamp;
      }
      const deltaSeconds = (timestamp - lastFrameRef.current) / 1000;
      lastFrameRef.current = timestamp;
      setCurrentTime((time) => {
        const next = Math.min(duration, time + deltaSeconds);
        if (next >= duration) {
          setIsPlaying(false);
        }
        return next;
      });
      animationRef.current = window.requestAnimationFrame(step);
    };

    animationRef.current = window.requestAnimationFrame(step);
    return () => {
      if (animationRef.current !== null) {
        window.cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
    };
  }, [duration, isPlaying, playbackRounds.length, viewMode]);

  const showPlayback = viewMode === "playback";
  const hasPlaybackRounds = playbackRounds.length > 0;

  return (
    <section className="map-stage">
      <div className="radar-frame">
        <img
          className="radar-image"
          src={radarSrc}
          alt="de_dust2 radar"
          onError={(event) => {
            if (radarSrc === localRadarSrc) {
              setRadarSrc(simpleRadarDust2Src);
            } else {
              event.currentTarget.classList.add("missing");
            }
          }}
        />
        <svg className="radar-overlay" viewBox="0 0 1024 1024" role="img">
          {showPlayback && hasPlaybackRounds ? (
            <PlaybackLayer
              rounds={playbackRounds}
              currentTime={currentTime}
              grenadeType={filters.grenadeType}
              showPath={filters.showPath}
              showGrenades={filters.showGrenades}
            />
          ) : (
            <>
              {filters.showPath ? <TrajectoryLayer rounds={overviewRounds} /> : null}
              {filters.showGrenades ? (
                <GrenadeLayer rounds={overviewRounds} grenadeType={filters.grenadeType} />
              ) : null}
            </>
          )}
        </svg>
        {results.length === 0 ? <div className="empty-state">Upload a Dust2 demo to render opening paths.</div> : null}
        {results.length > 0 && showPlayback && !hasPlaybackRounds ? (
          <div className="empty-state">Select one or more valid rounds to start playback.</div>
        ) : null}
      </div>
      {results.length > 0 && showPlayback ? (
        <div className="playback-controls">
          <button
            type="button"
            className="icon-button"
            disabled={!hasPlaybackRounds}
            title="Restart"
            onClick={() => {
              setCurrentTime(0);
              setIsPlaying(false);
            }}
          >
            <RotateCcw size={17} />
          </button>
          <button
            type="button"
            className="icon-button playback-play"
            disabled={!hasPlaybackRounds}
            title={isPlaying ? "Pause" : "Play"}
            onClick={() => {
              if (currentTime >= duration) {
                setCurrentTime(0);
              }
              setIsPlaying((playing) => !playing);
            }}
          >
            {isPlaying ? <Pause size={18} /> : <Play size={18} />}
          </button>
          <input
            type="range"
            min="0"
            max={duration}
            step="0.05"
            disabled={!hasPlaybackRounds}
            value={currentTime}
            aria-label="Playback time"
            onChange={(event) => {
              setIsPlaying(false);
              setCurrentTime(Number(event.target.value));
            }}
          />
          <span className="playback-time">{currentTime.toFixed(1)}s / {duration.toFixed(0)}s</span>
        </div>
      ) : null}
    </section>
  );
}

export type DisplayRound = RoundAnalysis & {
  roundKey: string;
  demoIndex: number;
  demoLabel: string;
};

function demoLabel(result: AnalysisResult, index: number): string {
  return `D${index + 1} ${result.meta.demoFile}`;
}

function roundKey(demoIndex: number, roundNumber: number): string {
  return `${demoIndex}:${roundNumber}`;
}
