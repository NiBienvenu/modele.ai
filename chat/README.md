# chat/

Logique des conversations, sans compte utilisateur : chaque conversation appartient au
`device_id` envoyé par le navigateur (en-tête `X-Device-Id`).

| Fichier | Rôle |
|---|---|
| `schemas.py` | `Conversation`, `Message`, `Role` |
| `repository.py` | Stockage SQLite (`storage/conversations.db`) |
| `prompt_builder.py` | Ajoute les derniers messages avant la question (`CHAT_HISTORY_MESSAGES`) |
| `service.py` | `ChatService` : crée la conversation, envoie au modèle, enregistre la réponse |
