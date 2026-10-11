# Pistes d'amélioration — RepoFlow

Analyse du projet au 10/10/2026 (branche `develop`, commit `4467f51`).
Suggestions classées par priorité, avec fichiers concernés et effort estimé
(S < 1 j, M 1-3 j, L > 3 j).

## P1 — Court terme (rapides et à forte valeur) — ✅ réalisé le 10/10/2026

### 1. ✅ État des filtres dans l'URL
Les filtres (recherche, dépôt, état) sont perdus au rafraîchissement et non
partageables. Utiliser `useSearchParams` (déjà présent sur la page détail)
pour persister `?q=`, `?repository=`, `?state=`.
*Fichiers : `frontend/src/pages/PullRequestsPage.tsx`, `IssuesPage.tsx`. Effort : S.*

### 2. ✅ Accessibilité du menu mobile
Le tiroir latéral mobile (`AppLayout.tsx`) ne piège pas le focus, ne se ferme
pas avec `Échap` et ne masque pas le scroll de fond. Ajouter un composant
`Drawer` (focus trap, `aria-modal`, fermeture clavier).
*Effort : S.*

### 3. ✅ Visibilité du quota GitHub dans l'UI
Le backend connaît `X-RateLimit-Remaining` (géré dans
`backend/app/integrations/github/client.py`) mais ne l'expose pas. Ajouter un
en-tête `X-GitHub-RateLimit-Remaining` sur les réponses proxy ou un champ dans
`/api/health`, et un badge discret dans l'en-tête frontend quand le quota est
bas. Complète le travail ETag/Retry-After déjà fait.
*Effort : S.*

### 4. ✅ Rétention et pagination du journal d'audit
`GET /api/v1/audit` limite à 500 entrées sans curseur, et rien ne purge les
 anciennes entrées. Ajouter une pagination par curseur (`before_id`) et une
 stratégie de rétention configurable (`REPOFLOW_AUDIT_RETENTION_DAYS`) avec
 purge dans le worker.
*Fichiers : `backend/app/api/v1/routes/audit.py`, `audit_service.py`,
`worker.py`. Effort : M.*

### 5. ✅ Rafraîchissement automatique optionnel
Un bouton « auto » (30 s/1 min, `setInterval` + visibilité de l'onglet) sur
tableau de bord et listes, désactivé par défaut. Évite le rafraîchissement
manuel systématique sans consommer le quota (le cache TTL + ETag absorbent).
*Fichiers : `frontend/src/hooks/useAsync.ts`, pages. Effort : S.*

## P2 — Moyen terme (structurants)

### 6. ✅ Réduire le nombre de requêtes GitHub (GraphQL)
Pour chaque PR ouverte : détail + check-runs + status + revues ≈ 4-5 requêtes
(voir le commentaire dans `github_provider.py:103`). Une seule requête GraphQL
par dépôt ramènerait tout (PR, checks, reviews, mergeable) : division par ~5 de
la consommation du quota. C'est la plus grosse optimisation possible. ✅ Implémenté : transport
GraphQL opt-in (`REPOFLOW_GITHUB_USE_GRAPHQL=true`), une requête par page
avec checks et revues inclus ; le détail et la fusion restent en REST.
*Effort : M-L.*

### 7. ✅ Recherche côté serveur
La recherche texte est aujourd'hui client-side (`frontend/src/lib/search.ts`) :
le serveur renvoie tout, le navigateur filtre. Ajouter un paramètre `search`
sur `GET /v1/pull-requests` et `/v1/issues` (filtrage dans `data_service`,
documenté dans le contrat `Provider`) pour préparer les gros volumes.
*Effort : M.*

### 8. ✅ Historisation légère des données
Les données GitHub ne sont pas persistées (choix documenté). Pour suivre
l'évolution (temps de fusion, taux d'échec des checks), ajouter un snapshot
quotidien agrégé par dépôt (compteurs PR/checks/issues) dans une table
`daily_snapshots`, alimenté par le worker. Pas de copie exhaustive : juste les
agrégats du dashboard.
*Effort : M.* ✅ Implémenté : table `daily_snapshots` (une ligne par dépôt et
par jour, mise à jour par le worker), service dédié réutilisant les compteurs
du dashboard, route `GET /api/v1/snapshots` (filtres `repository`/`since`).
Une visualisation graphique côté frontend reste possible plus tard.

### 9. ✅ Tests E2E (Playwright)
La CI couvre lint + tests unitaires, aucun parcours de bout en bout. Ajouter
2-3 parcours critiques contre le fournisseur demo : liste → filtre → détail
PR, automatisations → engage l'arrêt d'urgence. Le mode demo en fait un
prérequis trivial.
*Effort : M.*

### 10. ✅ Thème clair
Interface uniquement sombre. Exploiter `prefers-color-scheme` + variables CSS
Tailwind ; le sélecteur rejoint le switcher de langue dans l'en-tête.
*Effort : M.* ✅ Implémenté : inversion de palette via variables CSS
(`html.theme-light`), bascule persistée dans l’en-tête.

### 11. Cache distribué (optionnel) — différé
Le cache TTL est en mémoire (`app/core/cache.py`) : inopérant en
multi-instances. Si le déploiement scale, abstraire derrière l'interface
actuelle et brancher Redis (`REPOFLOW_CACHE_BACKEND=memory|redis`).
*Effort : M.* **Différé** : déploiement mono-instance à ce jour. ✅ Implémenté : libellés/assignés/jalons exposés par l’API,
filtres dédiés dans la barre et affichage sur les cartes.

## P3 — Long terme (à garder en tête)

### 12. Mises à jour temps réel — différé
Remplacer le rafraîchissement manuel par SSE (`/api/v1/events/stream`) côté
worker : pousser les événements d'audit nouveaux. Le fallback REST reste tel
quel.
*Effort : L.* **Différé** : le rafraîchissement automatique (P1.5) couvre le
besoin actuel.

### 13. Virtualisation des longues listes — non nécessaire aujourd'hui
Les listes PR/issues rendent tous les éléments. Si les volumes grandissent,
`@tanstack/react-virtual` sur les conteneurs de cartes.
*Effort : S.* **À évaluer** : volumes actuels faibles, recherche serveur en
place.
Les listes PR/issues rendent tous les éléments. Si les volumes grandissent,
`@tanstack/react-virtual` sur les conteneurs de cartes.
*Effort : S (une fois le besoin confirmé).*

### 14. ✅ Filtres issues avancés
Ajouter libellés, assignés et jalons (`GET /repos/{o}/{r}/issues` les expose
déjà) : colonnes `labels`/`assignees` dans le mapping, filtres dans l'UI.
*Effort : M.*

### 15. ✅ Token GitHub App
Échange clé privée → JWT → jeton d'installation implémenté
(`app/integrations/github/app_auth.py`) : cache + renouvellement
automatique, prioritaire sur le token personnel, quota 15 000 req/h.
Reste éventuellement : lister les installations dynamiquement
(`/installation/repositories`) au lieu d'un identifiant fixe.

## Déjà couvert (ne pas retravailler)
- Requêtes conditionnelles ETag, Retry-After, single-flight (2026-10).
- i18n fr/en backend + frontend, recherche client, combobox clavier,
  indicateur privé/public.
- Sécurité : en-têtes restrictifs, rate limiting, corrélations `X-Request-ID`,
  métriques Prometheus, garde-fous de fusion.
