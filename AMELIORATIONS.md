# Pistes d'amélioration — RepoFlow

Analyse du 12/10/2026 (branche `develop`). Réinitialisation du document :
les pistes précédentes réalisées sont archivées en fin de fichier, la liste
ci-dessous ne contient que les **suggestions encore ouvertes**, classées par
priorité (P0 > P3) et effort (S < 1 j, M 1-3 j, L > 3 j).

État à date : backend 264 tests (couverture ~93,7 %), frontend 135 tests +
8 E2E (couverture 89 % lignes / 81 % branches), CI complète (lint, tests,
migrations Alembic, build, E2E), Docker avec sondes `live`/`ready` et données
persistées dans `./data`.

## P0 — Sécurité et exploitation (à traiter en priorité)

### 1. Comptes utilisateurs et rôles
Le jeton porteur partagé (`REPOFLOW_API_TOKEN`) protège l'instance, mais
l'identité reste unique : impossible de savoir **qui** a fusionné ou engagé
l'arrêt d'urgence. Introduire un compte par utilisateur et un rôle
(lecteur / opérateur / admin) : l'arrêt d'urgence et l'écriture GitHub
réservés aux opérateurs/admins, le journal d'audit enregistrant l'identité.
*Fichiers : `app/api/deps.py`, `app/core/security.py`, modèle `users` +
migration, `frontend/src/hooks/useAuth.ts`, `AuthGate`. Effort : L.*

### 2. Sauvegarde de la base `./data`
La base SQLite vit dans un bind mount sans aucune stratégie de sauvegarde :
une suppression ou une corruption perd configs, règles, audit et snapshots.
Ajouter une sauvegarde automatique (`sqlite3 ... .backup` en cron conteneurisé
ou Litestream vers un stockage externe) **et un test de restauration**
documenté.
*Fichiers : `docker-compose.yml` (service `backup`), doc `user-guide`. Effort : S.*

### 3. Profil « production » durci
Plusieurs protections sont désactivées par défaut : `rate_limit_enabled=false`,
`hsts_enabled=false`, CORS ouvert en développement. Fournir un profil compose
`production` (rate limiting actif, HSTS derrière HTTPS, CORS restreint à
l'origine du frontend, `environment=production`) et un `docker-compose.prod.yml`
documenté.
*Fichiers : `docker-compose.yml`, `.env.example`, `app/core/config.py`. Effort : S-M.*

## P1 — Court terme (forte valeur, faible effort)

### 4. ~~Visibilité du quota GitHub~~ ✅
Réalisé : le client enregistre les en-têtes `X-RateLimit-*` après chaque
réponse, `/api/health` et `/api/health/ready` exposent le quota observé
(remaining/limit/reset), le tableau de bord affiche un badge permanent
(`Quota GitHub : 4 123 / 5 000 requêtes · réinitialisation 14 h 02`,
vert > 20 %, jaune ≤ 20 %, rouge ≤ 5 %) et l'en-tête global garde une alerte
sous 100 requêtes restantes.

### 5. Verrou distribué du worker
`run_forever` démarre dans chaque réplique : deux instances peuvent exécuter
la même passe (et la même fusion) en parallèle. Verrou Redis `SET NX EX`
(dépendance déjà optionnelle, repli mémoire mono-instance) avant `run_once`.
*Fichiers : `app/worker.py`, `app/core/cache.py`. Effort : M.*

### 6. Résilience du worker : backoff, jitter, watchdog
La boucle dort un intervalle fixe et retente immédiatement après un échec,
sans jitter ni indicateur de vivacité. Backoff exponentiel plafonné avec
jitter, et `repoflow_worker_last_success_timestamp` exposé dans `/api/metrics`
(plus une sonde de stagnation dans `ready`).
*Fichiers : `app/worker.py`, `app/core/metrics.py`, `routes/health.py`. Effort : M.*

### 7. Rétention et agrégation des snapshots
`daily_snapshots` croît sans limite (une ligne par dépôt et par jour), sans
équivalent de `REPOFLOW_AUDIT_RETENTION_DAYS`. Ajouter une rétention
configurable et des rollups semaine/mois pour borner la table.
*Fichiers : `services/snapshot_service.py`, `worker.py`, `core/config.py`. Effort : S-M.*

### 8. Logs structurés (JSON) et suivi d'erreurs
La journalisation est textuelle alors que `request_id`/`route`/`status`
existent déjà dans le contexte. Mode JSON optionnel (une ligne = un événement)
et branchement facultatif Sentry/GlitchTip côté backend **et** frontend
(`ErrorBoundary` déjà en place pour capturer).
*Fichiers : `core/logging.py`, `core/request_context.py`, `frontend`. Effort : M.*

### 9. Contrôles de sécurité en CI
Aucun job de sécurité : ajouter `pip-audit`/`npm audit` (dépendances), Bandit
ou Semgrep (SAST) et Trivy (scan des images Docker), au moins sur `main`.
*Fichier : `.github/workflows/ci.yml`. Effort : M.*

### 10. Webhooks GitHub en complément du polling
Le worker interroge périodiquement l'API : latence événement → décision et
consommation de quota. Point d'entrée webhook (signature HMAC `X-Hub-Signature-256`
vérifiée, secret en config) déclenchant une passe ciblée, le polling restant
en filet de sécurité.
*Fichiers : nouvelles routes `webhooks.py`, `services/analysis_service.py`,
doc `github-integration`. Effort : L.*

