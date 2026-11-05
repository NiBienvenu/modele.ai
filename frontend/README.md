# frontend/

Interface web React + Vite + TypeScript. Ne parle qu'aux deux routes REST, aucune logique métier.

## Lancer en développement

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (le backend doit tourner sur BACKEND_URL, par défaut :8000)
npm run build      # vérifie les types et produit dist/
```

## Organisation

| Dossier / fichier | Rôle |
|---|---|
| `src/api/client.ts` | Seul fichier qui appelle le backend (`POST /question`, `GET /response/{id}`) |
| `src/api/types.ts` | Formats JSON, identiques à `api/schemas.py` |
| `src/hooks/useQuestion.ts` | Envoie la question puis redemande la réponse chaque seconde |
| `src/hooks/useHistory.ts` | Historique local (50 dernières questions, dans le navigateur) |
| `src/hooks/useTheme.ts` | Thème clair / sombre, mémorisé |
| `src/components/` | Composants d'affichage : formulaire, réponse, stats, historique, bouton de thème |
| `src/styles.css` | Styles, couleurs des deux thèmes, adaptation mobile |
