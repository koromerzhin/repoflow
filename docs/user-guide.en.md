# Guide utilisateur — RepoFlow

This guide explains how to use RepoFlow pour analyser les pull requests GitHub, prioriser le travail et configurer l'automatisation de manière sûre.

## Présentation

RepoFlow surveille vos dépôts, calcule un score de priorisation, met en évidence les blocages et propose une automatisation explicite (jamais automatique par défaut). Tout est consultable via une interface web bilingue (français/anglais).

## Getting started

1. Copier `.env.example` vers `.env` et ajuster les variables (provider GitHub/demo, CORS, etc.)
2. Lancer avec Docker Compose : `docker compose up --build` → Frontend http://localhost:5173, API http://localhost:8000
3. Se connecter (si `REPOFLOW_API_TOKEN` est défini) avec le jeton dans l'overlay d'authentification
4. Ajouter au moins un dépôt suivi dans **Automations → Dépôts suivis**

## Dashboard

- **Overview** : PR ouvertes, prêtes à fusionner, en attente de reviews, issues ouvertes
- **Bandeau de démonstration** : visible si `data_source="demo"`
- **Rafraîchissement** : automatique configurable ou manuel (`?refresh=true`, boutons « Rafraîchir »)

## Pull requests

- Liste filtrable (recherche, dépôt, état). Badges : prêtes à fusionner, blocages, checks
- Détail d'une PR : fichiers modifiés, revues, timeline
- Score et critères de décision affichés (lisibilité)

## Issues

- Liste filtrable par dépôt/état, avec libellés/assignés

## Automations

- **Dépôts suivis** : ajouter/supprimer un dépôt surveillé
- **Règles de fusion** : créer/modifier/suspendre/supprimer (par dépôt, optionnellement par branche). Activation explicite de l'auto-merge par règle
- **Arrêt d'urgence** : bascule globale qui suspend **toute** automatisation, quelle que soit la Configuration

> La fusion (mode `squash`) n'est jamais automatique par défaut : elle exige autorisation globale **ET** une règle dédiée, une PR éligible et un arrêt d'urgence désengagé.

## History

Journal d'audit persistant : analyses du worker, décisions, fusions réussies ou bloquées. Filtrable par type d'événement et par dépôt. Export CSV ou JSON disponible.

## Main environment variables

| Variable | Défaut | Description |
| --- | --- | --- |
| `REPOFLOW_ENVIRONMENT` | `development` | Environnement (affecte logs/comportements) |
| `REPOFLOW_GITHUB_PROVIDER` | `demo` | `demo` ou `github_api` |
| `REPOFLOW_GITHUB_TOKEN` | vide | Token GitHub (requis si provider github_api) |
| `REPOFLOW_DATABASE_URL` | SQLite local | URL base de données |
| `REPOFLOW_AUTO_MERGE_ENABLED_GLOBALLY` | `false` | Autorisation globale d'auto-merge |
| `REPOFLOW_WORKER_ENABLED` | `false` | Activer le worker d'analyse |
| `REPOFLOW_WORKER_INTERVAL_SECONDS` | `300` | Intervalle du worker |
| `REPOFLOW_AUDIT_RETENTION_DAYS` | `30` | Rétention audit |
| `REPOFLOW_CORS_ORIGINS` | `http://localhost:5173` | Origines CORS autorisées |
| `REPOFLOW_API_TOKEN` | vide | Si défini, active l'auth Bearer sur `/api/v1/*` |
| `REPOFLOW_KILL_SWITCH_ENGAGED` | `false` | Arrêt d'urgence initial |

## FAQ

- **Pourquoi la fusion n'a pas eu lieu ?** Consulter l'History (blocages listés : brouillon, conflits, checks non réussis, approbations manquantes...).
- **Différence entre arrêt d'urgence et désactivation de règle ?** L'arrêt d'urgence suspend tout immédiatement ; une règle désactivée ne s'applique pas mais l'arrêt d'urgence reste prioritaire.
- **Mode démo vs GitHub ?** Mode démo utilise des données locales (pas d'appels réseau). GitHub nécessite token et permissions minimales.