## P2 — Moyen terme (structurants)

### 11. ~~GraphQL pour les issues et le détail des PR~~ ✅
Réalisé : la liste des issues interroge les dépôts **par lots d'alias**
(`ISSUES_BATCH_CHUNK = 10` dépôts par document, pagination en tours) — une
passe sur 62 dépôts consomme ~7 requêtes au lieu de 62 REST, et la connexion
GraphQL n'inclut jamais les pull requests. Le détail d'une PR passe aussi en
GraphQL : une requête agrégée (corps, checks, revues, fichiers,
`timelineItems`) remplace 5-6 requêtes REST. Requêtes validées contre l'API
réelle ; le chemin REST reste disponible (`REPOFLOW_GITHUB_USE_GRAPHQL=false`).

### 12. Checks requis réels (protections de branche)
`merge_rules` suppose que tous les checks sont requis faute de lire les
protections : risque de bloquer (ou laisser passer) à tort. Lire
`GET /repos/{o}/{r}/branches/{b}/protection`, n'exiger que les contextes
réellement requis, repli prudent si l'accès est refusé.
*Fichiers : `integrations/github/`, `services/merge_rules.py`. Effort : M-L.*

### 13. Image frontend de production
Le conteneur frontend lance `npm run dev` (Vite dev) : inadapté en production.
Build multi-étapes servi par nginx (cache long sur les assets, compression,
en-têtes de sécurité), healthcheck conservé.
*Fichiers : `frontend/Dockerfile`, `docker-compose.yml`. Effort : M.*

### 14. Validation des formulaires par schéma
Les formulaires valident « à la main », sans reflet exact des schémas
Pydantic. Introduire `zod` aligné sur `src/types/api.ts`, messages via l'i18n.
*Fichiers : `frontend/src/pages`, `src/types/api.ts`. Effort : S-M.*

### 15. Tests de charge
Mesurer dashboard, listes PR/issues et audit (k6 ou Locust, fournisseur demo)
pour objectiver le cache et détecter les régressions de latence.
*Fichiers : `perf/` ou `backend/tests`. Effort : M.*

