# RepoFlow — Frontend

Interface React + TypeScript (strict) de RepoFlow, construite avec Vite et
stylée avec Tailwind CSS. Voir le [README principal](../README.md) pour
l'installation complète.

## Commandes

```bash
npm install
npm run dev        # serveur de développement (http://localhost:5173)
npm run lint       # ESLint
npm run typecheck  # TypeScript strict
npm test           # Vitest + Testing Library
npm run build      # build de production
```

Le serveur de développement relaie les requêtes `/api` vers le backend
FastAPI (voir `server.proxy` dans `vite.config.ts`).
