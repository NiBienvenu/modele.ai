// The messages of the open conversation, scrolled to the latest one.

import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../hooks/useChat";
import { CheckIcon, CopyIcon, LogoMark } from "./Icons";

interface Props {
  messages: ChatMessage[];
}

export function MessageList({ messages }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  return (
    <div className="messages" aria-live="polite">
      {messages.map((message) =>
        message.role === "user" ? (
          <div key={message.id} className="message user">
            <div className="bubble">{message.content}</div>
          </div>
        ) : (
          <AssistantMessage key={message.id} message={message} />
        ),
      )}
      <div ref={endRef} />
    </div>
  );
}

function AssistantMessage({ message }: { message: ChatMessage }) {
  return (
    <div className="message assistant">
      <span className="avatar">
        <LogoMark width={16} height={16} />
      </span>
      <div className="assistant-body">
        {message.pending ? (
          <TypingDots />
        ) : (
          <>
            <div className={message.failed ? "assistant-text failed" : "assistant-text"}>
              {message.failed ? `La génération a échoué : ${message.content}` : message.content}
            </div>
            {!message.failed && <MessageMeta message={message} />}
          </>
        )}
      </div>
    </div>
  );
}

function MessageMeta({ message }: { message: ChatMessage }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard not allowed (non-HTTPS page): nothing to do
    }
  };

  return (
    <div className="message-meta">
      <button type="button" className="meta-button" onClick={copy} aria-label="Copier la réponse">
        {copied ? <CheckIcon width={15} height={15} /> : <CopyIcon width={15} height={15} />}
      </button>
      {message.elapsed_time !== null && <span>{message.elapsed_time.toFixed(2)} s</span>}
      {message.tokens !== null && <span>{message.tokens} tokens</span>}
    </div>
  );
}

function TypingDots() {
  return (
    <div className="typing" aria-label="Le modèle rédige la réponse">
      <span />
      <span />
      <span />
    </div>
  );
}
