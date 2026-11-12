# Audit Complet — Flux Frontend Login ETHAN

## Machine d'État Reconstituée

```
[1] User clique "Login"
      ↓
[2] LoginForm.handleSubmit() appelle onSubmit(operatorId, password)
      ↓
[3] LoginPage.handleLogin() — NE FAIT PAS le login API ici
    → Stocke operatorId/password dans useState (pendingOperatorId, pendingPassword)
    → setShowOverlay(true) — affiche le LoadingOverlay
      ↓
[4] LoadingOverlay s'anime pendant ~5 secondes (6 étapes visuelles)
    → Affiche "ACCESS GRANTED"
    → setTimeout(onComplete, 1200)
      ↓
[5] onComplete = handleAuthComplete() est appelé
    → Déclare doLogin() async à l'intérieur
    → Appelle: await login(pendingOperatorId, pendingPassword, pendingOperatorId)
      ↓
[6] AuthProvider.login() fait le fetch POST /api/auth/login
    → Route Handler proxy → FastAPI backend
    → Réponse 200 + Set-Cookie: ethan_token=...
    → setUser(normalizeUser(data.user))
      ↓
[7] ★ RETOUR dans handleAuthComplete.doLogin()
    → window.location.href = "/"  ← DEVRAIT recharger la page
      ↓
[8] Navigateur fait GET /
    → middleware.ts vérifie cookie "ethan_token"
    → Si présent → 200 OK → Dashboard
    → Si absent → 307 → /login
```

---

## Bugs Identifiés

### P0 — BLOQUANT : Stale Closure sur `pendingOperatorId` et `pendingPassword`

> [!CAUTION]
> **C'est LE bug qui bloque le login.**

**Fichier** : [login/page.tsx](file:///home/fatsio/AI/Ethan/interfaces/webui/src/app/(auth)/login/page.tsx#L21-L42)

**Le problème** :

```typescript
// Étape 1 : handleLogin est appelé au submit
const handleLogin = useCallback(
  async (operatorId: string, password: string) => {
    setError(null);
    setPendingOperatorId(operatorId);  // ← setState async
    setPendingPassword(password);       // ← setState async
    setShowOverlay(true);               // ← active l'overlay
  },
  []  // ← pas de dépendances
);

// Étape 2 : handleAuthComplete est appelé 5s plus tard par l'overlay
const handleAuthComplete = useCallback(() => {
  const doLogin = async () => {
    try {
      await login(pendingOperatorId, pendingPassword, pendingOperatorId);
      //          ^^^^^^^^^^^^^^^^    ^^^^^^^^^^^^^^^^
      //          VALEURS CAPTURÉES AU MOMENT DE LA CRÉATION DU CALLBACK
      //          = "" et "" (les valeurs initiales de useState)
      window.location.href = "/";
    } catch (err) {
      setShowOverlay(false);
      setError(err instanceof Error ? err.message : "Authentication failed");
    }
  };
  doLogin();
}, [login, router, pendingOperatorId, pendingPassword]);
```

**Analyse** :

1. `handleLogin` stocke les credentials via `setState` (asynchrone).
2. `handleLogin` active immédiatement `showOverlay`.
3. `handleAuthComplete` est un `useCallback` avec `[login, router, pendingOperatorId, pendingPassword]` en dépendances.
4. **Le problème est subtil** : `handleAuthComplete` est passé comme prop `onComplete` au composant `LoadingOverlay`.
5. `LoadingOverlay` capture `onComplete` dans son `useEffect` (ligne 95 : `[isVisible, status, onComplete, onError]`).
6. Quand `isVisible` passe à `true`, l'effet démarre l'animation. Il capture la référence `onComplete` **à cet instant**.
7. Pendant que l'animation tourne (~5s), React met à jour `pendingOperatorId`/`pendingPassword` et recrée `handleAuthComplete` avec les bonnes valeurs.
8. **MAIS** : le `useEffect` dans `LoadingOverlay` a déjà capturé l'**ancienne** référence de `onComplete` (celle avec `""` et `""`).
9. Quand le `setTimeout(() => { if (!cancelled) onComplete(); }, 1200)` se déclenche (ligne 78), il appelle l'ancienne closure.

**Résultat** : `login("", "", "")` est envoyé au backend. Le backend retourne un JWT pour l'utilisateur `""` (ou `"developer"` par défaut dans le code actuel). Le cookie EST setté mais pour un utilisateur fantôme. `window.location.href = "/"` recharge la page. Le middleware voit le cookie, laisse passer. Le dashboard charge.

**MAIS** : si le backend rejette les credentials vides (ce qui est le bon comportement), alors `login()` throw, le `catch` remet `showOverlay=false` et affiche l'erreur. Avec le code actuel de `main.py` (qui accepte n'importe quel username), le login "fonctionne" techniquement mais avec le mauvais utilisateur.

**Cependant**, la timeline exacte crée une **race condition** :
- Le `useEffect` de `LoadingOverlay` redémarre à chaque changement de `onComplete` dans ses dépendances.
- Le premier rendu démarre l'animation avec l'ancien `onComplete`.
- Le deuxième rendu (après que React ait batché les setState) **annule** l'animation (via `cancelled = true` dans le cleanup) et en redémarre une nouvelle.
- L'utilisateur voit donc l'animation recommencer de zéro, ou pire, les deux s'entremêlent.

