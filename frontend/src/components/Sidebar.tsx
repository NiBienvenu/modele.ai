// Left panel: new conversation, search, list of conversations.

import { useMemo, useState } from "react";
import type { ConversationSummary } from "../api/types";
import { ChatIcon, LogoMark, PlusIcon, SearchIcon, SidebarIcon, TrashIcon } from "./Icons";

interface Props {
  open: boolean;
  conversations: ConversationSummary[];
  activeId: string | null;
  error: string | null;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onClose: () => void;
}

export function Sidebar({ open, conversations, activeId, error, onNewChat, onSelect, onDelete, onClose }: Props) {
  const [search, setSearch] = useState("");

  const visible = useMemo(() => {
    const query = search.trim().toLowerCase();
    return query ? conversations.filter((c) => c.title.toLowerCase().includes(query)) : conversations;
  }, [conversations, search]);

  return (
    <aside className={open ? "sidebar open" : "sidebar"} aria-label="Conversations">
      <div className="sidebar-top">
        <div className="brand">
          <span className="brand-mark">
            <LogoMark width={18} height={18} />
          </span>
          <span className="brand-name">DocIA</span>
        </div>
        <button type="button" className="icon-button" onClick={onClose} aria-label="Fermer le panneau">
          <SidebarIcon />
        </button>
      </div>

      <button type="button" className="new-chat" onClick={onNewChat}>
        <PlusIcon /> Nouvelle conversation
      </button>

      <label className="search">
        <SearchIcon />
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Rechercher…"
          aria-label="Rechercher une conversation"
        />
      </label>

      <p className="sidebar-label">Conversations</p>
      <nav className="conversation-list">
        {error && <p className="sidebar-empty">{error}</p>}
        {!error && visible.length === 0 && (
          <p className="sidebar-empty">{search ? "Aucun résultat" : "Aucune conversation"}</p>
        )}
        {visible.map((conversation) => (
          <div key={conversation.id} className={conversation.id === activeId ? "conversation active" : "conversation"}>
            <button type="button" className="conversation-open" onClick={() => onSelect(conversation.id)}>
              <ChatIcon width={16} height={16} />
              <span className="conversation-title">{conversation.title}</span>
            </button>
            <button
              type="button"
              className="conversation-delete"
              onClick={() => onDelete(conversation.id)}
              aria-label={`Supprimer « ${conversation.title} »`}
            >
              <TrashIcon width={15} height={15} />
            </button>
          </div>
        ))}
      </nav>
    </aside>
  );
}
