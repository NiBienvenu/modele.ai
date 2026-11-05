# api/

Couche HTTP (FastAPI) : routes, schémas des requêtes et réponses. Appelle `inference/`, ne touche jamais directement au modèle.

| Route | Rôle |
|---|---|
| `POST /question` `{"prompt", "conversation_id"?}` | Met la question en file, `202` `{"request_id", "status", "conversation_id"}` |
| `GET /response/{request_id}` | Statut et réponse (`response`, `tokens`, `elapsed_time`, `error`) |
| `GET /conversations` | Conversations de l'appareil |
| `GET /conversations/{id}` | Une conversation et ses messages |
| `DELETE /conversations/{id}` | Supprime une conversation |

En-tête obligatoire : `X-Device-Id` (pas d'authentification, les conversations sont liées à l'appareil).

Fichiers : `schemas.py` (formats JSON), `routes.py` (les routes), `dependencies.py` (services + `X-Device-Id`).
