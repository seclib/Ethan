# Audit final — Migration WebUI ETHAN vers l'expérience Open WebUI

Date : session courante · Port de référence : **http://localhost:3001** (conteneur Docker `ethan-ui`, build production)

## Verdict : **PASS WITH WARNINGS**

Un utilisateur habitué à Open WebUI retrouve immédiatement les repères : sidebar conversationnelle avec New Chat + recherche, sélecteurs Agent/Model en tête du chat, pages de configuration en cartes avec recherche/filtres, diagnostics dans l'administration. Aucune formation nécessaire pour les actions courantes. Les avertissements (§7) sont des écarts mineurs non bloquants.

---

## 1. Navigation

| Contrôle | Résultat | Preuve SSR (:3001) |
|---|---|---|
| Sidebar familière (structure OWUI) | ✅ | `Explore=1 Pilotage=1 Settings=1 Administration=1` sur /workspace |
| New Chat évident | ✅ | `sidebar-new-chat=1`, « Nouveau chat » présent sur / **et** /workspace (visible partout) |
| Conversations accessibles | ✅ | Liste persistée hors page chat (`chat-sidebar.store`), épinglés + groupage temporel + recherche locale |
| Settings trouvables | ✅ | Groupe Settings : Providers · Memory (/workspace) · General (/settings) |
| Pages de configuration cohérentes | ✅ | Pattern commun `PageHeader` (titre+compteur+description+actions) sur toutes les pages |
| Recherche globale | ✅ | Palette Ctrl+K (`sidebar-search`) |

## 2. Chat (/)

| Contrôle | Résultat |
|---|---|
| Agent + Model visibles | ✅ `[ Agent ▼ ] [ Model ▼ ]` dans `assistant-top-bar` (SSR: Agent=1, Modèle=1) |
| Changement immédiat Agent/Model | ✅ Popovers — listes issues de `GET /agents` / `GET /models` (zéro mock : grep `mockData\|MOCK_\|fakeAgent\|dummyModel` = vide) |
| Model : recherche/groupes/disponibilité | ✅ groupedByProvider, coche actif, `is_available=false` → grisé + « Indisponible » non sélectionnable |
| Agent : Récents/General/Spécialisée | ✅ Groupes dérivés des vraies `capabilities` du Core ; « Sans agent » ; erreur API affichée |
| Composer clair | ✅ Barre visible : 📎 Joindre · Skills · Tools · Knowledge · Agent + compteurs ; Enter/Shift+Enter ; stop ⊓ |
| Contexte actif | ✅ `ChatContextBar` : Agent · Modèle · Outils · Skills · Connaissances · Mémoire — se masque si aucune capacité réelle (anti-chips fantômes) |
| Fichiers accessibles | ✅ Upload réel `uploadFile` → chips retirables |
| Streaming / erreurs | ✅ SSE inchangé, bouton stop, toasts erreurs |

## 3. Agents & Models (pages)

| Contrôle | Résultat | Preuve SSR |
|---|---|---|
| Agents : liste + recherche + création | ✅ | `Nouvel agent=1`, `Rechercher un agent=1` sur /agents |
| Agents : configuration + capabilities | ✅ | Cartes : statut, provider·model, compteurs outils/skills/connaissances depuis `Agent.skill_ids` / `metadata.*` |
| Agents : sélection depuis chat | ✅ | AgentSelector + composer synchronisés (état unique dans page.tsx) |
| Models : liste + providers | ✅ | Cartes avec provider, ctx length, badges capabilities ; filtre Favoris |
| Models : disponibilité | ✅ | Badge Disponible/Indisponible |
| Models : sélection depuis chat | ✅ | ModelSelector avec groupes par provider |

## 4. Fonctionnalités ETHAN toujours présentes

