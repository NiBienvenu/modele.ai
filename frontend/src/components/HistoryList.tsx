// Past questions of this browser, newest first. Click to expand.

import type { HistoryEntry } from "../hooks/useHistory";
import { Stats } from "./Stats";

interface Props {
  entries: HistoryEntry[];
  onClear: () => void;
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });

export function HistoryList({ entries, onClear }: Props) {
  if (entries.length === 0) return null;
  return (
    <section className="history">
      <header className="history-header">
        <h2>Historique</h2>
        <button type="button" className="link-button" onClick={onClear}>
          Effacer
        </button>
      </header>
      <ul>
        {entries.map((entry) => (
          <li key={entry.id}>
            <details>
              <summary>
                <span className="history-prompt">{entry.prompt}</span>
                <span className="history-date">{formatDate(entry.date)}</span>
              </summary>
              <p className={entry.failed ? "response-text error-text" : "response-text"}>{entry.response}</p>
              <Stats tokens={entry.tokens} elapsedTime={entry.elapsedTime} />
            </details>
          </li>
        ))}
      </ul>
    </section>
  );
}
