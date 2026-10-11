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

### 11. ✅ Cache distribué (optionnel)
Le cache TTL est en mémoire (`app/core/cache.py`) : inopérant en
multi-instances. Si le déploiement scale, abstraire derrière l'interface
actuelle et brancher Redis (`REPOFLOW_CACHE_BACKEND=memory|redis`).
*Effort : M.* ✅ Implémenté : backend Redis derrière la même interface
(`app/core/cache.py`), codecs Pydantic explicites par site de cache,
**repli automatique sur mémoire en cas de panne** avec nouvelle tentative
périodique, `REPOFLOW_CACHE_BACKEND`/`REPOFLOW_CACHE_REDIS_URL`, service
`redis` sous profil Docker, tests FakeRedis + intégration réelle (skipif).
Dépendance `redis>=5` en core. ✅ Implémenté : libellés/assignés/jalons exposés par l’API,
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

---

# Nouvelle analyse — 11/10/2026 (branche `develop`, commit `ff24367`)

État : backend 215 tests (couverture 92,7 %), frontend 79 tests + 4 E2E,
toutes les pistes P1/P2 actives réalisées. Nouvelles pistes, classées par
rapport valeur/effort.

## P1 — Rapides — ✅ réalisé le 11/10/2026

### 16. ✅ Chaînes d'erreur frontend non localisées
Deux messages d'erreur de `apiClient.ts` (« Impossible de contacter le
serveur… », « La requête a échoué… ») et l'exception de `main.tsx` sont en
français dur, hors `src/i18n/`. Les passer par des clés de traduction
(`api.networkError`, `api.httpError`, `app.rootMissing`) pour une interface
réellement bilingue de bout en bout.
*Fichiers : `frontend/src/services/apiClient.ts`, `main.tsx`. Effort : S.*

### 17. ✅ Focus sur le contenu à chaque navigation
Seul le lien « Aller au contenu » existe : après un changement de route, le
focus reste sur le lien cliqué. Déplacer le focus sur `<main>` (ou son
titre) à chaque navigation pour les lecteurs d'écran et le clavier.
*Fichier : `frontend/src/layouts/AppLayout.tsx`. Effort : S.*

### 18. ✅ Titres de page par route
`<title>RepoFlow</title>` est statique : impossible de distinguer les pages
dans l'historique ou les onglets. Un petit hook `useDocumentTitle(t('…'))`
appliqué par page (et traduit).
*Fichier : `frontend/index.html` + pages. Effort : S.*

### 19. ✅ Dockerfile backend : retirer le frontend BuildKit
`# syntax=docker/dockerfile:1` force le pull de `docker/dockerfile:1` à chaque
build (échec DNS observé le 10/10) et l'extra `postgres` est installé
systématiquement (image +lourde). Supprimer la ligne de syntax, n'installer
`psycopg` que via un profil ou un build arg, ajouter un utilisateur non-root.
*Fichier : `backend/Dockerfile`. Effort : S.*

## P2 — Structurants

### 20. Code splitting des routes
Toutes les pages sont importées statiquement dans `App.tsx` : un seul bundle
de ~390 Ko (117 Ko gzip) est téléchargé pour la première page. `React.lazy`
+ `Suspense` par page (le layout reste hors chunk).
*Fichier : `frontend/src/App.tsx`. Effort : S-M.*

### 21. ErrorBoundary frontend
Aucune frontière d'erreur : un crash de rendu d'une page blanchit toute
l'application. Un `ErrorBoundary` autour des routes avec message traduit et
bouton de rechargement.
*Fichier : `frontend/src/App.tsx` + `src/i18n`. Effort : S.*

### 22. Tests du worker (couverture 30 %)
`app/worker.py` est le moins couvert du backend (`run_once`,
`_record_snapshot`, `_purge_audit`). Tester une passe complète avec un
fournisseur factice : analyse, purge d'audit, snapshot, tolérance aux
erreurs du snapshot.
*Effort : M.*

### 23. Limiteur de débit distribué
Le rate limiting (`app/core/security.py`) est en mémoire par instance : sans
effet en multi-instances et réinitialisé à chaque redémarrage. Même
problématique que l'ancien cache : brancher un backend Redis optionnel
(`REPOFLOW_RATE_LIMIT_BACKEND=memory|redis`) ou documenter la limite
mono-instance.
*Effort : M.*

### 24. Pagination des listes PR/issues
Les routes plafonnent à 500 éléments sans pagination côté frontend : au-delà,
les données sont silencieusement tronquées. Ajouter `offset`/`before_id`
(curseur déjà prévu pour l'audit) et un chargement progressif (« Charger
plus » ou infini scroll) dans les listes.
*Effort : M.*

## P3 — Long terme

### 25. Visualisation des snapshots
`daily_snapshots` est persisté et exposé (`GET /api/v1/snapshots`) mais rien
ne l'affiche. Un graphique d'évolution (sparkline SVG sans dépendance, ou
librairie légère) sur le tableau de bord par compteur.
*Effort : M.*

### 26. CI : build Docker et dépendances
La CI teste le code mais jamais les images Docker (le build a déjà échoué en
dehors d'elle) et rien ne surveille les dépendances. Ajouter un job
`docker build` des deux images et activer Dependabot (ou Renovate).
*Effort : S-M.*

### 27. Messages d'audit figés dans une langue
Les messages d'audit sont rédigés en français au moment de l'écriture : un
utilisateur anglophone relit un journal en français. Décider : stocker le
code + paramètres et traduire à l'affichage, ou documenter la limitation.
*Effort : M (décision de design).*

### 28. Accessibilité : contrastes du thème clair
Le thème clair a été produit par inversion de palette sans vérification des
contrastes (WCAG AA). Auditer les paires texte/fond principales et ajuster
les tokens si nécessaire.
*Effort : S.*
