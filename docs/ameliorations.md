# Pistes d'amélioration — RepoFlow

Analyse du 11/10/2026 (branche `develop`, commit `fa5fbbd`).

Les pistes 1 à 28 sont réalisées ; seules 12 (temps réel) et 13
(virtualisation) restent différées et sont reprises plus bas. Cette nouvelle
série recense les manques encore ouverts, classés par priorité et par rapport
valeur/effort (S < 1 j, M 1-3 j, L > 3 j).

À date : backend 235 tests (couverture 93,55 %), frontend 104 tests + 4 E2E,
CI lint + tests + migrations + build Docker, Dependabot actif.

## P0 — Sécurité (à traiter en priorité)

### 29. Authentification et contrôle d'accès ✅
RepoFlow n'a **aucune authentification** : interroger l'API ou agir sur les
routes exposées est possible sans identité. Les routes sensibles sont
publiques — arrêt d'urgence, configs d'automatisation, journal d'audit — alors
que le CORS est ouvert avec `allow_credentials=True`.
Étapes : un jeton porteur (`REPOFLOW_API_TOKEN`, en-tête `Authorization`)
protège déjà l'instance ; ensuite seulement, un compte par utilisateur et un
rôle (lecteur / opérateur / admin) pour restreindre l'arrêt d'urgence et
l'écriture GitHub.
*Fichiers : `backend/app/api/deps.py`, `app/core/config.py`, middleware
d'authentification, `frontend/src/services/apiClient.ts`, `AppLayout`. Effort : L.*

## P1 — Court terme (rapides et à forte valeur)

### 30. Sondes liveness/readiness et healthcheck des services ✅
`backend` et `frontend` n'ont pas de `healthcheck` dans `docker-compose.yml`
(seuls `postgres` et `redis` en ont). `/api/health` vérifie la base mais renvoie
toujours `200` même en `degraded`, et ne distingue pas démarrage de service
prêt. Ajouter `/api/health/live` (processus vivant) et `/api/health/ready`
(base + cache + provider), un code `503` quand non-prêt, et les healthchecks
`depends_on: condition: service_healthy`.
*Fichiers : `backend/app/api/v1/routes/health.py`, `docker-compose.yml`. Effort : S.*

### 31. Métriques métier (pas seulement HTTP) ✅
`app/core/metrics.py` n'expose que des compteurs HTTP. Aucune visibilité sur
l'activité réelle : fusions tentées/réussies/échouées, passes du worker,
appels provider (rest/graphql), évictions cache, anomalies GitHub. Ajouter des
compteurs `repoflow_merges_total`, `repoflow_worker_runs_total`,
`repoflow_provider_requests_total`, `repoflow_cache_events_total`.
*Fichiers : `core/metrics.py`, `services/analysis_service.py`, `worker.py`,
`core/cache.py`. Effort : S-M.*

### 32. Histogrammes de latence ✅
La durée des requêtes est un simple couple somme/compteur (type `summary` sans
quantiles) : aucune latence p95/p99 n'est calculable côté Prometheus. Passer à
un histogramme à buckets (`repoflow_http_request_duration_seconds_bucket`).
*Fichier : `backend/app/core/metrics.py`. Effort : S.*

