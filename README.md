# Plateforme IA documentaire

Base de code pour créer un modèle d'IA spécialisé dans les documents :
livres, lois, décrets, histoire, documents administratifs et techniques,
documentation interne.

Le moteur IA est [LitGPT](https://github.com/Lightning-AI/litgpt) (Lightning AI,
licence Apache 2.0, voir `LICENSE.md`). Il est gardé dans `litgpt/` et allégé,
sans être réécrit.

## Architecture

```
.
├── litgpt/        Moteur IA (LitGPT) : modèles, tokenizer, génération, LoRA, QLoRA, quantization
├── backend/       Point d'entrée du serveur : assemble config + moteur + API
├── api/           Routes REST (HTTP seulement, aucune logique métier)
├── chat/          Conversations par appareil (SQLite), historique envoyé au modèle
├── inference/     Logique d'inférence : chargement du modèle, file des requêtes
├── training/      Fine-tuning (full, LoRA, QLoRA)
├── rag/           Futur : recherche dans les documents + base vectorielle
├── config/        settings.py (lit .env) + recettes YAML LitGPT (config/litgpt/)
├── frontend/      Interface web React + Vite + TypeScript
├── docker/        Dockerfile (image unique : interface + API + moteur)
├── scripts/       Scripts utilitaires
├── tests/         Tests du moteur LitGPT
├── models/        (données) poids des modèles          ┐
├── checkpoints/   (données) résultats de fine-tuning   │ volumes Docker,
├── datasets/      (données) jeux d'entraînement        │ ignorés par git
├── documents/     (données) documents sources          │
├── tokenizer/     (données) tokenizer séparé           │
├── storage/       (données) conversations (SQLite)     │
└── logs/          (données) journaux                   ┘
```

Les couches sont séparées et dépendent dans un seul sens :

```
frontend ──HTTP──▶ api ──▶ inference ──▶ litgpt
                              ▲
                           config (.env)
```

## Ce que garde le moteur LitGPT

- Chargement de modèles HuggingFace (`litgpt download`, `convert_to_litgpt`)
- Tokenizer, génération, inférence (`litgpt.LLM`, `litgpt generate`, `litgpt chat`)
- Gestion CPU/GPU, multi-GPU (`sequentially`, `tp`)
- Quantization (`bnb.nf4`, `bnb.int8`...)
- Fine-tuning : full, LoRA, QLoRA, adapter (`litgpt finetune_*`), fusion LoRA (`merge_lora`)
- Données : `JSON` (vos paires question/réponse), `TextFiles` (fichiers .txt), `Alpaca` (jeu de test)
- Recettes d'entraînement dans `config/litgpt/finetune/`

## Démarrage rapide (moteur seul)

```bash
pip install -e ".[extra]"

# Télécharger un petit modèle dans models/
litgpt download TinyLlama/TinyLlama-1.1B-Chat-v1.0 --checkpoint_dir models

# Générer du texte
litgpt generate models/TinyLlama/TinyLlama-1.1B-Chat-v1.0 --prompt "Qu'est-ce qu'un décret ?"

# Fine-tuning LoRA sur vos propres données JSON
litgpt finetune_lora models/TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
  --data JSON --data.json_path datasets/mes_donnees.json \
  --out_dir checkpoints/mon-modele
```

Format attendu pour `datasets/mes_donnees.json` :

```json
[
  {"instruction": "Que dit l'article 3 ?", "input": "", "output": "L'article 3 précise..."}
]
```

## Ports

| Service | Port | Adresse |
|---|---|---|
| Interface web (frontend) | **5555** | http://localhost:5555 |
| API (backend) | **4444** | http://localhost:4444/docs |

Pour en changer : `FRONTEND_PORT` / `BACKEND_PORT` (Docker) et `PORT` / `CORS_ORIGINS` (backend) dans `.env`.

## Tester dans le navigateur (Docker, le plus simple)

```bash
cp .env.example .env              # choisir MODEL_NAME si besoin
docker compose pull               # récupère l'image publiée sur ghcr.io
docker compose up -d              # lance le conteneur unique (interface + API + modèle)
docker compose logs -f app        # 1re fois : suivre le téléchargement du modèle
```