| Capacité | Accès UI | Source de vérité |
|---|---|---|
| Core / Runtime | Service (aucune réimplémentation front) | `core/`, `runtime/` |
| Agents | /agents + sélecteur chat | `lib/api/agents.ts` → routers agents |
| Providers | /providers (CRUD, test, statut) | `lib/api/providers.ts` |
| Models | /models + sélecteur chat | `lib/api/models.ts` |
| Skills | /skills | `lib/api/skills.ts` |
| Tools | /tools | `lib/api/tools.ts` |
| MCP | /tools section « Serveurs MCP » (hash #mcp) | `lib/api/tools.ts` |
| Knowledge / RAG | /knowledge (collections + documents + RAG) | `lib/api/knowledge.ts`, `lib/api/rag.ts` |
| Memory | /workspace (Memory) | `lib/api/memory.ts` |
| Configuration | /settings (10 sections) | `lib/api/settings.ts` |
| Diagnostics | /diagnostics (nouveau, `GET /health/detailed`) | proxy /api → :8000 |
| Monitoring | Lien externe Grafana (:3002) | `docker-compose.observability.yml` |

## 5. Architecture — anti-doublon

| Système | Deuxième implémentation front ? | Preuve |
|---|---|---|
| Agent system | ❌ NON | Toutes les références `/agents` passent par l'unique client `lib/api/agents.ts` (workspace, editor-dialog, sélecteurs, composer) |
| Model/Provider system | ❌ NON | Seuls des **placeholders** `http://localhost:11434` dans les formulaires (saisie utilisateur, pas de logique) ; aucun appel direct à un provider LLM |
| RAG system | ❌ NON | `grep embeddings` dans components = vide ; tout passe par `lib/api/rag.ts` → Core |
| Tools system | ❌ NON | `lib/api/tools.ts` unique |
| Mock data | ❌ AUCUNE | Grep `mockData\|MOCK_\|fakeAgent\|dummyModel` = vide |

**Chaîne validée** : `navigateur → :3001 → WebUI (Next 15) → proxy /api/* → FastAPI :8000 → Core/Runtime`. Open WebUI = référence UX uniquement (`examples/open-webui` jamais importé).

## 6. Technique

| Contrôle | Résultat |
|---|---|
| `npx tsc --noEmit` | ✅ exit 0 |
| `next lint` | ✅ No ESLint warnings or errors |
| Jest | ✅ 6 suites / 12 tests PASS |
| `next build` production (conteneur) | ✅ 0 erreur |
| Routes HTTP (19) | ✅ toutes 200 sur :3001 via conteneur reconstruit |
| API backend | ✅ `:8000/health` = 200 ; proxy `/api/v1/settings` = 401 (auth requise — attendu) |
| Persistance | ✅ sidebar, agent actif, modèle actif, récents (localStorage) — survive au refresh |
| Thèmes dark/light | ✅ deux plans de fond OWUI, tokens unifiés |
| Responsive | ✅ repli auto <768px, rail 60px avec tooltips |
| Docker | ✅ `ethan-ui` sur `127.0.0.1:3001->3000`, rebuild OK |
| Nettoyage | ✅ fichiers morts supprimés (`virtual-list`, barrel index), CSS `.btn*`/`.modal*` orphelins purgés, zéro ref 3011 |

## 7. Avertissements (non bloquants)

1. **Route du chat** : le chat reste sur `/` (pas de route `/c/[id]` type OWUI) — navigation conversationnelle fonctionnelle mais URL non dédiée.
2. **Administration partielle** : Diagnostics ✅, Monitoring = lien externe Grafana, Logs non dédiés (via Grafana/Loki), « Interface » fusionné dans Settings/General.
3. **Memory scoping** : memory globale, pas de scoping par agent (décision backend, non modifiée).
4. **MCP non page dédiée** : absorbé par /tools (section dédiée) — choix assumé et documenté.
5. **Dette résiduelle** : palette Ctrl+K avec entrées en dur à dériver de `NAV_ITEMS_FLAT` ; redimensionnement draggable de la sidebar absent.

## 8. Conclusion

La WebUI ETHAN est désormais perçue comme **« un Open WebUI personnalisé pour ETHAN »** : structure UX OWUI (sidebar conversationnelle, sélecteurs de premier niveau, cartes de configuration, diagnostics), identité ETHAN conservée (logo, nom, accent, terminologie — Missions/Calendar/Notes repositionnés dans Pilotage), et **ETHAN reste la source de vérité** : aucun doublon Agent/Model/Provider/RAG/Tools, aucune donnée mockée, backend intact.

**Verdict : PASS WITH WARNINGS** — les 5 avertissements du §7 sont des choix documentés ou des évolutions futures, aucun ne bloque l'usage quotidien sans formation.

