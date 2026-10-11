# RepoFlow

RepoFlow est une application web open source de **supervision multi-dépôts
GitHub**. Elle permet de suivre plusieurs dépôts distants sans les cloner,
de consulter leurs issues et pull requests, de contrôler l'état des checks CI
et de préparer la fusion des pull requests selon des règles configurables.

> **État du projet : v0.1.** L'application fonctionne par défaut en **mode
> démonstration** avec des données fictives clairement identifiées. La
> connexion à l'API GitHub réelle est disponible via
> `REPOFLOW_GITHUB_PROVIDER=github` + `REPOFLOW_GITHUB_TOKEN`. La fusion
> automatique `squash` est **implémentée mais désactivée par défaut** : elle
> n'a lieu que si une règle l'autorise, que la PR est éligible et que
> l'arrêt d'urgence est désengagé.

## Démarrage rapide (Docker Compose)

Le moyen le plus simple, si Docker est installé — aucun prérequis Python/Node :

```bash
git clone <url-du-depot> repoflow
cd repoflow
cp .env.example .env
docker compose up --build
```

- Interface : http://localhost:5173
- API : http://localhost:8000 (documentation Swagger : `/docs`)
- Par défaut : **mode démonstration** (données fictives, aucun jeton requis)
  et base SQLite persistée dans un volume Docker.

Pour brancher des vraies données GitHub, éditer `.env` :
`REPOFLOW_GITHUB_PROVIDER=github` et renseigner `REPOFLOW_GITHUB_TOKEN`
(voir `docs/github-integration.md`). Pour utiliser PostgreSQL : pointer
`REPOFLOW_DATABASE_URL` vers le service `postgres` du compose, puis lancer
`docker compose --profile postgres up --build` (détails plus bas).

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
- Configuration des dépôts suivis et des règles d'automatisation
  (`/api/v1/configs/*`) : CRUD complet, validation stricte côté serveur.
- Worker d'analyse périodique (`python -m app.worker` ou
  `REPOFLOW_WORKER_ENABLED=true`) : évalue les règles et fusionne les PR
  éligibles en `squash` lorsque l'automatisation est explicitement autorisée.
- État des automatisations et arrêt d'urgence global
  (`GET /api/v1/automation/status`, `POST /api/v1/automation/kill-switch`).
- Journal d'audit persistant consultable (`GET /api/v1/audit`, pagination par
  curseur `before_id`) : analyses, décisions, fusions réussies ou bloquées ;
  rétention configurable (`REPOFLOW_AUDIT_RETENTION_DAYS`, purge par le
  worker).
- Suivi du quota GitHub : dernier état `X-RateLimit-*` observé exposé par
  `GET /api/health` (`github_rate_limit`) et badge d'avertissement dans
  l'interface quand le quota restant est bas.
- Interface React sombre, **bilingue français / anglais** (détection du
  navigateur, bascule manuelle persistée, `?lang=en`), responsive :
  navigation, tableau de bord, dépôts, pull requests, détail de PR, issues,
  automatisations, historique, états de chargement / erreur / vide. Les
  messages d'erreur de l'API suivent l'en-tête `Accept-Language`. Filtres
  persistés dans l'URL, rafraîchissement automatique optionnel, moteur de
  recherche insensible à la casse et aux accents, combobox de dépôts
  accessible au clavier.
- Fournisseur de données abstrait (`demo` / `github`).
- Connexion GitHub réelle (dépôts, PR, checks CI, revues) avec pagination,
  requêtes conditionnelles (ETag), chargements coalescés, gestion du rate
  limit et erreurs normalisées ; fusion `squash` contrôlée.
- **GitHub App** (optionnel) : authentification par jeton d'installation
  (`REPOFLOW_GITHUB_APP_*`), échange clé privée → JWT → jeton renouvelé
  automatiquement avant expiration ; quota 15 000 requêtes/h.
- **Transport GraphQL** optionnel (`REPOFLOW_GITHUB_USE_GRAPHQL`) : la liste
  des pull requests est ramenée par une requête unique par dépôt (checks et
  revues incluses) au lieu de 4-5 requêtes REST par PR.
- **Recherche serveur** sur les pull requests et les issues (`?search=`,
  insensible à la casse et aux accents) ; filtres issues par libellé,
  assigné et jalon.
- **Thème clair** en complément du thème sombre (bascule persistée).
- Base SQLite ou **PostgreSQL** (migrations Alembic, options de pool
  configurables).
- **Observabilité** : identifiant de corrélation par requête (`X-Request-ID`)
  propagé dans les journaux et les réponses, journal d'accès, métriques
  Prometheus sur `GET /api/metrics` (compteurs et durées par route).
- **Sécurité** : en-têtes HTTP restrictifs (CSP sur l'API, `nosniff`, DENY
  *frame*…), HSTS optionnel, limitation de débit par adresse IP.