### 33. Export du journal d'audit ✅
`GET /api/v1/audit` est paginé, mais rien ne permet de sortir les entrées pour
un audit externe. Ajouter un export CSV/JSON (mêmes filtres que l'UI) avec
`Content-Disposition`, et un bouton côté interface.
*Fichiers : `routes/audit.py`, `services/audit_service.py`,
`frontend/src/pages/HistoryPage.tsx`. Effort : S.*

### 34. Thème par défaut selon `prefers-color-scheme` ✅
Le thème sombre est figé au premier lancement ; seul le basculement manuel est
persisté. Initialiser le thème depuis la préférence système avant le premier
rendu (pour éviter le flash), le choix manuel restant prioritaire.
*Fichiers : `frontend/src/index.css`, hook de thème, `layouts/AppLayout.tsx`.
Effort : S.*

### 35. Tests d'accessibilité automatisés ✅
L'effort P3.28 a corrigé les contrastes, mais rien ne garantit qu'une
régression ne réintroduira pas un défaut. Ajouter `axe-core` sur les pages
principales (Vitest) et/ou `@axe-core/playwright` dans le parcours E2E.
*Fichiers : `frontend/src/**/*.test.tsx`, `frontend/e2e/app.spec.ts`. Effort : S.*

### 36. Hygiène du dépôt ✅
Manquent : fichier `LICENSE` (la licence MIT est annoncée « à venir » dans le
README), `CHANGELOG.md`, tags/notes de version, `.editorconfig`, et des hooks
pre-commit (Ruff, ESLint, détection de secrets). Le README mentionne aussi le
worker « à venir » alors qu'il est exploitable (`python -m app.worker`).
*Fichiers : racine, `README.md`, `CONTRIBUTING.md`, `backend/pyproject.toml`.
Effort : S.*

### 37. Seuil de couverture incohérent dans la CI ✅
Le commentaire du job frontend annonce « seuil 85 % » alors que
`frontend/vite.config.ts` applique lignes 80 % / branches 65 %. Aligner le
libellé (ou relever réellement le seuil : 88 % / 79 % atteints).
*Fichier : `.github/workflows/ci.yml`. Effort : S.*

## P2 — Moyen terme (structurants)

### 38. Verrou distribué du worker
`run_forever` démarre dans **chaque** réplique : avec plusieurs instances, la
même passe d'analyse (et donc la même fusion) peut s'exécuter en parallèle.
Prendre un verrou distribué (Redis `SET NX EX`, même dépendance que le rate
limiter, repli mémoire mono-instance) avant `run_once`.
*Fichiers : `backend/app/worker.py`, `core/cache.py`/`security.py`. Effort : M.*

### 39. Tolérance du worker : backoff, jitter, watchdog
La boucle dort un intervalle fixe et retente immédiatement après un échec, sans
jitter (risque de synchronisation entre répliques) ni métrique de vivacité.
Ajouter un backoff exponentiel plafonné avec jitter, et exposer l'heure de
dernière passe réussie (`repoflow_worker_last_success_timestamp`).
*Fichier : `backend/app/worker.py`. Effort : M.*

### 40. Rétention et agrégation des snapshots
`daily_snapshots` croît indéfiniment (une ligne par dépôt et par jour) sans
équivalent de `REPOFLOW_AUDIT_RETENTION_DAYS`. Ajouter une rétention
configurable et/ou des rollups (semaine/mois) pour borner la table.
*Fichiers : `services/snapshot_service.py`, `worker.py`, `core/config.py`.
Effort : S-M.*

### 41. Logs structurés et suivi d'erreurs
La journalisation est textuelle. Ajouter un mode JSON optionnel (une ligne =
un événement, champs `request_id`/`route`/`status` déjà disponibles via le
contexte de requête) et un branchement optionnel vers un collecteur d'erreurs
(Sentry/GlitchTip) côté backend et frontend.
*Fichiers : `core/logging.py`, `core/request_context.py`, `frontend`. Effort : M.*

### 42. SAST, audit de dépendances et scan d'images en CI
La CI n'exécute aucun contrôle de sécurité : ni analyse statique (Bandit /
Semgrep), ni audit de dépendances (`pip-audit`, `npm audit`), ni scan des images
Docker (Trivy). Ajouter ces jobs (au minimum sur `main`).
*Fichier : `.github/workflows/ci.yml`. Effort : M.*

### 43. Checks requis : lire les protections de branche
`integrations/github/mapping.py:6` suppose que **tous** les checks sont
obligatoires faute d'accès aux protections. La règle de fusion peut donc
bloquer (ou laisser passer) à tort. Lire la protection de branche via l'API
(`GET /repos/{o}/{r}/branches/{b}/protection`) et n'exiger que les contextes
réellement requis, avec repli sur le comportement prudent actuel.
*Fichiers : `integrations/github/provider.py`, `services/merge_rules.py`. Effort : M-L.*

