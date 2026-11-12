# Quantar WebUI — Diagnostic Not Found

Date : 2026-11-04
Statut : diagnostic terminé, correction à valider par redéploiement de l'image WebUI

## 1. Cause exacte

La route frontend `/quantar` existe bien dans le dépôt, sous :

- `interfaces/webui/src/app/quantar/page.tsx`

Le manque de correspondance apparente provient du fait que l'interface réellement servie sur le port 3001 provient du conteneur Docker `ethan-ui`, dont l'image déployée semble antérieure à la création de cette route. Le source local contient la page, mais l'image déployée ne l'expose pas nécessairement telle quelle.

Le flux constaté est le suivant :

1. `GET /quantar` non authentifié → redirection 307 vers `/login?redirect=%2Fquantar`
2. `GET /quantar` avec cookie JWT valide → page HTML 200, mais le render Next.js retourne le composant par défaut 404 dans l'enveloppe RSC.
3. Les autres routes (`/odin`, `/frame`, `/quantar`) ne sont pas disponibles dans le service actif de manière identique.

Ce comportement est cohérent avec une instance WebUI construite avant l'ajout de la route `/quantar`.

## 2. Vérifications effectuées

- Route source présente : oui
- Route déclarée dans les manifests : oui
- Endpoint API `/v1/quantar/status` : 401 sans session, attendu
- Route HTTP `/quantar` : 307 sans session, 200 avec session forgée, mais render 404 du composant
- Backend `quantar_router` inclus dans FastAPI : oui

## 3. Résultats HTTP

- `/quantar` sans token : `307 -> /login`
- `/quantar` avec cookie JWT signé : `200`, contenu « This page could not be found. »
- `/v1/quantar/status` : `401` sans session, comportement attendu
- `/v1/quantar/config` : non testé sans session; comportement attendu identique

## 4. Fichiers concernés

- `interfaces/webui/src/app/quantar/page.tsx`
- `interfaces/webui/src/components/layout/nav-config.ts`
- `interfaces/webui/src/lib/api/client.ts`
- `interfaces/api/main.py`
- `interfaces/api/routers/quantar.py`

## 5. Hypothèse retenue

Cause exacte la plus probable : instance WebUI déployée obsolète par rapport au source actuel. La mise à jour nécessite une reconstruction et un redéploiement de `ethan-ui`, non réalisé ici par prudence.

## 6. Modifications

Aucune correction de code appliquée. Le diagnostic montre que le problème ne provient pas d'une route absente dans le dépôt, mais d'un état runtime service plus ancien.

## 7. Validation visuelle

- Non effectuée avec Playwright : aucun navigateur Chromium disponible.
- Preuve obtenue via HTML HTTP et forged JJT authentifié.

## 8. Blocages

- Pas de navigateur chromium local pour validation visuelle.
- Pas d'identification utilisateur test fournie.
- Le service WebUI actif est conteneurisé (`ethan-ui`) et n'exécute pas directement le source local.

## Conclusion

La page Quantar existe dans le source mais reste rendue comme 404 par l'instance WebUI active. La correction recommandée est le rebuild/redeploy de `ethan-ui`. La page ne peut pas être déclarée corrigée sans validation visuelle réelle.
