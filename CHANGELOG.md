# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Versioning Sémantique](https://semver.org/lang/fr/spec/v2.0.0.html).

## [Non publié]

### Ajouté
- Authentification par jeton porteur (API) et verrouillage front via AuthGate.
- Sondes liveness/readiness `/api/health/live` et `/api/health/ready`.
- Export CSV/JSON du journal d'audit avec nom de fichier daté.
- Thème système (`prefers-color-scheme`) + script anti-FOUC.
- Métriques métier étendues (histogrammes, compteurs, jauge dernier succès worker).
- Tests d'accessibilité axe-core (contraste désactivé).

### Modifié
- Orchestration des middlewares FastAPI (auth positionnée avant CORS/métriques).
- Câblage des métriques sur analyse, worker, cache et provider GitHub.
- Traductions front (auth, export audit).

### Sécurité
- Auth middleware avec comparaison `hmac.compare_digest` et schéma Bearer.
- Journal d'audit non sensible aux secrets (rendu au display).

## [0.1.0] - 2025-09-30

### Ajouté
- MVP backend FastAPI (analyse PR, règles, cache, audit, métriques, kill switch).
- Frontend React/Vite/TypeScript (tableaux, détails PR, historique, automations).
- Worker d'agrégats quotidiens, snapshots JSON, i18n fr/en.
- CI GitHub Actions (lint, tests, coverage backend/frontend).
- Docker Compose de développement (backend, frontend, PostgreSQL optionnel).
