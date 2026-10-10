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

## Phase 1 — Connexion GitHub réelle (priorité haute)

- [ ] Choisir et documenter le mode d'authentification (GitHub App recommandée).
- [ ] Implémenter `GithubProvider` : `list_repositories`, `list_pull_requests`.
- [ ] Client HTTP GitHub avec pagination (`Link`) et gestion du rate limit.
- [ ] Normalisation des erreurs GitHub (`ProviderError`).
- [ ] Ne jamais journaliser ni exposer le token.
- [ ] Tests avec réponses GitHub simulées (aucun appel réseau réel en CI).
- [ ] Résolution des checks via l'API Checks / commit statuses.

## Phase 2 — Issues et détails

- [ ] Endpoint `GET /api/v1/issues` + filtres par dépôt et par état.
- [ ] Page Issues côté frontend.
- [ ] Détail d'une pull request (fichiers, revues, timeline).
- [ ] Mise en cache et rafraîchissement manuel.

## Phase 3 — Configuration des règles d'automatisation (priorité haute)

- [ ] CRUD des dépôts suivis (`repository_configs`).
- [ ] CRUD des règles (`automation_rules`) par dépôt et par branche.
- [ ] Interface de configuration des règles (page Automatisations).
- [ ] Validation stricte côté serveur (jamais côté client uniquement).

## Phase 4 — Worker d'analyse et fusion contrôlée

- [ ] Service worker séparé (même image backend) pour l'analyse périodique.
- [ ] Évaluation des règles d'éligibilité à fusion.
- [ ] Fusion `squash` **contrôlée côté serveur**, **désactivée par défaut**.
- [ ] Refuser : brouillon, conflits, checks non réussis, approbations
      manquantes, restrictions de branche.
- [ ] Aucun contournement administrateur des protections de branche.
- [ ] Arrêt d'urgence global opérationnel.
- [ ] Historique d'audit persistant et consultable (page Historique).

## Phase 5 — Qualité et exploitation (priorité moyenne)

- [ ] Couverture de tests ciblée (seuils).
- [ ] Observabilité : métriques, identifiant de corrélation par requête.
- [ ] Support PostgreSQL en plus de SQLite.
- [ ] Durcissement sécurité (en-têtes HTTP, limitations de débit).
- [ ] Documentation utilisateur et guide de contribution.

## Dettes techniques connues

- `AUTO_CREATE_TABLES` est activé par défaut en développement ; en production,
  utiliser `alembic upgrade head`.
- Le fournisseur GitHub réel est un emplacement réservé qui répond `503`.
- La liste « prête à fusionner » du tableau de bord est une **évaluation
  indicative** sans exécution.
