// Text area + Send button. Ctrl/Cmd + Enter also sends.

import { useState, type FormEvent, type KeyboardEvent } from "react";

interface Props {
  disabled: boolean;
  onSubmit: (prompt: string) => void;
}

export function PromptForm({ disabled, onSubmit }: Props) {
  const [prompt, setPrompt] = useState("");
  const canSend = !disabled && prompt.trim().length > 0;

  const submit = (event?: FormEvent) => {
    event?.preventDefault();
    if (canSend) onSubmit(prompt.trim());
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) submit();
  };

  return (
    <form className="prompt-form" onSubmit={submit}>
      <label htmlFor="prompt" className="visually-hidden">
        Votre question
      </label>
      <textarea
        id="prompt"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="Posez une question sur vos documents…"
        rows={4}
      />
      <div className="prompt-actions">
        <span className="hint">Ctrl + Entrée pour envoyer</span>
        <button type="submit" disabled={!canSend}>
          {disabled ? "En cours…" : "Envoyer"}
        </button>
      </div>
    </form>
  );
}
