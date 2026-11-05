# docker/

Dockerfiles du backend et du frontend. Le `docker-compose.yml` est à la racine.

| Fichier | Rôle |
|---|---|
| `backend.Dockerfile` | Image Python : PyTorch (CPU par défaut, CUDA via `TORCH_INDEX_URL`) + LitGPT + API |
| `frontend.Dockerfile` | Build React avec Node, puis service par nginx |
| `nginx.conf` | Sert l'interface et relaie `/question` et `/response` vers le backend |

## Commandes

```bash
cp .env.example .env
docker compose pull && docker compose up -d                                 # images publiées
docker compose up --build -d                                              # CPU, depuis le code
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d   # GPU NVIDIA
docker compose logs -f backend
docker compose down          # arrête tout, les données restent dans ./models, ./checkpoints...
```

## Services

- `model` : télécharge `MODEL_NAME` dans `./models` puis s'arrête (ne fait rien si déjà présent)
- `backend` : API sur le port `BACKEND_PORT` (4444 par défaut)
- `frontend` : interface sur le port `FRONTEND_PORT` (5555 par défaut)

## Données persistantes

Les dossiers du projet sont montés dans les conteneurs : `models`, `checkpoints`, `datasets`,
`documents`, `tokenizer`, `logs`. Le cache HuggingFace est dans le volume nommé `hf-cache`.
Dans `.env`, `MODEL_PATH` et `TOKENIZER_PATH` doivent rester relatifs (ex : `models/...`).

## Fine-tuning dans Docker

```bash
docker compose run --rm backend python -m training.finetune --method lora \
  --dataset datasets/exemple_instructions.json --name essai
```
