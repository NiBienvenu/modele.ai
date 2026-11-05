import type { Theme } from "../hooks/useTheme";

interface Props {
  theme: Theme;
  onToggle: () => void;
}

export function ThemeToggle({ theme, onToggle }: Props) {
  const next = theme === "dark" ? "clair" : "sombre";
  return (
    <button type="button" className="theme-toggle" onClick={onToggle} aria-label={`Passer au thème ${next}`}>
      {theme === "dark" ? "☀" : "☾"}
    </button>
  );
}
