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
| `app/api/v1/routes/` | Endpoints versionnés (`dashboard`, `repositories`, `pull-requests`, `pull-requests/{number}`, `issues`, `configs`, `automation`, `audit`) et `health`. |
| `app/core/` | Configuration, logging, gestion des erreurs, cache TTL mémoire. |
| `app/db/` | Moteur, sessions et initialisation de la base. |
| `app/models/` | Modèles ORM SQLAlchemy 2.x. |
| `app/schemas/` | Modèles Pydantic de validation et de réponse. |
| `app/services/` | Règles métier : agrégation des checks, éligibilité de fusion, tableau de bord, configuration, analyse, audit, garde-fous système. |
| `app/integrations/github/` | Intégration GitHub derrière une interface abstraite. |
| `app/worker.py` | Worker d'analyse périodique (intégré à l'API ou en processus séparé). |

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
  considéré comme réussi.** Le nombre d'approbations requis et l'exigence de
  checks verts sont paramétrables par règle.
- `analysis_service` : évalue les règles et, si et seulement si toutes les
  conditions sont réunies, déclenche une fusion `squash`. La décision suit un
  ordre strict : arrêt d'urgence → autorisation globale → règle.
- `config_service` : CRUD des dépôts suivis et des règles, avec validation
  stricte des entrées (le client n'est jamais source de vérité).
- `audit_service` : journal immuable des analyses et décisions.

### Analyse et fusion contrôlée

Le worker (`app/worker.py`) exécute périodiquement `run_analysis`. Pour chaque
dépôt suivi et activé :

1. les pull requests ouvertes sont récupérées puis filtrées par la règle qui
   correspond à leur branche cible ;
2. chaque PR est évaluée (`evaluate_pr_for_rule`) : éligibilité, approbations,
   checks, et **branche cible = branche par défaut** du dépôt ;
3. une fusion `squash` n'est tentée que si la règle et l'autorisation globale
   sont actives et que l'arrêt d'urgence est désengagé ;
4. chaque décision (fusion, blocage, report, erreur) est journalisée.

Sans configuration explicite, **aucune fusion n'a lieu** : le comportement par
défaut est sûr.

## Frontend

| Répertoire | Responsabilité |
| --- | --- |
| `src/layouts/` | Gabarit applicatif (barre latérale, en-tête, bandeau mode démo). |
| `src/pages/` | Pages routées. |
| `src/components/` | Composants réutilisables (badges, états, cartes). |
| `src/services/` | Client HTTP centralisé. |
| `src/hooks/` | Hooks transverses (chargement asynchrone). |
| `src/lib/` | Clés de libellés, classes de statut, formatage des dates. |
| `src/i18n/` | Internationalisation (locales `fr` / `en`, initialisation i18next). |
| `src/types/` | Types TypeScript calqués sur les schémas Pydantic. |

L'interface est **bilingue français / anglais**, en thème sombre, responsive,
et distingue systématiquement les états de **chargement**, d'**erreur**, de
**liste vide** et de **contenu**.

### Internationalisation

- Initialisation dans `src/i18n/index.ts` (i18next + react-i18next +
  `i18next-browser-languagedetector`) : détection via `?lang=`, puis
  `localStorage`, puis langue du navigateur ; repli sur le français.
- Locales dans `src/i18n/locales/{fr,en}.ts` ; les libellés de `src/lib/`
  référencent des clés (`status.check.success`, …) traduites à l'affichage.
- La langue choisie est persistée (`localStorage`) et bascule via le
  sélecteur d'en-tête ; les dates sont formatées selon la langue.
- Côté backend, les messages (erreurs, bloqueurs de fusion) suivent
  l'en-tête `Accept-Language`.
- Les tests forcent le français (`beforeAll` dans `src/test/setup.ts`).

## Base de données

- SQLite en développement ; **PostgreSQL** possible en production
  (`pip install -e ".[postgres]"` et `REPOFLOW_DATABASE_URL` en
  `postgresql+psycopg://…`).
- Migrations gérées par **Alembic** (`backend/alembic/`).
- Tables : `repository_configs`, `automation_rules`, `audit_events`,
  `system_settings`.
- Le moteur SQLAlchemy ajuste ses options selon le dialecte : SQLite
  (`check_same_thread=False`), autres bases (`pool_pre_ping`, taille de pool
  configurables via `REPOFLOW_DB_POOL_*`).
- En développement, `REPOFLOW_AUTO_CREATE_TABLES=true` crée les tables au
  démarrage ; en production, exécuter `alembic upgrade head`.

Les données GitHub (issues, PR, checks) ne sont **pas** persistées : elles sont
servies à la demande par le fournisseur. Seules la configuration, l'état des
automatisations et le journal d'audit sont stockés.

## Couches transverses (observabilité et sécurité)

Les middlewares FastAPI sont empilés (du plus interne au plus externe) :

1. **Limitation de débit** (`app/core/security.py`) — fenêtre fixe en mémoire,
   clé = adresse IP. Désactivée par défaut ; réponse `429` au-delà du seuil.
2. **En-têtes de sécurité** (`app/core/security.py`) — `X-Content-Type-Options`,
   `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, COOP/CORP, CSP
   sur les chemins `/api`, HSTS en contexte HTTPS uniquement.
3. **Métriques** (`app/core/metrics.py`) — registre autonome, exposition
   Prometheus sur `GET /api/metrics` (libellés par méthode, route et statut ;
   les segments dynamiques sont normalisés via le modèle de route).
4. **Contexte de requête** (`app/core/request_context.py`) — identifiant de
   corrélation `X-Request-ID` (repris du client ou généré, sanitizé), propagé
   dans les journaux par `RequestIdFilter`, renvoyé au client ; journal
   d'accès structuré (`méthode chemin → statut (durée)`).
5. **CORS** (le plus externe) — les réponses d'erreur et de rejet reçoivent
   aussi les en-têtes CORS.

À l'exception de la limitation de débit (mémoire, par processus), ces couches
sont sans état et conveniennent à une mise à l'échelle horizontale.

## Évolutions prévues

- **Webhooks GitHub** : ingestion d'événements en temps réel en complément du
  worker périodique.
- **Stockage partagé du limiteur de débit** (Redis) pour une mise à l'échelle
  multi-processus.
