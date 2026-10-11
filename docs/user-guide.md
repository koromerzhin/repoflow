# Guide utilisateur RepoFlow

RepoFlow supervise plusieurs dépôts GitHub sans les cloner : issues, pull
requests, checks CI, règles d'automatisation et fusion contrôlée.

## Démarrage rapide

1. **Mode démonstration (par défaut)** : aucune configuration n'est requise.
   Toutes les données affichées sont fictives et signalées par un bandeau
   « Mode démonstration ».
2. **Vraies données GitHub** : démarrer le backend avec
   `REPOFLOW_GITHUB_PROVIDER=github` et un jeton d'API côté serveur
   (`REPOFLOW_GITHUB_TOKEN`). Voir `docs/github-integration.md`.
3. Ouvrir l'interface : http://localhost:5173 (ou la page servie par le
   backend) puis se rendre dans les pages ci-dessous.

## Les pages

### Tableau de bord
Indicateurs globaux (issues ouvertes, pull requests ouvertes, pull requests
« prêtes à fusionner ») et activité récente. Les PR « prêtes à fusionner »
reflètent une **évaluation indicative**, sans exécution.

### Dépôts
Liste des dépôts suivis : branche par défaut, visibilité, compteurs d'issues
et de PR, dernière activité.

### Pull requests
Liste des pull requests filtrée par dépôt. Pour chaque PR : état, décision de
revue, synthèse des checks CI, fichiers modifiés, et **blocages** éventuels
(checks en échec, approbations manquantes, etc.). Un clic sur le titre ouvre
le détail.

### Détail d'une pull request
Fichiers modifiés, revues, timeline complète.

### Issues
Liste des issues (hors pull requests), filtrable par dépôt et par état.

### Automatisations
- **Dépôts suivis** : ajouter ou retirer un dépôt surveillé.
- **Règles de fusion** : créer, modifier, suspendre ou supprimer des règles
  (par dépôt, éventuellement par branche), avec activation/désactivation de la
  fusion automatique pour chaque règle.
- **Arrêt d'urgence** : bascule globale qui suspend **toute** automatisation,
  quelle que soit la configuration.

> La fusion (mode `squash`, hybride *merge* GitHub) n'est jamais automatique
> par défaut : elle exige une autorisation globale **et** une règle dédiée,
> une PR éligible et un arrêt d'urgence désengagé.

### Historique
Journal d'audit persistant : analyses du worker, décisions, fusions réussies
ou bloquées. Filtrable par type d'événement et par dépôt. Export CSV ou JSON disponible.

## Questions fréquentes

- **Pourquoi la fusion n'a-t-elle pas eu lieu ?** Consulter l'historique :
  l'audit conserve chaque décision et son blocage (brouillon, conflits,
  checks non réussis, approbations manquantes, restriction de branche,
  arrêt d'urgence).
- **Comment forcer un rafraîchissement ?** Bouton « Rafraîchir » de chaque
  page (l'équivalent technique : `?refresh=true`).
- **Puis-je voir des métriques ?** Oui, via `GET /api/metrics` (format
  Prometheus) : compteurs et durées par route, avec le contexte d'exécution.
- **Qu'est-ce que l'en-tête `X-Request-ID` ?** L'identifiant de corrélation
  généré par le backend pour chaque requête ; il circule dans les journaux et
  les réponses, pratique pour tracer un problème de bout en bout.

## Exploitation

### Configurations utiles (`.env`, préfixe `REPOFLOW_`)

| Variable | Rôle | Défaut |
| --- | --- | --- |
| `REPOFLOW_DATABASE_URL` | Base de données (SQLite ou PostgreSQL) | SQLite |
| `REPOFLOW_DB_POOL_*` | Taille du pool, `pool_pre_ping` | 5 / 10 / true |
| `REPOFLOW_METRICS_ENABLED` | Exposition des métriques | `true` |
| `REPOFLOW_SECURITY_HEADERS_ENABLED` | En-têtes de sécurité HTTP | `true` |
| `REPOFLOW_HSTS_ENABLED` | Strict-Transport-Security (**HTTPS uniquement**) | `false` |
| `REPOFLOW_RATE_LIMIT_ENABLED` | Limitation de débit par adresse IP | `false` |
| `REPOFLOW_RATE_LIMIT_REQUESTS` | Seuil de requêtes par fenêtre | `120` |
| `REPOFLOW_RATE_LIMIT_WINDOW_SECONDS` | Durée de la fenêtre | `60` |
| `REPOFLOW_RATE_LIMIT_BACKEND` | Backend du compteur (`memory` ou `redis`) | `memory` |

La limitation de débit est **désactivée par défaut**. Derrière un proxy, la
renseigner pour protéger l'API des abus ; sans proxy configuré, la clé est
l'adresse IP du client. Le backend `redis` partage le compteur entre instances
(repli automatique sur la mémoire locale si Redis est injoignable).