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
├── inference/     Logique d'inférence : chargement du modèle, file des requêtes
├── training/      Fine-tuning (full, LoRA, QLoRA)
├── rag/           Futur : recherche dans les documents + base vectorielle
├── config/        settings.py (lit .env) + recettes YAML LitGPT (config/litgpt/)
├── frontend/      Interface web React + Vite + TypeScript
├── docker/        Dockerfiles
├── scripts/       Scripts utilitaires
├── tests/         Tests du moteur LitGPT
├── models/        (données) poids des modèles          ┐
├── checkpoints/   (données) résultats de fine-tuning   │ volumes Docker,
├── datasets/      (données) jeux d'entraînement        │ ignorés par git
├── documents/     (données) documents sources          │
├── tokenizer/     (données) tokenizer séparé           │
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

## Lancer l'API

```bash
cp .env.example .env
pip install -e ".[extra,platform]"
python -m backend.main          # http://localhost:8000, doc interactive sur /docs
```

```bash
curl -X POST localhost:8000/question -H "Content-Type: application/json" -d '{"prompt": "Qu'\''est-ce qu'\''un décret ?"}'
# {"request_id": "4f2c...", "status": "pending"}

curl localhost:8000/response/4f2c...
# {"request_id": "4f2c...", "status": "completed", "response": "...", "tokens": 87, "elapsed_time": 3.21, "error": null}
```

Statuts : `pending` (en file) → `processing` (le modèle génère) → `completed` ou `failed`.

## Lancer avec Docker

```bash
cp .env.example .env
docker compose up --build -d        # interface : http://localhost:3000
# GPU NVIDIA :
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d
```

Détails dans `docker/README.md`.

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
6. ✅ Docker / docker-compose (`docker/`, `docker-compose.yml`)
7. Plus tard : RAG, base vectorielle, multi-modèle, authentification, historique, tableau de bord
