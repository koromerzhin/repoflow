# RepoFlow

RepoFlow est une application web open source de **supervision multi-dépôts
GitHub**. Elle permet de suivre plusieurs dépôts distants sans les cloner,
de consulter leurs issues et pull requests, de contrôler l'état des checks CI
et de préparer la fusion des pull requests selon des règles configurables.

> **État du projet : v0.1.** L'application fonctionne par défaut en **mode
> démonstration** avec des données fictives clairement identifiées. La
> connexion à l'API GitHub réelle est disponible en **lecture seule** via
> `REPOFLOW_GITHUB_PROVIDER=github` + `REPOFLOW_GITHUB_TOKEN`. La fusion
> automatique n'est pas encore active.

## Fonctionnalités

### Disponibles

- Backend FastAPI avec point de santé `GET /api/health`.
- Tableau de bord `GET /api/v1/dashboard` : indicateurs et activité récente.
- Dépôts `GET /api/v1/repositories`.
- Pull requests `GET /api/v1/pull-requests` (filtre par dépôt) avec état
  agrégé des checks et éligibilité de fusion **indicative**.
- Issues `GET /api/v1/issues` (filtres par dépôt et par état) — les pull
  requests sont exclues de cette liste.
- Détail d'une pull request `GET /api/v1/pull-requests/{number}` : fichiers
  modifiés, revues et timeline, avec page frontend dédiée.
- Cache TTL mémoire des données du fournisseur (`REPOFLOW_CACHE_TTL_SECONDS`)
  et rafraîchissement manuel via `?refresh=true` ou les boutons « Rafraîchir ».
- Interface React sombre, en français, responsive : navigation, tableau de
  bord, dépôts, pull requests, détail de PR, issues, états de chargement /
  erreur / vide.
- Fournisseur de données abstrait (`demo` / `github`).
- Connexion GitHub réelle **en lecture seule** (dépôts, PR, checks CI,
  revues) avec pagination, gestion du rate limit et erreurs normalisées.
- Base SQLite, migrations Alembic, historique d'audit et règles
  d'automatisation (désactivées par défaut).
- Tests backend (Pytest) et frontend (Vitest + Testing Library).
- Docker Compose et CI GitHub Actions.

### À venir

- Configuration des règles d'automatisation par dépôt et par branche.
- Fusion automatique `squash` **contrôlée côté serveur** (désactivée par défaut).
- Worker d'analyse périodique.
- Journal d'audit consultable dans l'interface.

## Technologies

- **Backend** : Python, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, SQLite,
  Pytest, Ruff.
- **Frontend** : React 19, TypeScript (strict), Vite, React Router, Tailwind
  CSS, lucide-react, ESLint, Vitest, React Testing Library.
- **Exécution** : Docker, Docker Compose, GitHub Actions.

## Prérequis

- Python **3.11+** (testé avec 3.14).
- Node.js **20+** (testé avec 22) et npm.
- Docker et Docker Compose (optionnel, pour l'exécution conteneurisée).

## Installation locale

```bash
git clone <url-du-depot> repoflow
cd repoflow
cp .env.example .env
```

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Lancer le serveur de développement :

```bash
uvicorn app.main:app --reload --port 8000
```

- API : http://localhost:8000
- Documentation interactive : http://localhost:8000/docs
- Santé : http://localhost:8000/api/health

Par défaut, la base SQLite est créée automatiquement et le mode
démonstration est actif (aucun token requis).

### Frontend

Dans un second terminal :

```bash
cd frontend
npm install
npm run dev
```

- Interface : http://localhost:5173

Le frontend relaie les appels `/api` vers le backend (proxy Vite), aucune
configuration CORS supplémentaire n'est nécessaire.

## Exécution via Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

- Backend : http://localhost:8000
- Frontend : http://localhost:5173

La base SQLite est persistée dans un volume Docker nommé.

## Tests et qualité

### Backend

```bash
cd backend
source .venv/bin/activate
ruff check .          # lint
ruff format --check . # formatage
pytest                # tests
```

Migrations :

```bash
alembic upgrade head
```

### Frontend

```bash
cd frontend
npm run lint       # ESLint
npm run typecheck  # TypeScript strict
npm test           # Vitest
npm run build      # build de production
```

## Structure du projet

```text
repoflow/
├── backend/
│   ├── app/
│   │   ├── api/            # routes HTTP (v1) + santé
│   │   ├── core/           # config, logging, erreurs
│   │   ├── db/             # moteur, sessions, init
│   │   ├── models/         # modèles SQLAlchemy
│   │   ├── schemas/        # schémas Pydantic
│   │   ├── services/       # règles métier
│   │   ├── integrations/
│   │   │   └── github/     # fournisseur abstrait (démo + GitHub)
│   │   └── main.py
│   ├── alembic/            # migrations
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   └── src/
│       ├── components/  features/  layouts/  pages/
│       ├── services/    hooks/     lib/      types/
│       └── main.tsx
├── docs/                   # documentation d'architecture et GitHub
├── .github/workflows/      # CI
├── docker-compose.yml
├── .env.example
├── AGENTS.md
├── PLAN.md
└── README.md
```

## Sécurité et fusion

- Aucun secret dans le frontend, les journaux ou les URL.
- Les tokens GitHub restent côté serveur avec des permissions minimales.
- Aucune fusion automatique n'est active par défaut ; toute action de fusion
  sera contrôlée côté serveur.
- Un check échoué, en cours ou inconnu n'est **jamais** considéré comme réussi.
- Une pull request en brouillon n'est jamais fusionnée automatiquement.
- Un arrêt d'urgence global est prévu (`REPOFLOW_KILL_SWITCH_ENGAGED`).

Voir `docs/architecture.md` et `docs/github-integration.md` pour les détails.

## Licence

MIT (voir le fichier de licence à venir).
