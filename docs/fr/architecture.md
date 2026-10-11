# Architecture — RepoFlow

Ce document décrit l'architecture logique, les choix de conception et les interactions entre composants.

## Vue d'ensemble

RepoFlow est une application modulaire FastAPI + React permettant d'analyser, de prioriser et d'automatiser la gestion des pull requests (PR) GitHub. L'approche repose sur :
- Un **backend API** FastAPI (monolithique modulaire) exposant des routes REST versionnées (`/api/v1`).
- Un **frontend React/Vite/TypeScript** consommant l'API.
- Un **worker d'analyse périodique** (Thread / tâche planifiée) qui agrège les métriques et applique des règles.
- Un **fournisseur de données GitHub** abstrait (implémentation démo + GitHub API) pour faciliter les tests sans dépendre du réseau.

L'objectif est la simplicité, la testabilité et la prévisibilité (aucune fusion automatique par défaut).

## Organisation des modules (backend)

| Répertoire | Responsabilité |
| --- | --- |
| `app/api/` | Routes HTTP et dépendances FastAPI. Aucune logique métier. |
| `app/api/v1/routes/` | Endpoints versionnés (`dashboard`, `repositories`, `pull-requests`, `pull-requests/{number}`, `issues`, `configs`, `automation`, `audit`) et `health`/`health/live`/`health/ready`. |
| `app/core/` | Configuration, logging, gestion des erreurs, cache TTL mémoire. |
| `app/db/` | Moteur, sessions et initialisation de la base. |
| `app/integrations/github/` | Abstraction du fournisseur (`Provider`), implémentations `demo` et `github_api`. |
| `app/models/` | Modèles SQLAlchemy (repositories, rules, audit, daily_snapshots). |
| `app/schemas/` | Schémas Pydantic d'entrée/sortie (types partagés avec le front). |
| `app/services/` | Logique métier : `analysis_service` (règles + décisions), `config_service`, `automation_service`, `audit_service`, `snapshots_service`. |
| `app/i18n.py` | Localisation des messages d'erreur API (fr/en) via `Accept-Language`. |
| `app/main.py` | Création de l'app, middlewares, gestion des exceptions, routes racines/métriques. |
| `app/worker.py` | Worker d'analyse périodique (mode boucle ou unique exécution). |

## Séparation des responsabilités

- **Routes** : validation des requêtes, appels aux services, retour de schémas Pydantic. Pas d'accès direct à GitHub depuis les routes.
- **Services** : règles d'orchestration (analyse d'une PR, application des règles, journalisation d'audit). Indépendants du protocole HTTP.
- **Intégrations** : seul ce module parle à GitHub (ou à la démo). Retourne des DTO internes (`PullRequest`, `Check`, `Review`, etc.) pour découpler les modèles.
- **Modèles/Schémas** : modèles SQLAlchemy (persistance) vs schémas Pydantic (API) — jamais exposer directement un modèle ORM brut.
- **Core** : utilitaires transverses (config, erreurs, métriques, logging, contexte).

## Modèle de données (synthétique)

- `repository_configs` : dépôts suivis, options (activer automatisation, restrictions). Index sur `full_name`.
- `merge_rules` : règles par dépôt (et optionnellement par branche cible), filtres, conditions, flags `auto_merge_enabled`, `enabled`. Contrainte d'unicité logique (dépôt + branche).
- `audit_logs` : journal immuable des événements (type, payload sérialisé, PR, acteur, horodatage). Purge selon rétention.
- `daily_snapshots` : agrégats quotidiens (ouverture, prêtes à fusionner, échecs de checks, issues ouvertes) par dépôt/date.

Les données de démonstration sont signalées par `is_demo: true` / `data_source: "demo"` dans les réponses.

## Collecte des données GitHub

Les dépôts suivis ne sont pas dupliqués en base : les PR/issues sont lus à la
demande auprès du fournisseur, puis mis en cache mémoire
(`REPOFLOW_CACHE_TTL_SECONDS`, `?refresh=true` pour forcer).

L'agrégation (`provider.collect`) interroge les dépôts **en parallèle**, avec
une concurrence bornée (`REPOFLOW_GITHUB_MAX_CONCURRENCY`) et un budget de
temps par dépôt (`REPOFLOW_GITHUB_COLLECTION_TIMEOUT`). Un dépôt lent ou en
échec **réseau** est ignoré sans faire échouer la requête ; en revanche les
erreurs applicatives (limite de requêtes, authentification, permissions)
remontent telles quelles au client.

Les dépôts **archivés** sont exclus du référentiel affiché et de toutes les
agrégations (PR, issues, compteurs) : leurs données sont figées. Un dépôt
archivé reste interrogeable individuellement (vue ciblée, détail de PR).

## Worker d'analyse

