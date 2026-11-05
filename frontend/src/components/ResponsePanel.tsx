// Shows the current answer: waiting state, text, stats or error.

import type { ResponseOut } from "../api/types";
import { Stats } from "./Stats";

interface Props {
  loading: boolean;
  result: ResponseOut | null;
  error: string | null;
}

const STATUS_LABELS = {
  pending: "En file d'attente…",
  processing: "Le modèle rédige la réponse…",
} as const;

export function ResponsePanel({ loading, result, error }: Props) {
  if (error) return <section className="panel error" role="alert">{error}</section>;
  if (!loading && !result) return null;

  if (!result || result.status === "pending" || result.status === "processing") {
    const label = result && (result.status === "pending" || result.status === "processing")
      ? STATUS_LABELS[result.status]
      : "Envoi…";
    return (
      <section className="panel waiting" aria-live="polite">
        <span className="spinner" aria-hidden="true" /> {label}
      </section>
    );
  }

  if (result.status === "failed") {
    return <section className="panel error" role="alert">La génération a échoué : {result.error}</section>;
  }

  return (
    <section className="panel" aria-live="polite">
      <p className="response-text">{result.response}</p>
      <Stats tokens={result.tokens} elapsedTime={result.elapsed_time} />
    </section>
  );
}
