// Light / dark theme. First visit follows the system setting,
// then the user's choice is remembered.

import { useEffect, useState } from "react";
import { readStored, writeStored } from "../lib/storage";

export type Theme = "light" | "dark";

const KEY = "theme";

function initialTheme(): Theme {
  const stored = readStored(KEY);
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(initialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme; // Read by styles.css
    writeStored(KEY, theme);
  }, [theme]);

  const toggle = () => setTheme((t) => (t === "dark" ? "light" : "dark"));
  return { theme, toggle };
}
