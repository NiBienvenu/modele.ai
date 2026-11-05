// Message box: grows with the text. Enter sends, Shift + Enter = new line.

import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { SendIcon } from "./Icons";

interface Props {
  disabled: boolean;
  onSend: (text: string) => void;
  autoFocus?: boolean;
}

const MAX_HEIGHT_PX = 200;

export function Composer({ disabled, onSend, autoFocus }: Props) {
  const [text, setText] = useState("");
  const areaRef = useRef<HTMLTextAreaElement>(null);
  const canSend = !disabled && text.trim().length > 0;

  // Auto-grow the text area up to MAX_HEIGHT_PX
  useEffect(() => {
    const area = areaRef.current;
    if (!area) return;
    area.style.height = "auto";
    area.style.height = `${Math.min(area.scrollHeight, MAX_HEIGHT_PX)}px`;
  }, [text]);

  const submit = (event?: FormEvent) => {
    event?.preventDefault();
    if (!canSend) return;
    onSend(text.trim());
    setText("");
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <form className="composer" onSubmit={submit}>
      <textarea
        ref={areaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="Posez une question sur vos documents…"
        rows={1}
        autoFocus={autoFocus}
        aria-label="Votre message"
      />
      <div className="composer-bar">
        <span className="composer-hint">Entrée pour envoyer · Maj + Entrée pour aller à la ligne</span>
        <button type="submit" className="send-button" disabled={!canSend} aria-label="Envoyer">
          <SendIcon width={18} height={18} strokeWidth={2.2} />
        </button>
      </div>
    </form>
  );
}
