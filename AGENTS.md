# AGENTS.md — conventions de développement RepoFlow

Ce document guide les agents de développement (dont OpenCode) travaillant sur
RepoFlow. Il décrit les commandes, la structure et les règles à respecter.

## Commandes essentielles

### Backend (depuis `backend/`)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

ruff check .            # lint — doit passer
ruff format .           # formatage (ou --check en CI)
pytest                  # tests — doivent passer
uvicorn app.main:app --reload --port 8000
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Frontend (depuis `frontend/`)

```bash
npm install
npm run lint            # ESLint — doit passer
npm run typecheck       # TypeScript strict — doit passer
npm test                # Vitest
npm run build           # build de production
npm run dev
```

Toujours exécuter lint + tests avant de considérer une tâche terminée.

## Architecture

Respecter la séparation des responsabilités :

- `app/api/` : routes HTTP uniquement, pas de logique métier.
- `app/services/` : règles métier, indépendantes d'un fournisseur précis.
- `app/integrations/github/` : accès aux données via le contrat `Provider`.
- `app/schemas/` : modèles Pydantic des entrées/sorties.
- `app/models/` : modèles SQLAlchemy.
- `app/core/` : configuration, logging, erreurs.

Côté frontend :

- `src/types/` : types calqués sur les schémas Pydantic du backend.
- `src/services/` : un client HTTP centralisé (`apiClient.ts`).
- `src/pages/` : pages routées. `src/components/` : composants réutilisables.

## Règles de code

- **Backend** : Python typé (`from __future__ import annotations`), Ruff comme
  source de vérité (lint + format). Pas de commentaire superflu.
- **Frontend** : TypeScript `strict`, imports via l'alias `@/`, composants
  fonctionnels. Interface en **français**. Ne pas utiliser de commentaires
  inutiles.
- Les réponses d'API sont typées par des schémas Pydantic explicites.
- Les données de démonstration doivent toujours être identifiables
  (`is_demo: true`, `data_source: "demo"`).

## Sécurité — règles non négociables

- **Jamais** de secret dans le frontend, les logs ou les URL.
- Les tokens GitHub restent côté serveur.
- Un check échoué, en cours ou **inconnu** n'est jamais un succès.
- Une PR en brouillon n'est jamais fusionnée automatiquement.
- Aucune fusion automatique par défaut.
- Aucun contournement administrateur des protections de branche.
- Toute action réelle sur GitHub est interdite sans autorisation explicite.

## Migrations

Toute modification des modèles SQLAlchemy doit être accompagnée d'une
migration Alembic autogénérée et testée (`upgrade head` puis `downgrade base`).

## Tests

- Backend : couvrir chaque route et chaque règle métier (cas passant et
  bloquant). Utiliser `TestClient` et des données déterministes.
- Frontend : tester les composants et le client HTTP avec Testing Library ;
  ne jamais dépendre d'un vrai serveur.