Puis ouvrir **http://localhost:5555**, écrire une question, appuyer sur **Entrée**.
La réponse s'affiche avec le temps et le nombre de tokens. Les conversations apparaissent
dans le panneau de gauche (recherche, suppression) et sont gardées sur le serveur, liées à
l'appareil (aucun compte : le navigateur envoie un identifiant `X-Device-Id`).
La documentation de l'API est sur **http://localhost:4444/docs** (bouton « Try it out »).

> Le premier lancement télécharge le modèle dans `./models` : l'interface affiche
> « En file d'attente… » tant que le modèle se charge. Les fois suivantes, il est déjà là.

Arrêter : `docker compose down` (les modèles et documents restent dans les dossiers du projet).

## Mettre à jour (images Docker publiées)

À chaque push sur `develop` (ou `master`), GitHub Actions (`.github/workflows/docker-publish.yml`)
construit et publie **une seule image** : `ghcr.io/nibienvenu/plateforme-ia`

Le dépôt étant privé, l'image l'est aussi. Une seule fois par machine, se connecter
avec un token GitHub (Settings > Developer settings > Personal access tokens, droit `read:packages`) :

```bash
echo VOTRE_TOKEN | docker login ghcr.io -u NiBienvenu --password-stdin
```

Pour récupérer la dernière version sur n'importe quelle machine :

```bash
git pull                          # met à jour docker-compose.yml et .env.example
docker compose pull               # télécharge la nouvelle image
docker compose up -d              # redémarre les conteneurs mis à jour
```

Version précise : créer un tag git `v1.0.0` (images `:1.0.0`), puis `IMAGE_TAG=1.0.0` dans `.env`.
Construire depuis le code au lieu de télécharger : `docker compose up --build -d`.
GPU NVIDIA (construction locale) : `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d`.

## Tester sans Docker (développement)

```bash
cp .env.example .env
pip install -e ".[extra,platform]"
python -m backend.main                       # terminal 1 : API sur http://localhost:4444

cd frontend && npm install && npm run dev    # terminal 2 : interface sur http://localhost:5555
```

Avec `curl` :

```bash
curl -X POST localhost:4444/question -H "Content-Type: application/json" -H "X-Device-Id: mon-appareil-01" -d '{"prompt": "Qu'\''est-ce qu'\''un décret ?"}'
# {"request_id": "4f2c...", "status": "pending", "conversation_id": "9a1b..."}

curl localhost:4444/response/4f2c...
# {"request_id": "4f2c...", "status": "completed", "response": "...", "tokens": 87, "elapsed_time": 3.21, "error": null}
```

Toutes les routes de conversation demandent l'en-tête `X-Device-Id` (identifiant de l'appareil, 8 à 64 caractères).

| Route | Rôle |
|---|---|
| `POST /question` `{"prompt", "conversation_id"?}` | Pose une question (nouvelle conversation si pas d'id) |
| `GET /response/{request_id}` | Statut et réponse |
| `GET /conversations` | Liste des conversations de l'appareil |
| `GET /conversations/{id}` | Une conversation avec ses messages |
| `DELETE /conversations/{id}` | Supprime une conversation |

Statuts : `pending` (en file) → `processing` (le modèle génère) → `completed` ou `failed`.

## Tests de la plateforme

```bash
python -m unittest discover -s tests/platform -t .
```

## Feuille de route

1. ✅ Nettoyage de LitGPT
2. ✅ Nouvelle arborescence
3. ✅ Configuration centralisée (`.env`) et moteur d'inférence (`inference/`)
4. ✅ API REST : `POST /question`, `GET /response/{request_id}`
5. ✅ Interface web (`frontend/`)
6. ✅ Docker : une seule image publiée sur ghcr.io
7. ✅ Interface chatbot : conversations par appareil, recherche, thème clair/sombre
8. Plus tard : RAG, base vectorielle, multi-modèle, authentification, historique, tableau de bord
