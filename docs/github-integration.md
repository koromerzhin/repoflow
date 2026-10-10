# Intégration GitHub

RepoFlow sait fonctionner de deux manières, sélectionnées par
`REPOFLOW_GITHUB_PROVIDER` :

- `demo` (par défaut) : données fictives déterministes, **aucun token requis**.
- `github` : données réelles lues depuis l'API GitHub, **token requis côté
  serveur**.

L'intégration GitHub est **strictement en lecture seule** dans cette version :
aucune écriture (commentaire, label, fusion) n'est effectuée.

## Interface abstraite

Toute l'application dépend du contrat `Provider`
(`app/integrations/github/provider.py`) :

```python
class Provider(Protocol):
    name: str
    is_demo: bool
    requires_token: bool

    async def list_repositories(self) -> list[RepositoryRecord]: ...
    async def list_pull_requests(
        self, repository_full_name: str | None = None
    ) -> list[PullRequestRecord]: ...
```

`DemoProvider` et `GithubProvider` implémentent ce contrat. La sélection se
fait dans `app/integrations/github/factory.py`.

## Authentification

Le fournisseur `github` attend un jeton **côté serveur** dans
`REPOFLOW_GITHUB_TOKEN`. Il est envoyé en en-tête
`Authorization: Bearer <token>` et ne figure jamais dans une URL, une réponse
d'API ou un log. Les requêtes utilisent également :

- `Accept: application/vnd.github+json`
- `X-GitHub-Api-Version: 2022-11-28`
- `User-Agent: RepoFlow`

### Options d'authentification

| Option | Avantages | Inconvénients | Candidat |
| --- | --- | --- | --- |
| **GitHub App** | Permissions fines par installation, jetons d'installation à durée limitée, webhooks, idéal multi-dépôts. | Mise en place plus lourde (clé privée, installation). | **Recommandé** |
| **OAuth App + token utilisateur** | Simple à démarrer, agit au nom de l'utilisateur. | Portée large, liée à l'utilisateur, révocation manuelle. | Acceptable pour le développement |
| **Personal Access Token (fine-grained)** | Très simple. | Manuel, lié à une personne, rotation à organiser. | Développement / auto-hébergement |