### 44. Webhooks GitHub en complément du polling
Le worker interroge périodiquement l'API : latence entre l'événement et la
décision, et consommation de quota. Ajouter un point d'entrée webhook
(signature HMAC vérifiée) qui déclenche une passe ciblée, en conservant le
polling comme filet de sécurité.
*Fichiers : nouvelles routes, `services/analysis_service.py`, doc
`github-integration.md`. Effort : L.*

### 45. Validation de formulaires par schéma
Les formulaires frontend valident « à la main » (règles dispersées), sans
reflet exact des schémas Pydantic. Introduire une validation par schéma
(ex. `zod`) alignée sur les types API et afficher les messages via l'i18n.
*Fichiers : `frontend/src/pages`, `frontend/src/types/api.ts`. Effort : S-M.*

### 46. Image frontend de production
Le `frontend/Dockerfile` lance le serveur de développement Vite (`npm run
dev`) : inadapté à la production (source maps, pas de cache long, pas de
compression). Ajouter un build multi-étapes servi statiquement (nginx/Caddy)
avec en-têtes de cache et `healthcheck`.
*Fichiers : `frontend/Dockerfile`, `docker-compose.yml`. Effort : M.*

### 47. Tests de charge
Aucun test de performance/montée en charge. Mesurer listes PR/issues, dashboard
et endpoints d'audit (k6 ou Locust, fournisseur demo) pour objectiver les
optimisations de cache et détecter les régressions.
*Fichiers : `backend/tests` ou `perf/`. Effort : M.*

## P3 — Long terme

### 48. Mises à jour temps réel (SSE) — différé
Reprise de la piste 12 : flux d'événements (`/api/v1/events/stream`) alimenté
par le worker. Le rafraîchissement automatique (P1.5) couvre encore le besoin.
*Effort : L.*

### 49. Virtualisation des longues listes — à évaluer
Reprise de la piste 13 : `@tanstack/react-virtual` si les volumes grandissent.
*Effort : S.*

### 50. Analytics produit à partir des snapshots
Les snapshots ne stockent que des compteurs. Calculer des indicateurs de
tendance (temps de fusion médian, taux d'échec des checks, MTTR) pour nourrir
une page « tendances » au-delà des sparklines actuelles.
*Fichiers : `services/snapshot_service.py`, `frontend`. Effort : M.*

### 51. Notifications
Prévenir sur fusion réussie, PR bloquée, échec du worker ou arrêt d'urgence
engagé (webhook sortant, e-mail ou Slack), avec désabonnement par canal.
*Fichiers : `worker.py`, `services/analysis_service.py`, config. Effort : M.*

### 52. Multi-utilisateurs / vues sauvegardées
Dépend de la piste 29 : comptes, espaces d'équipe et vues de filtres
enregistrées, réutilisant les filtres persistés dans l'URL.
*Effort : L.*

### 53. Tracing distribué (OpenTelemetry)
Le `X-Request-ID` assure déjà la corrélation des logs. Étendre au tracing
(span par requête, appel provider, passe worker) si le besoin d'observabilité
augmente.
*Fichiers : `core/request_context.py`, intégrations. Effort : L.*

### 54. Partitionnement des snapshots
Si `daily_snapshots` devient volumineuse, partitionner par mois ou basculer
sur `pg_partman`, en complément de la rétention (piste 40).
*Effort : M.*

## Déjà couvert (ne pas retravailler)
- ETag, `Retry-After`, single-flight, cache mémoire/Redis, rate limiting
  mémoire/Redis, `X-Request-ID`, métriques HTTP, en-têtes de sécurité.
- i18n fr/en backend (y compris messages d'audit reconstruits à l'affichage)
  et frontend, thème clair, recherche serveur, pagination PR/issues/audit.
- GraphQL opt-in, token GitHub App, historique `daily_snapshots` et sparklines,
  code splitting, `ErrorBoundary`, tests E2E et tests du worker.

## Dettes connues et limites documentées
- Rate limiting à fenêtre fixe (Redis dépendance optionnelle).
- GraphQL opt-in : détail PR et fusion restent en REST.
- Worker désactivé par défaut ; aucun seed de snapshots en mode demo.
- Pas d'authentification (piste 29, la plus structurante).
