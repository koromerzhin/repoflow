# Contribuer à RepoFlow

Merci pour votre intérêt ! Ce guide décrit les conventions du projet. La
lecture d'`AGENTS.md` (conventions de développement) est un prérequis.

## Installer le projet

Voir section « Installation locale » du `README.md`. En résumé :

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd frontend && npm install
```

## Valider avant de proposer une modification

Tout changement doit passer **tous** les contrôles :

### Backend (depuis `backend/`)

```bash
ruff check .            # lint
ruff format --check .   # formatage
pytest                  # tests + couverture (seuil : 90 %)
alembic upgrade head    # si migration nouvelle
alembic downgrade base  # vérifier la réversibilité
```

### Frontend (depuis `frontend/`)

```bash
npm run lint
npm run typecheck
npm test
npm run test:coverage   # seuils : lignes 80 %, branches 65 %
npm run build
```

## Règles de code

- **Backend** : Python typé (`from __future__ import annotations`), Ruff comme
  source de vérité, aucun commentaire superflu. Interfaces et messages en
  **français** (et **anglais** via `Accept-Language`).
- **Frontend** : TypeScript strict, alias `@/`, composants fonctionnels,
  interface **bilingue** via `src/i18n/` (locales `fr` et `en` — tout libellé
  passe par une clé de traduction), tests Testing Library, pas de dépendance à
  un vrai serveur.
- Les réponses API sont typées par des schémas Pydantic explicites ; les types
  TypeScript leur correspondent dans `src/types/api.ts`.
- Les données de démonstration sont toujours identifiables
  (`is_demo: true`, `data_source: "demo"`).

## Tests

- **Backend** : couvrir chaque route et chaque règle métier (cas passant et
  bloquant) avec `TestClient` et des données déterministes.
- **Frontend** : tester les composants et le client HTTP ; mocker le client
  (`apiClient.ts`) pour isoler les pages.
- La couverture est mesurée dans la CI ; ne pas baisser le seuil sans
  justification.

## Migrations Alembic

Toute modification des modèles SQLAlchemy exige une migration autogénérée et
testée (`alembic revision --autogenerate -m "description"` puis `upgrade head`
et `downgrade base`).

## Sécurité — règles non négociables

- Jamais de secret dans le frontend, les logs ou les URL.
- Les tokens GitHub restent côté serveur.
- Un check échoué, en cours ou **inconnu** n'est jamais un succès.
- Une PR en brouillon n'est jamais fusionnée automatiquement.
- Aucune fusion automatique par défaut ; chaque décision est journalisée.
- Aucun contournement administrateur des protections de branche.

## Proposer une modification

1. Travailler sur une branche dédiée (`develop` est la branche de
   référence). Ouvrir une pull request vers `develop`.
2. Décrire la motivation et l'approche ; lier l'issue éventuelle.
3. Les vérifications CI (lint, tests, couverture, migrations) doivent être
   vertes avant toute fusion.
4. Une pull request en brouillon n'est jamais fusionnée ; la fusion est
   manuelle et examinée.