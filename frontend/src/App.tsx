// Main layout: sidebar + chat area. Assembles hooks and components,
// no business logic here.

import { useCallback, useEffect, useState } from "react";
import { Composer } from "./components/Composer";
import { MoonIcon, SidebarIcon, SunIcon } from "./components/Icons";
import { MessageList } from "./components/MessageList";
import { Sidebar } from "./components/Sidebar";
import { Welcome } from "./components/Welcome";
import { useChat } from "./hooks/useChat";
import { useConversations } from "./hooks/useConversations";
import { useTheme } from "./hooks/useTheme";

const MOBILE_QUERY = "(max-width: 860px)";
const isMobile = () => window.matchMedia?.(MOBILE_QUERY).matches ?? false;

export function App() {
  const { theme, toggle } = useTheme();
  const conversations = useConversations();
  const chat = useChat(conversations.refresh);
  const [sidebarOpen, setSidebarOpen] = useState(() => !isMobile());

  // On phones the sidebar is a drawer: close it after picking a conversation
  const closeOnMobile = () => isMobile() && setSidebarOpen(false);

  const selectConversation = (id: string) => {
    void chat.open(id);
    closeOnMobile();
  };

  const newChat = () => {
    void chat.open(null);
    closeOnMobile();
  };

  const removeConversation = useCallback(
    async (id: string) => {
      if (!window.confirm("Supprimer cette conversation ?")) return;
      await conversations.remove(id);
      if (id === chat.activeId) void chat.open(null);
    },
    [chat, conversations],
  );

  // Escape closes the drawer on phones
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && closeOnMobile();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const empty = chat.messages.length === 0;

  return (
    <div className={sidebarOpen ? "layout" : "layout sidebar-closed"}>
      <Sidebar
        open={sidebarOpen}
        conversations={conversations.conversations}
        activeId={chat.activeId}
        error={conversations.error}
        onNewChat={newChat}
        onSelect={selectConversation}
        onDelete={(id) => void removeConversation(id)}
        onClose={() => setSidebarOpen(false)}
      />
      {sidebarOpen && <div className="backdrop" onClick={() => setSidebarOpen(false)} aria-hidden="true" />}

      <main className="chat">
        <header className="topbar">
          {!sidebarOpen && (
            <button type="button" className="icon-button" onClick={() => setSidebarOpen(true)} aria-label="Ouvrir le panneau">
              <SidebarIcon />
            </button>
          )}
          <div className="topbar-spacer" />
          <button
            type="button"
            className="icon-button round"
            onClick={toggle}
            aria-label={theme === "dark" ? "Passer au thème clair" : "Passer au thème sombre"}
          >
            {theme === "dark" ? <SunIcon /> : <MoonIcon />}
          </button>
        </header>

        {chat.loadError && <p className="load-error" role="alert">{chat.loadError}</p>}

        {empty ? (
          <section className="chat-empty">
            <Welcome onPick={chat.send} disabled={chat.sending} />
            <Composer disabled={chat.sending} onSend={chat.send} autoFocus />
          </section>
        ) : (
          <>
            <section className="chat-scroll">
              <MessageList messages={chat.messages} />
            </section>
            <footer className="chat-footer">
              <Composer disabled={chat.sending} onSend={chat.send} />
              <p className="disclaimer">Les réponses peuvent contenir des erreurs. Vérifiez les textes officiels.</p>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}
