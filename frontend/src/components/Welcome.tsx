// Shown for a new conversation: greeting + a few example questions.

import { LogoMark } from "./Icons";

const SUGGESTIONS = [
  "Résume ce décret en 5 points",
  "Quelle est la différence entre une loi et un décret ?",
  "Explique ce document technique simplement",
];

interface Props {
  onPick: (text: string) => void;
  disabled: boolean;
}

export function Welcome({ onPick, disabled }: Props) {
  return (
    <div className="welcome">
      <span className="welcome-mark">
        <LogoMark width={30} height={30} />
      </span>
      <p className="welcome-hello">Bonjour 👋</p>
      <h1 className="welcome-title">Que voulez-vous savoir sur vos documents ?</h1>
      <div className="suggestions">
        {SUGGESTIONS.map((text) => (
          <button key={text} type="button" className="suggestion" disabled={disabled} onClick={() => onPick(text)}>
            {text}
          </button>
        ))}
      </div>
    </div>
  );
}
