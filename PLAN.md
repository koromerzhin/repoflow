# PLAN.md — feuille de route RepoFlow

Feuille de route priorisée. `[x]` = fait, `[ ]` = à faire.

## Phase 0 — Socle initial (v0.1) ✅

- [x] Architecture modulaire (api / services / integrations / schemas / models / core).
- [x] Application FastAPI démarrable + logging + gestion d'erreurs + config par variables d'environnement.
- [x] Routes : `GET /api/health`, `GET /api/v1/dashboard`, `GET /api/v1/repositories`, `GET /api/v1/pull-requests`.
- [x] Schémas Pydantic explicites pour chaque réponse.
- [x] Modèles SQLAlchemy + base SQLite + migration Alembic initiale.
- [x] Intégration abstraite `Provider` + fournisseur de démonstration + emplacement réservé GitHub.
- [x] Règles métier d'agrégation des checks et d'éligibilité de fusion (lecture seule).
- [x] Tests backend Pytest (routes + règles métier + provider).
- [x] Frontend React + TypeScript strict + Vite + Tailwind + React Router.
- [x] Interface : menu latéral, tableau de bord, dépôts, pull requests, états de chargement/erreur/vide, pages « À venir ».
- [x] Client HTTP centralisé + types TypeScript.
- [x] Tests frontend Vitest + Testing Library.
- [x] Documentation (README, AGENTS, docs/architecture, docs/github-integration).
- [x] Docker Compose (backend + frontend) et `.env.example`.
- [x] CI GitHub Actions (backend + frontend).

## Phase 1 — Connexion GitHub réelle (priorité haute) ✅

- [x] Choisir et documenter le mode d'authentification (GitHub App recommandée ; jeton PAT/installation accepté).
- [x] Implémenter `GithubProvider` : `list_repositories`, `list_pull_requests`.
- [x] Client HTTP GitHub avec pagination (`Link`) et gestion du rate limit.
- [x] Normalisation des erreurs GitHub (`ProviderError`).
- [x] Ne jamais journaliser ni exposer le token (en-tête uniquement, loggers httpx/httpcore silencieux).
- [x] Tests avec réponses GitHub simulées (aucun appel réseau réel en CI).
- [x] Résolution des checks via l'API Checks / commit statuses.

## Phase 2 — Issues et détails ✅

- [x] Endpoint `GET /api/v1/issues` + filtres par dépôt et par état.
- [x] Page Issues côté frontend.
- [x] Détail d'une pull request (fichiers, revues, timeline) :
      `GET /api/v1/pull-requests/{number}` + page frontend dédiée.
- [x] Mise en cache TTL côté serveur et rafraîchissement manuel (`?refresh=true`,
      boutons « Rafraîchir »).

## Phase 3 — Configuration des règles d'automatisation (priorité haute) ✅

- [x] CRUD des dépôts suivis (`repository_configs`).
- [x] CRUD des règles (`automation_rules`) par dépôt et par branche.
- [x] Interface de configuration des règles (page Automatisations).
- [x] Validation stricte côté serveur (jamais côté client uniquement).

## Phase 4 — Worker d'analyse et fusion contrôlée ✅

- [x] Service worker séparé (même image backend) pour l'analyse périodique.
- [x] Évaluation des règles d'éligibilité à fusion.
- [x] Fusion `squash` **contrôlée côté serveur**, **désactivée par défaut**.
- [x] Refuser : brouillon, conflits, checks non réussis, approbations
      manquantes, restrictions de branche.
- [x] Aucun contournement administrateur des protections de branche.
- [x] Arrêt d'urgence global opérationnel.
- [x] Historique d'audit persistant et consultable (page Historique).

## Phase 5 — Qualité et exploitation (priorité moyenne) ✅

- [x] Couverture de tests ciblée (seuils) : backend `--cov-fail-under=90`,
      frontend `test:coverage` (lignes 80, fonctions 70, branches 65),
      vérifiés en CI.
- [x] Observabilité : métriques Prometheus (`/api/metrics`), identifiant de
      corrélation par requête (`X-Request-ID`) dans les journaux.
- [x] Support PostgreSQL en plus de SQLite (`pip install -e ".[postgres]"`,
      options de pool configurables, service Compose optionnel).
- [x] Durcissement sécurité (en-têtes HTTP, limitation de débit par IP).
- [x] Documentation utilisateur (`docs/user-guide.md`) et guide de contribution
      (`CONTRIBUTING.md`).

## Dettes techniques connues

- La limitation de débit est en mémoire (fenêtre fixe par processus) ; une
  mise en échelle multi-processus requerrait un stockage partagé (Redis).
- Le système de métriques est autonome et minimal (compteurs + durées) ; les
  *histogrammes* Prometheus pourront être ajoutés si besoin.
- `AUTO_CREATE_TABLES` est activé par défaut en développement ; en production,
  utiliser `alembic upgrade head`.
- Le fournisseur GitHub interroge le détail de chaque PR (une optimisation
  GraphQL réduirait le nombre de requêtes).
- Le chemin d'écriture GitHub se limite à la fusion `squash` (aucune autre
  action d'écriture n'est exposée).
- L'échange clé privée → jeton d'installation (GitHub App) n'est pas encore
  implémenté : fournir un jeton prêt à l'emploi.
- La liste « prête à fusionner » du tableau de bord est une **évaluation
  indicative** sans exécution.
