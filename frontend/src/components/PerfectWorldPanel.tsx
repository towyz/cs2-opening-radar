import { CloudDownload } from "lucide-react";
import { FormEvent, useState } from "react";
import type { PerfectWorldRecentResponse } from "../api/client";

interface PerfectWorldPanelProps {
  loading: boolean;
  onImport: (uid: string, steam64?: string) => Promise<PerfectWorldRecentResponse>;
}

export function PerfectWorldPanel({ loading, onImport }: PerfectWorldPanelProps) {
  const [targetSteam64, setTargetSteam64] = useState("");
  const [report, setReport] = useState<PerfectWorldRecentResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const steam64 = targetSteam64.trim();
    if (!steam64) {
      return;
    }
    setReport(null);
    try {
      setReport(await onImport(steam64, steam64));
    } catch {
      setReport(null);
    }
  }

  return (
    <form className="perfectworld-panel" onSubmit={handleSubmit}>
      <div className="perfectworld-title">
        <CloudDownload size={18} />
        <span>Perfect World dust2</span>
      </div>
      <input
        className="steam-input"
        placeholder="Target Steam64"
        value={targetSteam64}
        onChange={(event) => setTargetSteam64(event.target.value)}
      />
      <button className="primary-button" disabled={!targetSteam64.trim() || loading}>
        <CloudDownload size={18} />
        <span>{loading ? "Importing" : "Import recent 5"}</span>
      </button>
      {report ? <PerfectWorldImportReport report={report} /> : null}
    </form>
  );
}

function PerfectWorldImportReport({ report }: { report: PerfectWorldRecentResponse }) {
  const imported = report.imported.length;
  return (
    <div className="import-report">
      <p>
        Downloaded {imported} demo{imported === 1 ? "" : "s"} from Perfect World. Scanned {report.scanned}, saved{" "}
        {report.downloaded}.
      </p>
      {report.notice ? <p>{report.notice}</p> : null}
      {report.skipped.length > 0 ? (
        <ul>
          {report.skipped.slice(0, 3).map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