**Ce pattern est fondamentalement cassé.**

---

### P0 — BLOQUANT : Le `useEffect` de LoadingOverlay se réexécute en boucle

**Fichier** : [loading-overlay.tsx](file:///home/fatsio/AI/Ethan/interfaces/webui/src/app/(auth)/login/components/loading-overlay.tsx#L36-L95)

```typescript
useEffect(() => {
  if (!isVisible || status !== "authenticating") return;
  // ... animation logic ...
  // line 78: setTimeout(() => { if (!cancelled) onComplete(); }, 1200);
  return () => { cancelled = true; clearTimeout(initialDelay); };
}, [isVisible, status, onComplete, onError]);  // ← onComplete dans les deps
```

**Problème** : `onComplete` (= `handleAuthComplete`) est recréé par React après chaque batch de setState dans `handleLogin`. Séquence :

1. `handleLogin` → `setPendingOperatorId("admin")` + `setPendingPassword("admin")` + `setShowOverlay(true)`
2. React batche et re-rend → `handleAuthComplete` est recréé (nouvelle ref) car ses deps ont changé
3. L'`useEffect` dans `LoadingOverlay` voit que `onComplete` a changé → exécute le cleanup (met `cancelled = true`) → redémarre l'animation
4. Mais `status` est remis à `"authenticating"` par le reset effect (ligne 27-33) **uniquement si `isVisible` change**
5. Le status n'est pas reset → l'animation peut se retrouver dans un état incohérent

**Scénarios possibles** :
- L'animation redémarre et l'utilisateur voit un délai double (~10s)
- L'animation est annulée et `onComplete` n'est jamais appelé → **l'utilisateur reste bloqué indéfiniment sur l'overlay**
- L'ancienne animation appelle `onComplete` avec les vieilles valeurs avant d'être cancelled

---

### P1 — `proxy.ts` est un fichier mort qui crée de la confusion

**Fichier** : [proxy.ts](file:///home/fatsio/AI/Ethan/interfaces/webui/src/proxy.ts)

Ce fichier exporte une fonction `proxy()` et un `config`, mais **il n'est importé nulle part**. Le vrai middleware est dans `middleware.ts`. Les deux fichiers coexistent avec des logiques légèrement différentes (ex: `proxy.ts` considère `/` comme public, `middleware.ts` non).

Ce n'est pas un bug fonctionnel, mais c'est une source majeure de confusion lors du debug.

---

### P1 — `rewrites()` dans `next.config.js` est en conflit potentiel avec le Route Handler

**Fichier** : [next.config.js](file:///home/fatsio/AI/Ethan/interfaces/webui/next.config.js#L6-L13)

```javascript
async rewrites() {
  return [
    { source: "/api/:path*", destination: `${ETHAN_API_URL}/:path*` }
  ];
}
```

Les Route Handlers Next.js (`src/app/api/auth/[...path]/route.ts`) ont **priorité** sur les rewrites — c'est documenté par Next.js. Donc pour `/api/auth/*`, le Route Handler est bien utilisé. Mais pour toutes les **autres** routes `/api/*`, les rewrites sont toujours actifs et continuent d'avaler les `Set-Cookie`.

Ce n'est pas bloquant pour le login, mais c'est une bombe à retardement pour tout futur endpoint qui setterait un cookie.

---

### P2 — Le middleware.ts a un commentaire mensonger

```typescript
// Since JWT is stored in localStorage (client-side)...
```

Le JWT n'est plus dans localStorage. Le commentaire est un vestige qui induit en erreur.

---

## Résumé

| Priorité | Bug | Fichier | Impact |
|----------|-----|---------|--------|
| **P0** | Stale closure : `handleAuthComplete` capture `""` au lieu des vrais credentials | `login/page.tsx` L31-42 | Login envoie des credentials vides |
| **P0** | `useEffect` dans `LoadingOverlay` se cancel/restart quand `onComplete` change de ref | `loading-overlay.tsx` L36-95 | Animation peut ne jamais appeler `onComplete` → utilisateur bloqué |
| **P1** | `proxy.ts` est un fichier mort avec une logique de sécurité concurrente | `proxy.ts` | Confusion architecturale |
| **P1** | `rewrites()` global reste actif pour les routes non-auth | `next.config.js` | Cookies futurs seront perdus |
| **P2** | Commentaire obsolète dans `middleware.ts` | `middleware.ts` L4-9 | Dette doc |

## Correction Recommandée (P0)

Le fix est simple : **ne pas séparer l'animation de l'appel API**. Deux approches :

**Option A** (minimale) : Utiliser un `useRef` pour les credentials au lieu de `useState`, éliminant le problème de stale closure :
```typescript
const pendingRef = useRef({ operatorId: "", password: "" });
```

**Option B** (propre) : Appeler `login()` dans `handleLogin` immédiatement, puis déclencher l'overlay **uniquement si le login réussit**. L'overlay devient purement cosmétique (pas de callback `onComplete` qui déclenche quoi que ce soit) :
```typescript
handleLogin → await login() → setShowOverlay(true) → setTimeout → window.location.href = "/"
```