- **Qualité** : couverture de tests suivie en CI (backend ≥ 90 %, frontend
  ≥ 80 % de lignes).
- Tests backend (Pytest + coverage) et frontend (Vitest + coverage).
- Docker Compose (backend, frontend, PostgreSQL optionnel) et CI GitHub
  Actions.

### À venir

- Exécution du worker en service séparé dédié (image partagée).

## Technologies

- **Backend** : Python, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, SQLite /
  PostgreSQL, Pytest (+ couverture), Ruff.
- **Frontend** : React 19, TypeScript (strict), Vite, React Router, i18next
  (react-i18next), Tailwind CSS, lucide-react, ESLint, Vitest (+ couverture),
  React Testing Library.
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

Pour le support PostgreSQL, installer l'extra correspondant (au lieu de ou en
plus de `dev`) :

```bash
pip install -e ".[dev,postgres]"
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

Le worker d'analyse périodique est désactivé par défaut. Pour l'exécuter en
continu dans un processus séparé :

```bash
python -m app.worker
```

Il peut aussi être démarré automatiquement avec l'API via
`REPOFLOW_WORKER_ENABLED=true` (intervalle : `REPOFLOW_WORKER_INTERVAL_SECONDS`).

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

## Exécution via Docker Compose (détaillée)

Cf. aussi « Démarrage rapide » en haut de page.

```bash
cp .env.example .env
docker compose up --build
```

- Backend : http://localhost:8000
- Frontend : http://localhost:5173

La base SQLite est persistée dans un volume Docker nommé.

Avec PostgreSQL (profil optionnel) :

```bash
# 1. Adapter .env :
#    REPOFLOW_DATABASE_URL=postgresql+psycopg://repoflow:repoflow@postgres:5432/repoflow
#    (le mot de passe doit correspondre à REPOFLOW_DB_PASSWORD)
# 2. Lancer, profil "postgres" inclus :
docker compose --profile postgres up --build
```

## Tests et qualité

### Backend

```bash
cd backend
source .venv/bin/activate
ruff check .          # lint
ruff format --check . # formatage
pytest                # tests + couverture (seuil : 90 %)
```

La couverture est mesurée par défaut (`pytest` inclut `--cov=app`) ; la
commande échoue sous 90 % de couverture.

Migrations :

```bash
alembic upgrade head
```

### Frontend

```bash
cd frontend
npm run lint            # ESLint
npm run typecheck       # TypeScript strict
npm test                # Vitest
npm run test:coverage   # Vitest + couverture (seuils : lignes 80 %, branches 65 %)
npm run build           # build de production
```

## Structure du projet

```text
repoflow/
├── backend/
│   ├── app/
│   │   ├── api/            # routes HTTP (v1) + santé + métriques
│   │   ├── core/           # config, logging, erreurs, sécurité,
│   │   │                   #   métriques, contexte de requête
│   │   ├── db/             # moteur, sessions, init
│   │   ├── models/         # modèles SQLAlchemy
│   │   ├── schemas/        # schémas Pydantic
│   │   ├── services/       # règles métier
│   │   ├── integrations/
│   │   │   └── github/     # fournisseur abstrait (démo + GitHub)
│   │   ├── worker.py       # worker d'analyse périodique
│   │   └── main.py
│   ├── alembic/            # migrations
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   └── src/
│       ├── components/  layouts/  pages/
│       ├── hooks/       lib/      services/  types/
│       └── test/        main.tsx
├── docs/                   # architecture, GitHub, guide utilisateur
├── .github/workflows/      # CI
├── docker-compose.yml
├── .env.example
├── AGENTS.md
├── CONTRIBUTING.md
├── PLAN.md
└── README.md
```

## Sécurité et fusion

- Aucun secret dans le frontend, les journaux ou les URL.
- Les tokens GitHub restent côté serveur avec des permissions minimales.
- La fusion automatique est désactivée par défaut (`REPOFLOW_AUTO_MERGE_ENABLED_GLOBALLY=false`)
  et doit être explicitement autorisée **à la fois** globalement et par règle.
- Un check échoué, en cours ou inconnu n'est **jamais** considéré comme réussi.
- Une pull request en brouillon n'est jamais fusionnée automatiquement.
- La fusion n'est envisagée que vers la branche par défaut du dépôt (protection
  de branche prudente) ; aucun contournement administrateur.
- Un arrêt d'urgence global est opérationnel (`REPOFLOW_KILL_SWITCH_ENGAGED`
  ou bascule via l'API/la page Automatisations).
- Le worker n'exécute une fusion que si toutes les conditions sont réunies ;
  chaque décision est journalisée dans l'audit.

Voir `docs/architecture.md`, `docs/github-integration.md` et
`docs/user-guide.md` pour les détails.

## Licence

MIT (voir le fichier de licence à venir).
