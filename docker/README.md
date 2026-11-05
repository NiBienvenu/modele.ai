# docker/

Une **seule image** contient toute la plateforme : l'interface web, l'API REST et le moteur LitGPT.
FastAPI sert l'interface et l'API dans le même conteneur.

| Fichier | Rôle |
|---|---|
| `Dockerfile` | Étape 1 : build React avec Node. Étape 2 : Python + PyTorch (CPU par défaut, CUDA via `TORCH_INDEX_URL`) + LitGPT + API + interface construite |
| `../docker-compose.yml` | Le service `app`, ses ports et ses volumes |
| `../docker-compose.gpu.yml` | Ajout pour GPU NVIDIA (construction locale) |

## Commandes

```bash
cp .env.example .env
docker compose pull && docker compose up -d                                   # image publiée
docker compose up --build -d                                                  # CPU, depuis le code
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d  # GPU NVIDIA
docker compose logs -f app
docker compose down          # arrête tout, les données restent dans les dossiers du projet
```

## Ports (même conteneur)

- **5555** : interface web (`FRONTEND_PORT`)
- **4444** : API, documentation sur `/docs` (`BACKEND_PORT`)

## Données persistantes

Les dossiers du projet sont montés dans le conteneur : `models`, `checkpoints`, `datasets`,
`documents`, `tokenizer`, `storage` (conversations SQLite), `logs`.
Le cache HuggingFace est dans le volume nommé `hf-cache`.
Le modèle (`MODEL_NAME`) est téléchargé dans `./models` au premier démarrage.
Dans `.env`, `MODEL_PATH` et `TOKENIZER_PATH` doivent rester relatifs (ex : `models/...`).

## Fine-tuning dans Docker

```bash
docker compose run --rm app python -m training.finetune --method lora \
  --dataset datasets/exemple_instructions.json --name essai
```