- Exécuté périodiquement (`REPOFLOW_WORKER_ENABLED`, intervalle configurable). Peut tourner en mode « one-shot ».
- Pour chaque dépôt configuré : collecte des PR ouvertes, récupère checks/reviews, applique les règles (`analysis_service.decide_merge`).
- Écrit dans `audit_logs` chaque décision (`analysis`, `merge_attempted`, `merge_blocked`, `merge_succeeded`, `merge_failed`).
- Persiste un snapshot quotidien (`snapshots_service.persist_daily_snapshot`).
- Purge les anciens `audit_logs` selon `REPOFLOW_AUDIT_RETENTION_DAYS`.
- Gère le `kill_switch` global (`automation_service.is_kill_switch_engaged`) : aucune fusion n'a lieu si engagé.

## Automatisation & sécurité des fusions

- Fusion uniquement sur PR **non brouillon**, **pas fermée/verrouillée**, **vers la branche par défaut**, avec **tous les checks requis réussis** (aucun check échoué/en cours/inconnu).
- Au moins une revue approuvante (selon règles) et pas de changements requis.
- Conflits = bloqués. Mergeable state pris en compte avec prudence.
- **Jamais** de contournement des protections de branche administrateur.
- Mode `squash` privilégié côté implémentation (`merge_method="squash"`).
- Démonstration : la fusion est simulée (jamais appelée réellement contre GitHub) quand `GITHUB_PROVIDER=demo`.

## Couches transverses

### Middlewares (FastAPI, ordre du plus interne au plus externe)

1. **Limitation de débit** (`app/core/security.py`) — fenêtre fixe en mémoire, clé IP. Désactivée par défaut ; `429` si seuil dépassé.
2. **En-têtes de sécurité** — `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, COOP/CORP, CSP sur `/api`, HSTS si HTTPS.
3. **Authentification** (`app/core/security.py`) — jeton porteur optionnel `Authorization: Bearer` si `REPOFLOW_API_TOKEN` défini ; 401 sur `/api/v1/*` avec `WWW-Authenticate: Bearer`.
4. **Métriques** (`app/core/metrics.py`) — exposition Prometheus `/api/metrics` (normalisation des routes dynamiques).
5. **Contexte de requête** (`app/core/request_context.py`) — `X-Request-ID` (client ou généré), propagé dans les logs, renvoyé au client ; accès structuré.
6. **CORS** — appliqué aux réponses (y compris erreurs).

### Métriques & observabilité

- Compteurs : requêtes HTTP, événements cache, appels provider, décisions worker/merge.
- Histogrammes de latence (requêtes HTTP, appels provider).
- Jauge : `repoflow_worker_last_success_timestamp_seconds`.
- Cache TTL mémoire (clé par type de ressource, `maxsize`, TTL). En production, Redis peut être envisagé.
- Journalisation structurée (niveau, module, request_id). Erreurs normalisées vers schémas JSON cohérents.

### Gestion des erreurs

- Exceptions métier (`app/core/errors.py`) mappées vers codes HTTP + `error.code` + `error.message` (localisé via i18n).
- Validation Pydantic → 422 avec structure `{"error": {...}}`.
- 401/403/404/409/429/500 cohérents.

### Internationalisation

- API : sélection via `Accept-Language` (`app/i18n.py`), messages en français/anglais.
- Frontend : `i18next` (`src/i18n/locales/fr.ts`, `en.ts`), tout libellé via clés, détection + persistance locale.

## Frontend (React/Vite/TS)

| Répertoire | Responsabilité |
| --- | --- |
| `src/components/` | Composants réutilisables (badges, cartes, drawer, sélecteurs). |
| `src/hooks/` | Hooks personnalisés (état URL, auto-refresh, thème). |
| `src/layouts/` | Mise en page commune (`AppLayout`). |
| `src/lib/` | Utilitaires (auth, téléchargement). |
| `src/pages/` | Pages routées (Dashboard, PRs, Issues, Automations, History, Détail PR, 404). |
| `src/services/` | Client HTTP centralisé (`apiClient.ts`) — gestion des erreurs, auth Bearer, export audit. |
| `src/types/` | Types alignés sur schémas Pydantic backend. |
| `src/i18n/` | Configuration + locales fr/en. |

- Routage `react-router-dom`, thème sombre/clair + `prefers-color-scheme`, auth par token porteur (AuthGate).
- Design responsive, composants fonctionnels, TypeScript strict.

## Déploiement / exécution locale

- **Développement** : `docker compose up --build` (backend+frontend) ou local (venv + npm).
- **Tests** : backend `pytest` (cov >=90%), frontend `vitest` (lignes>=80%, branches>=65%), E2E Playwright.
- **Base** : SQLite par défaut (dév), PostgreSQL via profil compose. Migrations Alembic obligatoires.
- **Configuration** : via variables d'environnement (`.env`) — jamais de secrets dans le front.

## Points d'attention

- Pas de fusion automatique par défaut ; double garde (global + règle).
- Tous les états « en cours/inconnu/échoué » ne sont jamais considérés comme succès.
- PR brouillon jamais fusionnée.
- Aucun contournement admin des règles de protection.
- Auth backend optionnelle mais activée par token ; front gère 401 via AuthGate.
- Export audit respecte filtres et limite 5000/50000 max.
