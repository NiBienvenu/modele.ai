# backend/

Point d'entrée du serveur Python. Assemble la config, le moteur IA et l'API (ex. `backend/main.py`). Ne contient pas de logique métier.

`main.py` : `create_app()` assemble config + service d'inférence + routes + CORS.
Lancer : `python -m backend.main` ou `uvicorn backend.main:build_default_app --factory`.
