// Main page: assembles the components. No business logic here.

import { HistoryList } from "./components/HistoryList";
import { PromptForm } from "./components/PromptForm";
import { ResponsePanel } from "./components/ResponsePanel";
import { ThemeToggle } from "./components/ThemeToggle";
import { useHistory } from "./hooks/useHistory";
import { useQuestion } from "./hooks/useQuestion";
import { useTheme } from "./hooks/useTheme";

export function App() {
  const { theme, toggle } = useTheme();
  const history = useHistory();
  const question = useQuestion(history.add);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Assistant documentaire</h1>
        <ThemeToggle theme={theme} onToggle={toggle} />
      </header>
      <main>
        <PromptForm disabled={question.loading} onSubmit={question.ask} />
        <ResponsePanel loading={question.loading} result={question.result} error={question.error} />
        <HistoryList entries={history.entries} onClear={history.clear} />
      </main>
    </div>
  );
}
