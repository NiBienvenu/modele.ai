# api/

Couche HTTP (FastAPI) : routes, schémas des requêtes et réponses. Appelle `inference/`, ne touche jamais directement au modèle.

| Route | Rôle | Réponse |
|---|---|---|
| `POST /question` `{"prompt": "..."}` | Met la question en file | `202` `{"request_id", "status"}` |
| `GET /response/{request_id}` | Statut et réponse | `200` `{"request_id", "status", "response", "tokens", "elapsed_time", "error"}`, `404` si inconnu |

Fichiers : `schemas.py` (formats JSON), `routes.py` (les 2 routes), `dependencies.py` (injection du service).
