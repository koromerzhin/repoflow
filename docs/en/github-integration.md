# Intégration GitHub — RepoFlow

This document describes how to configure RepoFlow avec l'API GitHub (vs demo mode).

## Modes de fonctionnement

- `demo` (défaut) : simulated data, no network calls. Ideal for demos/tests.
- `github` : calls to GitHub API REST/GraphQL GitHub avec token.

## Configuration

1. Créer un Personal Access Token (classic) ou GitHub App (selon besoin)
2. Définir `.env` :
   - `REPOFLOW_GITHUB_PROVIDER=github`
   - `REPOFLOW_GITHUB_TOKEN=ghp_xxx`
3. Redémarrer backend

## Scopes recommandés (PAT classic)

Minimum pour lecture+fusion (squash) :
- `repo` (full) si privé OU `public_repo` si public
- `read:org` si dépôts org
- `pull_requests:write` requis pour fusionner

## Comportements sécurité

- Jamais de fusion si checks échoués/en cours/inconnu
- Jamais de fusion sur PR brouillon
- Jamais de contournement admin des protections
- Fusion vers branche par défaut uniquement
- Mode `squash` par défaut
- Arrêt d'urgence bloque toute fusion

## Limitations/notes

- Respect strict des règles de protection de branche
- Gestion des taux (RateLimit exposé dans `/api/health`)
- En mode démo, les fusions sont simulées et marquées `is_demo`
