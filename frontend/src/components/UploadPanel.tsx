import { Play, Upload } from "lucide-react";
import { FormEvent, useState } from "react";

interface UploadPanelProps {
  loading: boolean;
  error: string | null;
  onImport: (demo: File) => void;
}

export function UploadPanel({ loading, error, onImport }: UploadPanelProps) {
  const [demo, setDemo] = useState<File | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (demo) {
      onImport(demo);
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
      <button className="primary-button" disabled={!demo || loading}>
        <Play size={18} />
        <span>{loading ? "Reading" : "Add demo"}</span>
      </button>
      {error ? <p className="inline-error">{error}</p> : null}
    </form>
  );
}
