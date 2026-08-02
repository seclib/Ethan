# Audit du Flux d'Authentification ETHAN

## Architecture actuelle

Le flux d'authentification s'appuie sur une architecture hybride où le frontend gère l'état visuel et le backend FastAPI gère la sécurité :

1. **Frontend (Formulaire)** : `interfaces/webui/src/app/(auth)/login/page.tsx` gère l'UI.
2. **API Client** : `AuthProvider` appelle `fetch("/api/auth/login", { credentials: "include" })`.
3. **Proxy (Next.js rewrites)** : Le fichier `next.config.js` intercepte `/api/*` et route la requête vers le backend `http://api:8000/*`.
4. **Backend (FastAPI)** : Le endpoint `/auth/login` dans `interfaces/api/main.py` valide la requête et attache un header `Set-Cookie: ethan_token=...; HttpOnly; SameSite=lax; Path=/`.
5. **Redirection** : Si le proxy retourne 200 OK, `login/page.tsx` déclenche `window.location.href = "/"`.
6. **Middleware (Next.js)** : Le fichier `middleware.ts` intercepte l'accès à `/`, lit `request.cookies.get("ethan_token")`. Si absent, il redirige vers `/login?redirect=/`.

## Flux réel observé

1. L'utilisateur saisit ses identifiants et valide.
2. La requête `/api/auth/login` est envoyée. Le backend FastAPI accepte la connexion et retourne un code HTTP 200 OK avec le header `Set-Cookie`.
3. Le frontend (ne voyant pas d'erreur) affiche l'animation "Access Granted".
4. Le frontend exécute `window.location.href = "/"`, forçant le navigateur à charger la page d'accueil.
5. **Le navigateur n'envoie pas le cookie `ethan_token` lors de cette requête.**
6. Le `middleware.ts` intercepte la requête, constate l'absence du cookie, et renvoie une redirection HTTP 307 vers `/login?redirect=/`.
7. Le navigateur recharge la page de login à son état initial.
8. Résultat visuel : la page se rafraîchit instantanément sur `/login` sans message d'erreur. L'utilisateur semble "bloqué".

## Cause racine probable

**Le mécanisme de `rewrites` natif de Next.js (dans `next.config.js`) ne relaie pas correctement le header `Set-Cookie` retourné par le backend FastAPI vers le navigateur.**

C'est une limitation connue du proxy interne de Next.js (souvent lié au runtime Edge ou au client `undici` sous-jacent) lors du proxying de requêtes cross-origin ou vers des conteneurs Docker internes :
- Le backend génère bien le `Set-Cookie`.
- Le serveur Next.js reçoit la réponse du backend.
- Le serveur Next.js omet de propager le header `Set-Cookie` au navigateur client lors de l'acheminement de la réponse.

Puisque le navigateur ne reçoit jamais le cookie, la navigation subséquente vers le dashboard (`/`) est logiquement rejetée par le middleware de sécurité `middleware.ts`.

## Fichiers concernés

- `interfaces/webui/next.config.js` (cause : proxying défectueux des cookies)
- `interfaces/webui/src/middleware.ts` (conséquence : rejet légitime)
- `interfaces/api/main.py` (sain : la logique backend est correcte)

## Correction minimale recommandée

Il faut contourner le système de `rewrites` de `next.config.js` uniquement pour les routes critiques d'authentification en créant un **Route Handler explicite** côté Next.js. Ce handler fera le relais manuellement et s'assurera de copier le `Set-Cookie`.

**Action à réaliser :**
Créer un fichier `interfaces/webui/src/app/api/auth/login/route.ts` contenant le proxy manuel :

```typescript
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json();
  
  // En Docker, ETHAN_API_URL = "http://api:8000"
  const backendUrl = process.env.ETHAN_API_URL || "http://localhost:8000";
  
  const response = await fetch(`${backendUrl}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await response.json();
  const nextResponse = NextResponse.json(data, { status: response.status });
  
  // Propager explicitement le(s) cookie(s) retourné(s) par FastAPI
  const setCookieHeader = response.headers.get("set-cookie");
  if (setCookieHeader) {
    nextResponse.headers.set("set-cookie", setCookieHeader);
  }
  
  return nextResponse;
}
```

*Note : La même opération devra être effectuée pour `interfaces/webui/src/app/api/auth/refresh/route.ts` et `logout/route.ts` afin de garantir que la gestion du cycle de vie du cookie n'est jamais altérée par le proxy global.*
