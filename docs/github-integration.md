# Intégration GitHub (préparation)

Cette version ne se connecte **pas** à GitHub : le fournisseur actif est
`demo`, qui ne requiert aucun token. Ce document prépare l'intégration réelle.

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

Le fournisseur de démonstration (`DemoProvider`) et l'emplacement réservé du
fournisseur réel (`GithubProvider`) implémentent ce contrat. La sélection se
fait via `REPOFLOW_GITHUB_PROVIDER` (`demo` ou `github`) dans la fabrique
`app/integrations/github/factory.py`.

## Options d'authentification à étudier

| Option | Avantages | Inconvénients | Candidat |
| --- | --- | --- | --- |
| **GitHub App** | Permissions fines par installation, jetons d'installation à durée limitée, webhooks, idéal multi-dépôts. | Mise en place plus lourde (clé privée, installation). | **Recommandé** |
| **OAuth App + token utilisateur** | Simple à démarrer, agit au nom de l'utilisateur. | Portée large, liée à l'utilisateur, révocation manuelle. | Acceptable pour le développement |
| **Personal Access Token (fine-grained)** | Très simple. | Manuel, lié à une personne, rotation à organiser. | Développement / auto-hébergement |

### Permissions minimales à viser

Le principe du **moindre privilège** doit s'appliquer :

- **Métadonnées** : lecture (obligatoire).
- **Contents** : lecture seule (jamais d'écriture avant la fusion contrôlée).
- **Issues** : lecture seule pour l'affichage.
- **Pull requests** : lecture seule ; écriture uniquement pour la fusion, et
  seulement lorsque l'automatisation sera activée.
- **Checks / Commit statuses** : lecture seule.
- **Administration / protections de branche** : à éviter. **Aucun contournement
  administrateur** des protections de branche ne doit être utilisé.

## Points techniques à préparer

- **Pagination** : l'API GitHub renvoie des résultats paginés via l'en-tête
  `Link`. Le client devra suivre les pages jusqu'à épuisement ou jusqu'à une
  limite configurée.
- **Limites de requêtes (rate limits)** : réagir aux en-têtes
  `X-RateLimit-Remaining` / `X-RateLimit-Reset`, appliquer un backoff, et
  mettre en cache les réponses lorsque c'est pertinent.
- **Erreurs** : distinguer 401 (authentification), 403 (permissions ou rate
  limit), 404 (ressource absente), 422 (requête invalide) et 5xx (GitHub).
  Les erreurs sont normalisées par `ProviderError`.
- **Fusion** : utiliser l'API de merge avec `merge_method: "squash"`, en
  vérifiant côté serveur toutes les conditions avant l'appel, et en
  n'activant jamais le contournement des protections de branche.

## Sécurité

- Le token reste **exclusivement côté serveur**. Il n'est jamais renvoyé par
  l'API, jamais placé dans une URL, jamais journalisé.
- En cas de configuration `github` sans token, l'application répond
  `503 not_configured` avec un message explicite plutôt que de démarrer à moitié.
