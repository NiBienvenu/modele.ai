# inference/

Logique métier de l'inférence : chargement du modèle via `litgpt.LLM`, file des requêtes, génération, mesure du temps et des tokens.

| Fichier | Rôle |
|---|---|
| `schemas.py` | Types simples : `GenerationParams`, `GenerationResult`, `Job`, `JobStatus` |
| `model_loader.py` | Seul fichier qui sait charger un modèle LitGPT (téléchargement, GPU, quantization) |
| `engine.py` | `InferenceEngine` (contrat) et `LitGPTEngine` (génération + comptage des tokens + temps) |
| `job_store.py` | Stockage en mémoire des requêtes, nettoyage automatique |
| `service.py` | `InferenceService` : file d'attente + un thread qui traite les questions une par une |
| `factory.py` | Construit le service à partir de la configuration |
