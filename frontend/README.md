# frontend/

Interface web React + Vite + TypeScript. Ne parle qu'aux deux routes REST, aucune logique métier.

## Lancer en développement

```bash
cd frontend
npm install
npm run dev        # http://localhost:5555 (le backend doit tourner sur BACKEND_URL, par défaut :4444)
npm run build      # vérifie les types et produit dist/
```

## Organisation

Interface de type chatbot : panneau de conversations (nouvelle, recherche, suppression),
fil de messages, zone de saisie, thème clair/sombre, adaptée au mobile. Couleurs unies, sans dégradé.

| Dossier / fichier | Rôle |
|---|---|
| `src/api/client.ts` | Seul fichier qui appelle le backend, envoie `X-Device-Id` |
| `src/api/types.ts` | Formats JSON, identiques à `api/schemas.py` |
| `src/lib/deviceId.ts` | Identifiant de l'appareil (créé une fois, gardé dans le navigateur) |
| `src/hooks/useChat.ts` | Conversation ouverte : envoi, attente de la réponse, messages |
| `src/hooks/useConversations.ts` | Liste des conversations (panneau de gauche) |
| `src/hooks/useTheme.ts` | Thème clair / sombre |
| `src/components/` | `Sidebar`, `MessageList`, `Composer`, `Welcome`, `Icons` |
| `src/styles.css` | Couleurs des deux thèmes, mise en page, mobile |

En production, l'interface construite (`dist/`) est servie par le backend (image Docker unique).