> Note : le fournisseur actuel consomme directement un jeton (PAT ou jeton
> d'installation GitHub App). L'échange de clé privée → jeton d'installation
> (et l'usage de `/installation/repositories`) fera l'objet d'une étape
> ultérieure.

### Permissions minimales à viser

Le principe du **moindre privilège** doit s'appliquer :

- **Métadonnées** : lecture (obligatoire).
- **Contents** : lecture seule.
- **Issues** : lecture seule pour l'affichage.
- **Pull requests** : lecture seule.
- **Checks / Commit statuses** : lecture seule.
- **Administration / protections de branche** : à éviter. **Aucun contournement
  administrateur** des protections de branche ne doit être utilisé.

## Endpoints utilisés

| Donnée | Endpoint |
| --- | --- |
| Dépôts | `GET /user/repos` |
| Pull requests ouvertes | `GET /repos/{owner}/{repo}/pulls?state=open` |
| Détail d'une PR (mergeable, diff) | `GET /repos/{owner}/{repo}/pulls/{number}` |
| Issues | `GET /repos/{owner}/{repo}/issues` |
| Check-runs | `GET /repos/{owner}/{repo}/commits/{ref}/check-runs` |
| Commit statuses | `GET /repos/{owner}/{repo}/commits/{ref}/status` |
| Revues | `GET /repos/{owner}/{repo}/pulls/{number}/reviews` |
| Fichiers modifiés | `GET /repos/{owner}/{repo}/pulls/{number}/files` |
| Chronologie | `GET /repos/{owner}/{repo}/issues/{number}/timeline` |

## Points techniques

- **Pagination** : l'en-tête `Link` (`rel="next"`) est suivi jusqu'à
  épuisement ou jusqu'à `REPOFLOW_GITHUB_MAX_PAGES` (garde-fou anti-boucle).
  La taille de page est bornée à 100 (`REPOFLOW_GITHUB_PER_PAGE`).
  Certaines réponses sont enveloppées (ex. `check_runs`) ; le client extrait
  alors la liste via une clé dédiée.
- **Limites de requêtes (rate limits)** : détection via
  `X-RateLimit-Remaining` ; une limite atteinte lève `GitHubRateLimitError`
  (HTTP 503 côté RepoFlow) en exposant `X-RateLimit-Reset`. Le client interrompt
  aussi la pagination si la page suivante serait impossible.
- **Erreurs normalisées** (`app/integrations/github/errors.py`) :
  `401` → `GitHubAuthError`, `403` (hors rate limit) → `GitHubPermissionError`,
  `403/429` avec rate limit → `GitHubRateLimitError`, `404` → `NotFoundError`,
  `5xx` → `ProviderError`.
- **Délai d'attente** : `REPOFLOW_GITHUB_TIMEOUT` (secondes) s'applique à
  chaque requête HTTP.

## Choix de conversion (mapping)

- **Check-runs** : `success`, `neutral`, `skipped` → réussi ; `failure`,
  `timed_out`, `cancelled`, `action_required`, `stale` → échec ; tout statut
  non terminé → en attente ; conclusion inconnue → inconnu.
- **Commit statuses** : `success` → réussi, `failure`/`error` → échec,
  `pending` → en attente.
- **Tous les checks sont marqués `required=True`** : sans accès aux protections
  de branche, considérer chaque check comme obligatoire est la position la plus
  prudente (un check échoué, en cours ou inconnu bloque la fusion).
- **Décision de revue** : dernier état par relecteur ; `changes_requested`
  prime sur `approved` ; revues présentes mais non concluantes → « revue
  requise ». Une revue `DISMISSED` est ignorée.
- **`mergeable`** : un état GitHub `null` (calcul en cours) est traité comme
  **non fusionnable**, par prudence.
- **Issues** : l'endpoint `/issues` de GitHub renvoie aussi des pull requests ;
  celles-ci sont **exclues** (présence de la clé `pull_request`). Le filtre
  d'état (`open`, `closed`, `all`) est transmis à l'API.
- **Compteurs** : `open_issues_count` de GitHub inclut les PR ; RepoFlow affiche
  donc `open_pull_requests_count = 0` pour un dépôt réel (valeur non disponible
  séparément sur cet endpoint).
- **Détail de PR** : la fiche agrège le détail de la PR, ses checks, ses
  revues, ses fichiers (`/pulls/{number}/files`) et sa chronologie
  (`/issues/{number}/timeline`). Les événements de timeline sont réduits à un
  type, un acteur et un message lisible.

## Cache

- Les données du fournisseur sont mises en cache **en mémoire, par processus**,
  pendant `REPOFLOW_CACHE_TTL_SECONDS` (30 s par défaut, `0` pour désactiver).
- Le paramètre de requête `?refresh=true` (boutons « Rafraîchir ») contourne le
  cache et force un rechargement ; il reste sans effet si le cache est désactivé.
- Ce cache n'est ni persistant ni partagé entre instances : il réduit la
  pression sur l'API GitHub, sans remplacer un cache distribué.

## Sécurité

- Le token reste **exclusivement côté serveur**. Il n'est jamais renvoyé par
  l'API, jamais placé dans une URL, jamais journalisé. Les loggers `httpx` et
  `httpcore` sont forcés au niveau `WARNING`.
- En cas de configuration `github` sans token, l'application répond
  `503 not_configured` avec un message explicite.
- La fusion automatique reste désactivée : l'évaluation d'éligibilité est en
  lecture seule.

## Coût des requêtes

Pour chaque PR, le fournisseur récupère le détail, les check-runs, les commit
statuses et les revues (le résumé de PR ne contient ni `mergeable` ni les
statistiques de diff). La fiche de détail ajoute les fichiers et la chronologie
(uniquement à la demande). Une optimisation GraphQL réduisant le nombre d'appels
est envisagée ultérieurement.
