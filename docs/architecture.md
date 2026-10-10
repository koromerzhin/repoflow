# Architecture de RepoFlow

## Vue d'ensemble

RepoFlow est un **monolithe modulaire** : une seule application backend
déployable, découpée en couches aux frontières explicites, complétée par une
application frontend React. Ce choix évite la complexité des microservices
tout en gardant des responsabilités clairement séparées et testables.

```
Navigateur ──HTTP──▶ Frontend React (Vite) ──/api──▶ Backend FastAPI
                                                       │
                          ┌────────────────────────────┼───────────────────────────┐
                          │                            │                           │
                     Couche API                  Couche services             Intégration
                   (routes HTTP)               (règles métier)             (fournisseur GitHub)
                          │                            │                           │
                          └──────────────┬─────────────┴─────────────┬─────────────┘
                                         │                           │
                                   Schémas Pydantic            Accès base (SQLAlchemy)
```

## Backend

| Répertoire | Responsabilité |
| --- | --- |
| `app/api/` | Routes HTTP et dépendances FastAPI. Aucune logique métier. |
| `app/api/v1/routes/` | Endpoints versionnés (`dashboard`, `repositories`, `pull-requests`, `pull-requests/{number}`, `issues`) et `health`. |
| `app/core/` | Configuration, logging, gestion des erreurs, cache TTL mémoire. |
| `app/db/` | Moteur, sessions et initialisation de la base. |
| `app/models/` | Modèles ORM SQLAlchemy 2.x. |
| `app/schemas/` | Modèles Pydantic de validation et de réponse. |
| `app/services/` | Règles métier : agrégation des checks, éligibilité de fusion, tableau de bord. |
| `app/integrations/github/` | Intégration GitHub derrière une interface abstraite. |

### Flux de données

1. La route appelle un **service** via une dépendance FastAPI.
2. Le service interroge le **fournisseur** (`Provider`) pour obtenir des
   enregistrements de domaine (`RepositoryRecord`, `PullRequestRecord`,
   `IssueRecord`), les résultats étant mis en cache mémoire avec un TTL
   configurable (`REPOFLOW_CACHE_TTL_SECONDS`, contournable via `?refresh=true`).
3. Le service applique les **règles métier** (`merge_rules`) et convertit les
   enregistrements en **schémas d'API**.
4. La route sérialise la réponse.

Cette séparation garantit que remplacer le fournisseur de démonstration par
le fournisseur GitHub réel n'impacte ni les services ni les routes.

### Règles métier clés

- `aggregate_checks_state` : un seul échec ⇒ `failure` ; sinon un `pending` ⇒
  `pending` ; sinon un `unknown` ⇒ `unknown` ; uniquement des succès ⇒ `success`.
- `evaluate_merge_eligibility` : évaluation **en lecture seule**. Une PR en
  brouillon, non approuvée, en conflit, non ouverte, ou dont un check
  obligatoire n'est pas réussi est bloquée. **Un check inconnu n'est jamais
  considéré comme réussi.**

## Frontend

| Répertoire | Responsabilité |
| --- | --- |
| `src/layouts/` | Gabarit applicatif (barre latérale, en-tête, bandeau mode démo). |
| `src/pages/` | Pages routées. |
| `src/components/` | Composants réutilisables (badges, états, cartes). |
| `src/services/` | Client HTTP centralisé. |
| `src/hooks/` | Hooks transverses (chargement asynchrone). |
| `src/lib/` | Libellés français, classes de statut, formatage. |
| `src/types/` | Types TypeScript calqués sur les schémas Pydantic. |

L'interface est en français, en thème sombre, responsive, et distingue
systématiquement les états de **chargement**, d'**erreur**, de **liste vide**
et de **contenu**.

## Base de données

- SQLite en développement et pour la première version.
- Migrations gérées par **Alembic** (`backend/alembic/`).
- Tables : `repository_configs`, `automation_rules`, `audit_events`.
- En développement, `REPOFLOW_AUTO_CREATE_TABLES=true` crée les tables au
  démarrage ; en production, exécuter `alembic upgrade head`.

Les données GitHub (issues, PR, checks) ne sont **pas** persistées dans cette
première version : elles sont servies à la demande par le fournisseur.

## Évolutions prévues

- **Worker d'analyse périodique** : service séparé réutilisant l'image
  backend, chargé de scruter les dépôts et d'évaluer les règles de fusion.
- **Fusion automatique** : jamais activée par défaut, toujours contrôlée côté
  serveur, avec historique d'audit.
- **Webhooks GitHub** : ingestion d'événements en temps réel.
