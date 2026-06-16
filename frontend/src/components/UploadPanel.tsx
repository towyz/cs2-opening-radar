import { Play, Upload } from "lucide-react";
import { FormEvent, useState } from "react";

interface UploadPanelProps {
  loading: boolean;
  error: string | null;
  onAnalyze: (demo: File, steam64: string) => void;
}

export function UploadPanel({ loading, error, onAnalyze }: UploadPanelProps) {
  const [demo, setDemo] = useState<File | null>(null);
  const [steam64, setSteam64] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (demo && steam64.trim()) {
      onAnalyze(demo, steam64.trim());
    }
  }

  return (
    <form className="upload-panel" onSubmit={handleSubmit}>
      <label className="file-control">
        <Upload size={18} />
        <span>{demo ? demo.name : "Choose .dem"}</span>
        <input
          type="file"
          accept=".dem"
          onChange={(event) => setDemo(event.target.files?.[0] ?? null)}
        />
      </label>
      <input
        className="steam-input"
        placeholder="Steam64"
        value={steam64}
        onChange={(event) => setSteam64(event.target.value)}
      />
      <button className="primary-button" disabled={!demo || !steam64.trim() || loading}>
        <Play size={18} />
        <span>{loading ? "Parsing" : "Analyze"}</span>
      </button>
      {error ? <p className="inline-error">{error}</p> : null}
    </form>
  );
}

