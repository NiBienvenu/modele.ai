# config/

Configuration centralisée. `settings.py` lit le fichier `.env`. `litgpt/` contient les recettes YAML de LitGPT (ancien `config_hub`).

| Fichier | Rôle |
|---|---|
| `settings.py` | Lit `.env` et expose `get_settings()` (groupes : paths, model, generation, server) |
| `env.py` | Petit lecteur de fichier `.env`, sans dépendance |
| `logging_setup.py` | Journaux vers la console et `logs/platform.log` |
| `litgpt/` | Recettes YAML de fine-tuning LitGPT (LoRA, QLoRA, full) par modèle |

Pour commencer : `cp .env.example .env` à la racine du projet.