### 16. Listes longues : pagination serveur côté UI
PR/issues accumulent les pages côté client via « Charger plus » (389 issues
en mémoire) ; le compteur de filtre reste local. Paginer côté UI (pages
numérotées réutilisant `offset`) et/ou virtualiser si les volumes croissent.
*Fichiers : `frontend/src/pages/IssuesPage.tsx`, `PullRequestsPage.tsx`. Effort : S.*

## P3 — Long terme

### 17. Mises à jour temps réel (SSE)
Flux `/api/v1/events/stream` alimenté par le worker ; le rafraîchissement
automatique couvre le besoin à ce jour. *Effort : L.*

### 18. Notifications
Prévenir sur fusion réussie, PR bloquée, échec du worker, quota GitHub bas ou
arrêt d'urgence engagé (webhook sortant, Slack, e-mail), désabonnement par
canal. *Fichiers : `worker.py`, `analysis_service.py`, config. Effort : M.*

### 19. Analytics produit à partir des snapshots
Dépasser les sparklines : temps de fusion médian, taux d'échec des checks,
MTTR, page « tendances ». *Fichiers : `snapshot_service.py`, frontend. Effort : M.*

### 20. PostgreSQL pour la production
SQLite convient au mono-poste ; si multi-utilisateurs (piste 1) ou forte
activité worker, activer le profil `postgres` existant et documenter la
migration Alembic. *Fichiers : `docker-compose.yml`, doc. Effort : M.*

### 21. Multi-utilisateurs / vues sauvegardées
Dépend de la piste 1 : espaces d'équipe, vues de filtres enregistrées
réutilisant les filtres d'URL. *Effort : L.*

### 22. Tracing distribué (OpenTelemetry)
`X-Request-ID` assure la corrélation des logs ; étendre au tracing (span par
requête, appel provider, passe worker) si le besoin d'observabilité augmente.
*Effort : L.*

## Réalisé depuis la précédente analyse (ne pas retravailler)

- **Sécurité/ops** : jeton porteur `REPOFLOW_API_TOKEN` + middleware, sondes
  `/api/health/live` et `/api/health/ready` (503 si non-prêt), healthchecks
  compose `depends_on: service_healthy` (y compris correctif IPv4 `127.0.0.1`).
- **Observabilité** : métriques métier (`repoflow_merges_total`,
  `worker_runs_total`, `provider_requests_total`, `cache_events_total`),
  histogrammes de latence p95/p99.
- **Données** : export audit CSV/JSON, persistance SQLite dans `./data`
  (bind mount, propriété uid 1001), passthrough compose complet des variables
  GitHub (GraphQL, App, timeouts, cache).
- **Collecte** : fan-out parallèle borné (`REPOFLOW_GITHUB_MAX_CONCURRENCY`)
  avec budget par dépôt (`_COLLECTION_TIMEOUT`), isolation des erreurs réseau,
  propagation des erreurs applicatives ; requête GraphQL alignée sur le
  schéma actuel de GitHub ; **exclusion des dépôts archivés** (référentiel,
  PR, issues, compteurs).
- **Interface** : activités récentes cliquables vers les PR, compteurs
  dépôts → PR/issues du dépôt, lien « Voir sur GitHub » (nouvel onglet) sur le
  détail PR, corps Markdown GFM + HTML sanitisé (`rehype-raw` +
  `rehype-sanitize`) pour PR, revues et issues.
- **Qualité** : tests d'accessibilité axe-core, hygiène dépôt (LICENSE,
  CHANGELOG, `.editorconfig`, pre-commit), seuils CI cohérents, correctif
  timezone des tests de snapshots, E2E en CI.

## Dettes connues et limites documentées

- Rate limiting à fenêtre fixe, désactivé par défaut (piste 3).
- GraphQL opt-in : issues et détail PR restent en REST (piste 11).
- Worker désactivé par défaut ; pas de seed de snapshots en mode démo.
- Fusion automatique désactivée par défaut (garde-fou volontaire).
- Le HTML non autorisé par la liste blanche est supprimé silencieusement
  (comportement identique à GitHub).
