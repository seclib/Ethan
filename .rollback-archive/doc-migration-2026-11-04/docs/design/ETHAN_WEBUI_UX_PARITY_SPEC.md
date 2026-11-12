# ETHAN WebUI — Spécification de parité UX avec Open-WebUI

**Date :** 13 août 2026
**Révision ETHAN inspectée :** `c9252ca87493d0b291ba1289fa077c7ab87b86d1`
**Références :** `docs/audit/OPENWEBUI_UX_REFERENCE.md`, `docs/audit/OPENWEBUI_COMPONENT_REFERENCE.md`, `docs/audit/OPENWEBUI_FUNCTIONAL_REFERENCE.md`, `docs/architecture/OPENWEBUI_ETHAN_MAPPING.md`, `docs/architecture/ETHAN_WEBUI_TARGET_ARCHITECTURE.md`

## 1. Principe de parité

**Open-WebUI est la référence UX.** ETHAN ne doit pas inventer une UX
différente sans raison valable.

Toute différence ETHAN/Open-WebUI doit appartenir à **une et une seule** de ces
catégories :

| # | Catégorie | Définition | Exemple |
|---|---|---|---|
| 1 | **Nécessité ETHAN** | Le comportement Open-WebUI est impossible ou incohérent avec l'architecture ETHAN (Core/Runtime propriétaire) | Auth par cookie HttpOnly `ethan_token` au lieu du token localStorage |
| 2 | **Amélioration UX démontrable** | Le changement améliore mesurablement l'expérience (temps, erreurs, clarté) avec preuve | — |
| 3 | **Limitation technique** | Le comportement Open-WebUI dépend d'une technologie non retenue (Pyodide, Socket.IO) | Code interpreter Pyodide → exécution serveur |
| 4 | **Différence fonctionnelle obligatoire** | ETHAN possède une capacité que Open-WebUI n'a pas (agents, missions, goals) et qui doit être exposée | Écran Agents/Missions dans la sidebar |

**Règle absolue :** si aucune catégorie ne s'applique, **conserver le
comportement Open-WebUI**.

---

## 2. Synthèse des décisions de parité

| Élément UX | Décision | Catégorie de différence |
|---|---|---|
| Sidebar | Conserver (bibliothèque opérationnelle) | — |
| Navigation secondaire Workspace/Admin | Conserver (onglets horizontaux) | — |
| Gating par permission | Conserver | — |
| Commandes globales | Conserver | — |
| Chat (arbre, streaming, actions) | Conserver | — |
| Model selector | Conserver (popover, recherche, multi) | — |
| Composer | Conserver (rich input, slash, queue) | — |
| Attachments | Conserver (chips, progression) | — |
| Tool selection | Conserver (modal, tool_ids) | — |
| Knowledge selection | Conserver (menu, commande, citations) | — |
| Skill selection | Conserver (mention structurée) | — |
| Settings | Conserver (modal + admin) | — |
| Dialogs | Conserver (overlays spécialisés) | — |
| Dropdowns | Conserver (menus contextuels) | — |
| Cards | Conserver (registre Workspace) | — |
| Notifications | Conserver (toasts) | — |
| Context menus | Conserver (actions au survol) | — |
| Search | Conserver (overlay global) | — |
| Mobile/responsive | Conserver (breakpoint 768px) | — |
| Dark/light mode | Conserver (thème system) | — |
| Auth | Adapter | 1 — Nécessité ETHAN |
| Temps réel | Adapter | 3 — Limitation technique (Socket.IO → SSE/NATS) |
| Code interpreter | Adapter | 3 — Limitation technique (Pyodide → serveur) |
| Terminal | Adapter | 3 — Limitation technique (XTerm → serveur) |
| Agents/Missions/Goals | Ajouter | 4 — Différence fonctionnelle obligatoire |
| Observabilité (logs) | Ajouter | 4 — Différence fonctionnelle obligatoire |

---

## 3. Spécifications détaillées

### 3.1. Sidebar

**Comportement Open-WebUI (référence) :**
- Ouverte sur desktop selon `localStorage.sidebar` ; fermée par défaut sur mobile.
- Bouton compact quand fermée ; overlay/mobile drawer quand ouverte.
- Largeur redimensionnable (`sidebarWidth`).
- C'est la **bibliothèque opérationnelle** de l'utilisateur : chats, favoris de modèles, notes, channels, dossiers, items épinglables (notes/workspace/automations/calendar/admin).
- Recherche globale accessible depuis la sidebar.
- Nouveau chat / chat temporaire.
- Dossiers hiérarchiques par drag-and-drop ; tags ; chats archivés.

**Décision ETHAN :** Conserver intégralement.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| État ouvert/fermé | Persisté dans `localStorage.sidebar` ; défaut ouvert desktop, fermé mobile |
| Largeur | Redimensionnable par drag ; persistée dans `localStorage.sidebarWidth` |
| Mobile | Drawer overlay avec backdrop ; fermeture par clic backdrop ou Escape |
| Sections | 1. Nouveau chat + chat temporaire · 2. Recherche · 3. Chats (dossiers, tags, archivés) · 4. Favoris modèles · 5. Items épinglables (Notes, Workspace, Automations, Calendar, Admin) |
| Données | `GET /chats`, `GET /v1/notes`, `GET /v1/channels`, `GET /v1/automations`, `GET /v1/calendar` ; favoris via `GET/PUT /users/{id}/settings` |
| Gating | Un item n'est pas affiché si la permission/feature est absente (ex. Admin si non-admin) |
| Drag-and-drop | Déplacer un chat dans un dossier → `PUT /chats/{id}` avec `folder_id` |

**Différences autorisées :** Aucune.

---

### 3.2. Navigation

**Comportement Open-WebUI (référence) :**
- Shell `100dvh`, contenu scrollable, sidebar et contenu flexibles.
- Navigation secondaire Workspace/Admin : onglets horizontaux scrollables, actif par pathname ; menu hamburger sur mobile.
- Gating : l'item n'est pas affiché si feature/permission absente ; la page redirige au montage.
- Commandes globales (raccourcis) : recherche, nouveau chat, focus composer, copie dernière réponse/code, sidebar, settings, temporaire, régénération.

**Décision ETHAN :** Conserver intégralement.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Shell | Hauteur `100dvh` ; sidebar et contenu flexibles ; toasts et modals hors du flux |
| Onglets Workspace | Models, Knowledge, Prompts, Skills, Tools — horizontaux, scrollables, actif par pathname |
| Onglets Admin | Users, Analytics, Evaluations, Functions, Settings — même pattern |
| Mobile | Menu hamburger pour les navs secondaires |
| Gating | Test de permission au montage + masquage des onglets non autorisés ; redirection si accès refusé |
| Raccourcis | `Ctrl+K` recherche · `Ctrl+Shift+O` nouveau chat · `Ctrl+Shift+F` focus composer · `Ctrl+Shift+C` copier dernière réponse · `Ctrl+Shift+J` copier dernier code · `Ctrl+Shift+S` sidebar · `Ctrl+Shift+,` settings · `Ctrl+Shift+T` chat temporaire · `Ctrl+Shift+R` régénérer |

**Différences autorisées :** Aucune.

---

### 3.3. Workspace

**Comportement Open-WebUI (référence) :**
- UX de registre : liste/recherche/pagination, création explicite, vue détail, menu par ressource.
- Patterns partagés : `ViewSelector`, tags, visibilité, access control, import/export, clone, confirmation des suppressions.
- Éditeurs (modèles, skills, tools) : contenu technique dans un panneau dédié, séparé de la liste.
- Knowledge : navigation à deux niveaux (liste de bases → page d'une base avec fichiers, ajout de texte, import/upload, reindex/reset, permissions).

**Décision ETHAN :** Conserver le pattern registre. Adapter les sources de données aux routes ETHAN.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Liste | Recherche + pagination + tri ; chaque ligne = carte avec actions au survol |
| Création | Bouton explicite « Create » → route `/workspace/{resource}/create` |
| Détail | Route stable `/workspace/{resource}/edit?id=` ; panneau technique séparé |
| Actions | Éditer, cloner, exporter, importer, supprimer (avec confirmation), access control |
| Access control | Modal `AccessControl` : grants par utilisateur/groupe ; `write_access` renvoyé par l'API |
| Knowledge | 2 niveaux : liste des bases → page base (fichiers, add text, upload, reindex/reset, permissions) |
| Données | Models → `GET /models` · Knowledge → `GET /v1/knowledge` · Prompts → `GET /v1/prompts` · Skills → `GET /v1/skills` · Tools → `GET /v1/tools` |

**Différences autorisées :** Aucune sur le pattern UX. Les données viennent des routes ETHAN (aucune catégorie nécessaire — c'est la règle de base).

---

### 3.4. Chat

**Comportement Open-WebUI (référence) :**
- Arbre de conversation : chaque message a `id`, `parentId`, `childrenIds`, rôle, contenu, fichiers, modèle, `done`.
- Brancher/éditer/régénérer crée ou pointe vers des enfants ; chemin courant produit par `createMessagesList`.
- Streaming SSE avec deltas ; `splitLargeDeltas` optionnel.
- Multi-modèle / arena : un assistant par modèle.
- Actions de message : éditer, sauvegarder une copie, copier (texte/formaté), TTS, évaluer, régénérer (menu variante/prompt), supprimer, actions de modèle.
- Message assistant structuré en couches : en-tête identité/modèle, statut, contenu Markdown, parties spéciales (code, reasoning/details, tool calls, citations, fichiers, tasks, web results, follow-ups), barre d'actions au survol.
- Citations à proximité du message ; tool calls rendus en détails ; artefacts/embeds en panneaux.

**Décision ETHAN :** Conserver intégralement l'UX. Le pipeline d'exécution est Core (voir `ETHAN_WEBUI_TARGET_ARCHITECTURE.md` §4).

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Arbre | `Message { id, chat_id, parent_id, children_ids[], role, content, model, files[], tool_calls[], sources[], status, done, created_at, updated_at }` |
| Éditer | Crée un enfant ; préserve les blocs `details` (reasoning) par pré/post-traitement |
| Régénérer | Menu de variante/prompt ; crée un enfant |
| Streaming | SSE `chat.message.delta` → accumulation ; `chat.message.done` → finalisation |
| Multi-modèle | Un placeholder assistant par modèle ; `message_ids: {model_id: assistant_message_id}` |
| Actions | Éditer, copier (texte/formaté), TTS, évaluer, régénérer, supprimer, action de modèle — conditionnées par permissions |
| Citations | `chat.sources` → `Citations.svelte` à proximité du message |
| Tool calls | `chat.tool.call` / `chat.tool.result` → `ToolCallDisplay.svelte` |
| Statuts | `generating`, `error`, `done` ; bouton principal devient stop pendant génération |
| Queue | Nouveaux messages mis en file pendant génération (pas de blocage) |
| Données | `POST /chat/completions` (pipeline) · `GET/POST /chats` · `GET/POST /chats/{id}/messages` |

**Différences autorisées :** Aucune sur l'UX. Le protocole de streaming est SSE/NATS au lieu de Socket.IO (catégorie 3 — Limitation technique).

---

### 3.5. Model selector

**Comportement Open-WebUI (référence) :**
- Popover ancré au bouton, porté dans le DOM (évite le clipping).
- Recherche textuelle Fuse ; tags ; type de connexion ; modèles épinglés ; métadonnées/capabilities.
- Menu contextuel : épingle, lien, éditer (suivant droits).
- Multi-sélection : le modèle principal peut devenir comparaison multi-réponses.
- « Set as default » et épingler = préférence utilisateur, pas modification globale.

**Décision ETHAN :** Conserver intégralement.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Ouverture | Clic sur le bouton modèle → popover ancré, porté dans le DOM |
| Recherche | Filtre flou (Fuse) sur nom, tags, provider |
| Affichage | Nom, tags, type de connexion, capabilities, badge épinglé |
| Multi-sélection | Checkbox ; chaque modèle sélectionné crée un assistant dans le chat |
| Menu contextuel | Épingler, définir par défaut, éditer (si `write_access`) |
| Persistance | `pinnedModels` + modèle par défaut dans `GET/PUT /users/{id}/settings` |
| Données | `GET /models` (agrégation providers + fiches custom) |

**Différences autorisées :** Aucune.

---

### 3.6. Composer

**Comportement Open-WebUI (référence) :**
- Une seule zone de saisie riche (`RichTextInput`) ; focus global.
- Menu d'entrée : joindre fichier/page, choisir knowledge base, conversation, note, intégration, terminal.
- Sélections visibles et supprimables au-dessus/près de l'input.
- Commandes slash : prompts, modèles, knowledge, skills, emojis.
- Sélection d'une skill → mention structurée `<$skillId|label>` dans l'éditeur.
- Toggles Web Search, image generation, code interpreter, tools — seulement si modèle + permissions pertinents.
- Bouton principal devient stop quand `generating` ; queue pour nouveaux messages.
- Entrées physiques : collage texte volumineux, drop, presse-papiers image, micro/dictée, voice mode.
- Modals pour variables de prompt manquantes ; jamais de remplissage silencieux.

**Décision ETHAN :** Conserver intégralement.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Saisie | Rich text (Tiptap/ProseMirror ou équivalent) ; focus global `chat-input` |
| Menu d'entrée | Bouton `+` → menu : Fichiers, Knowledge, Conversation, Note, Intégration, Terminal |
| Sélections actives | Chips supprimables au-dessus de l'input (fichiers, knowledge, skills, tools) |
| Commandes slash | `/` → prompts, modèles, knowledge, skills, emojis |
| Mention skill | `<$skillId|label>` inséré ; extrait en `skill_ids` à l'envoi ; retiré du prompt |
| Toggles | Web Search, Image, Code Interpreter, Tools — visibles seulement si capability modèle + permission |
| Stop/Queue | Bouton stop pendant génération ; file de messages en attente |
| Upload | Drop, collage, presse-papiers image → `POST /files` (multipart) |
| Variables | Modal de saisie si variable manquante ; jamais de remplissage silencieux |
| Envoi | `POST /chat/completions` avec `{ prompt, files, model_ids, tool_ids, skill_ids, filter_ids, features, parent_id }` |

**Différences autorisées :** Aucune.

---

### 3.7. Attachments

**Comportement Open-WebUI (référence) :**
- Chips/items avec progression et erreur de traitement.
- Retirer avant envoi ; overlay de fichiers ; preview/file nav.
- Un fichier sélectionné est soit image multimodale, soit contexte retrieval.
- Cycle visible « upload → processing stream → disponible/erreur ».

**Décision ETHAN :** Conserver intégralement.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Upload | `POST /files` (multipart) → réponse `{ id, filename, content_type, size, status }` |
| Progression | Événement `file.processing` → `file.ready` / `file.error` (SSE) |
| États | `uploading` → `processing` → `ready` / `error` ; affichés comme chips |
| Retrait | Clic sur la chip → retiré de la sélection avant envoi |
| Preview | Overlay fichiers avec aperçu ; file navigator |
| Type | Image → `image_url` multimodale ; autre → contexte retrieval |
| Données | `GET /files`, `GET /files/{id}`, `GET /files/{id}/process/status` |

**Différences autorisées :** Aucune.

---

### 3.8. Tool selection

**Comportement Open-WebUI (référence) :**
- Bouton outils/serveurs + modal de sélection (`ToolServersModal`).
- Sélection par `tool_ids` ; serveurs d'outils directs.
- Valves configurées selon droits.

**Décision ETHAN :** Conserver l'UX. L'exécution est Core (`ToolManager`).

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Modal | Liste des tools + serveurs ; recherche ; toggle par tool |
| Sélection | `tool_ids` envoyés dans `POST /chat/completions` |
| Valves | Modal de configuration par tool (si permission) |
| Serveurs | `GET /v1/tools/servers` ; connexion directe utilisateur si feature activée |
| Données | `GET /v1/tools`, `GET /v1/tools/servers` |
| Exécution | Côté Core uniquement ; la WebUI affiche `chat.tool.call` / `chat.tool.result` |

**Différences autorisées :** Aucune sur l'UX.

---

### 3.9. Knowledge selection

**Comportement Open-WebUI (référence) :**
- Menu Input `Knowledge` + commande `/` `Commands/Knowledge`.
- Modèle peut embarquer `meta.knowledge`.
- Sources injectées dans le contexte puis émises à `Citations.svelte`.

**Décision ETHAN :** Conserver intégralement.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Sélection | Menu ou commande `/` → liste des bases → sélection multiple |
| Affichage | Chips supprimables dans le composer |
| Envoi | `knowledge_ids` dans `POST /chat/completions` |
| Citations | `chat.sources` → `Citations.svelte` à proximité du message |
| Données | `GET /v1/knowledge` |

**Différences autorisées :** Aucune.

---

### 3.10. Skill selection

**Comportement Open-WebUI (référence) :**
- Commande `/` `Commands/Skills` insère une mention `<$skillId|label>`.
- `Chat.svelte` extrait en `skill_ids` et retire la mention du prompt.
- Union des mentions utilisateur et `model.meta.skillIds`.
- Skill explicitement choisie → contenu complet injecté en message système ; skill attachée au modèle → inventaire id/nom/description.

**Décision ETHAN :** Conserver intégralement.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Insertion | Commande `/` → mention `<$skillId|label>` dans l'éditeur |
| Extraction | À l'envoi : `skill_ids` extraits ; mention retirée du prompt |
| Activation | Union mentions + `model.meta.skillIds` ; vérification ACL + `is_active` côté Core |
| Injection | Skill choisie → contenu complet en message système ; skill de modèle → inventaire |
| Données | `GET /v1/skills` |

**Différences autorisées :** Aucune.

---

### 3.11. Settings

**Comportement Open-WebUI (référence) :**
- `SettingsModal` : General, Interface, Connections, Integrations, Personalization, Audio, Data Controls, Account, About.
- Recherche de réglage intégrée.
- Admin Settings séparé sous `/admin/settings/[tab]` : connections, tool/terminal servers, modèles par défaut, bannières, code execution, retrieval/audio/images/pipelines.
- Préférences utilisateur persistées dans `User.settings` JSON.

**Décision ETHAN :** Conserver la structure (modal user + admin séparé). Adapter la persistance à `ConfigurationService` + settings utilisateur.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Modal user | Onglets General, Interface, Connections, Integrations, Personalization, Audio, Data Controls, Account, About |
| Recherche | Champ de recherche filtrant les réglages |
| Persistance user | `GET/PUT /users/{id}/settings` (préférences UI, modèles épinglés, mémoire, audio, ergonomie) |
| Admin | `/admin/settings/[tab]` ; données via `GET /config` + `GET/PUT /config/{domain}` |
| Gating | Onglets admin visibles seulement si admin |
| Données | `GET /config`, `GET/PUT/PATCH /config/{domain}`, `GET/PUT /users/{id}/settings` |

**Différences autorisées :** Persistance via `ConfigurationService` ETHAN (catégorie 1 — Nécessité ETHAN).

---

### 3.12. Dialogs

**Comportement Open-WebUI (référence) :**
- Overlays spécialisés au changement de page pour les actions contextuelles : recherche, chats archivés/partagés, fichiers, tagging, partage, réglages, raccourcis, terminal, valves, OAuth, confirmations.
- Stores `show*` = état de présentation ; données rechargées depuis API après mutations.
- Fermeture par Escape ; focus via DOM.

**Décision ETHAN :** Conserver intégralement.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Type | Modal centré, drawer latéral, popover ancré — selon le contexte |
| Fermeture | Escape + clic backdrop |
| Focus | Focus initial dans le dialog ; retour au déclencheur à la fermeture |
| Données | Rechargées depuis API après mutation (jamais d'état métier local durable) |
| Confirmations | Suppressions et opérations à portée large → confirmation explicite |

**Différences autorisées :** Aucune.

---

### 3.13. Dropdowns

**Comportement Open-WebUI (référence) :**
- Menus contextuels ancrés ; actions au survol ; tooltips avec libellé accessible.
- Fermeture par Escape ; clic extérieur.

**Décision ETHAN :** Conserver intégralement.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Ancrage | Popover ancré au déclencheur, porté dans le DOM (évite clipping) |
| Actions | Visibles au survol sur desktop ; toujours accessibles au clavier/tactile |
| Accessibilité | `aria-haspopup`, `aria-expanded`, tooltips avec libellé |
| Fermeture | Escape + clic extérieur |

**Différences autorisées :** Aucune.

---

### 3.14. Cards

**Comportement Open-WebUI (référence) :**
- Registre Workspace : liste/recherche/pagination ; chaque ressource = carte avec menu.
- Patterns : `ViewSelector`, tags, visibilité, access control, import/export, clone.

**Décision ETHAN :** Conserver intégralement.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Carte | Titre, description, tags, badges (visibilité, type), menu d'actions au survol |
| Actions | Éditer, cloner, exporter, importer, supprimer, access control |
| Vue | Liste ou grille (`ViewSelector`) |
| Pagination | Chargement paginé depuis l'API |

**Différences autorisées :** Aucune.

---

### 3.15. Notifications

**Comportement Open-WebUI (référence) :**
- Toasts (`svelte-sonner`) : succès, erreur de connexion, manque de permission, reconnexion.
- Alerte de reconnexion Socket.IO au layout racine ; recharge du client si version/deployment ID changent.
- État « compte pending » bloque l'applicatif.

**Décision ETHAN :** Conserver le système de toasts. Adapter la reconnexion au protocole SSE/NATS.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Toasts | Succès (vert), erreur (rouge), avertissement (ambre), info (neutre) |
| Permission | Toast « permission refusée » quand l'API retourne 403 |
| Reconnexion | Bandeau « reconnexion… » quand le flux SSE/WebSocket se coupe ; reconnexion automatique |
| Version | Rechargement du client si `version`/`deployment_id` changent |
| Pending | Écran bloquant si compte en attente |

**Différences autorisées :** Protocole de reconnexion SSE/NATS au lieu de Socket.IO (catégorie 3 — Limitation technique).

---

### 3.16. Context menus

**Comportement Open-WebUI (référence) :**
- Actions denses invisibles jusqu'au survol, mais restent des boutons.
- Tooltip + libellé accessible.
- Menu contextuel par ressource (chat, modèle, skill, tool, knowledge).

**Décision ETHAN :** Conserver intégralement.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Déclencheur | Clic droit ou bouton `⋯` |
| Contenu | Actions selon permission (`write_access`, admin) |
| Accessibilité | Boutons avec `aria-label` ; navigation clavier |
| Fermeture | Escape + clic extérieur |

**Différences autorisées :** Aucune.

---

### 3.17. Search

**Comportement Open-WebUI (référence) :**
- Overlay de recherche global (`Ctrl+K`) ; recherche dans chats, fichiers, etc.
- Recherche de modèles dans le selector (Fuse).

**Décision ETHAN :** Conserver l'overlay. La recherche globale est une capacité Core à créer (voir mapping §14).

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Ouverture | `Ctrl+K` ou clic sur la barre de recherche |
| Portée | Chats, fichiers, knowledge, skills, tools, prompts, notes |
| Résultats | Groupés par type ; navigation clavier ; entrée → ouvre la ressource |
| Données | Endpoint de recherche globale ETHAN (à créer dans Core) |

**Différences autorisées :** Aucune sur l'UX.

---

### 3.18. Mobile / responsive

**Comportement Open-WebUI (référence) :**
- Breakpoint métier à `768px` : sidebar mobile fermée, navs secondaires scrollables, boutons toggle visibles.
- Panes de contrôle désactivés/fermés sur mobile.
- Drawer overlay pour sidebar.

**Décision ETHAN :** Conserver intégralement.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Breakpoint | `768px` |
| Sidebar | Fermée par défaut ; drawer overlay avec backdrop |
| Navs secondaires | Onglets horizontaux scrollables |
| Panes | Chat Controls, artefacts, embeds — fermés/désactivés sur mobile |
| Composer | Toggles réduits ; accès via menu d'entrée |

**Différences autorisées :** Aucune.

---

### 3.19. Dark / light mode

**Comportement Open-WebUI (référence) :**
- Thème `system` + préférences UI centralisées.
- Interface Settings : échelle de texte, contraste, direction de chat, largeur, code, rich input, background, comportements de scroll.

**Décision ETHAN :** Conserver intégralement.

**Spécification exploitable :**

| Élément | Spécification |
|---|---|
| Thème | `light` / `dark` / `system` ; persisté dans les préférences utilisateur |
| Variables | Tokens CSS (couleurs, espacements, typographie) |
| Préférences UI | Échelle de texte, contraste, direction de chat, largeur, code, rich input, background, scroll |
| Persistance | `GET/PUT /users/{id}/settings` |

**Différences autorisées :** Aucune.

---

## 4. Différences ETHAN obligatoires

### 4.1. Auth (catégorie 1 — Nécessité ETHAN)

| Élément Open-WebUI | Élément ETHAN |
|---|---|
| Token dans `localStorage` | Cookie HttpOnly `ethan_token` + proxy Next → Bearer |
| Auth Open-WebUI (DB SQLAlchemy) | JWT ETHAN + `UserManager` Core |
| Register Open-WebUI | Register ETHAN (à corriger : persistance en base) |

### 4.2. Temps réel (catégorie 3 — Limitation technique)

| Élément Open-WebUI | Élément ETHAN |
|---|---|
| Socket.IO (`/ws/socket.io`) | SSE (`GET /events`) ou WebSocket ETHAN, alimenté par NATS |
| Heartbeat 30s | Heartbeat du protocole ETHAN |
| Événements Socket.IO | Événements `chat.*`, `file.*`, `task.*` (voir architecture cible §4.2) |

### 4.3. Code interpreter (catégorie 3 — Limitation technique)

| Élément Open-WebUI | Élément ETHAN |
|---|---|
| Worker Pyodide navigateur | Exécution serveur (Core) — jamais de code exécuté dans le navigateur |

### 4.4. Terminal (catégorie 3 — Limitation technique)

| Élément Open-WebUI | Élément ETHAN |
|---|---|
| XTerm + serveurs de terminal Open-WebUI | Terminal serveur ETHAN (capacité Core à créer) ; XTerm conservé comme rendu |

### 4.5. Agents / Missions / Goals (catégorie 4 — Différence fonctionnelle obligatoire)

ETHAN possède des capacités absentes d'Open-WebUI. Elles doivent être exposées
dans la sidebar et/ou le Workspace :

| Capacité | Entrée UX | Données |
|---|---|---|
| Agents | Sidebar → Agents ; Workspace → Agents | `GET/POST /v1/agents` |
| Missions | Sidebar → Missions ; Dashboard | `GET/POST /v1/missions` |
| Goals | Sidebar → Goals ; Planner | `GET/POST /v1/goals` |

### 4.6. Observabilité (catégorie 4 — Différence fonctionnelle obligatoire)

| Capacité | Entrée UX | Données |
|---|---|---|
| Logs | Sidebar → Logs | Endpoint logs ETHAN (à créer) |
| Flux | Sidebar → Flux | `GET /v1/flux` |
| Health | Admin → Health | `GET /health/detailed` |

---

## 5. Règles de décision pour tout futur écart

Avant d'introduire une différence ETHAN/Open-WebUI :

1. **Identifier le comportement Open-WebUI exact** (référence).
2. **Tenter de conserver** ce comportement.
3. Si impossible ou incohérent, **classer la différence** dans une des 4 catégories :
   - 1 — Nécessité ETHAN
   - 2 — Amélioration UX démontrable (avec preuve)
   - 3 — Limitation technique
   - 4 — Différence fonctionnelle obligatoire
4. **Documenter** la différence dans ce document (tableau §2 + section détaillée).
5. **Implémenter** uniquement après classification.

**Toute différence non classée est un défaut de parité et doit être rejetée.**

---

## 6. Matrice de conformité (à remplir à chaque itération)

| Élément UX | Conforme | Écart classé | Catégorie | Commentaire |
|---|---|---|---|---|
| Sidebar | ☐ | ☐ | — | |
| Navigation | ☐ | ☐ | — | |
| Workspace | ☐ | ☐ | — | |
| Chat | ☐ | ☐ | — | |
| Model selector | ☐ | ☐ | — | |
| Composer | ☐ | ☐ | — | |
| Attachments | ☐ | ☐ | — | |
| Tool selection | ☐ | ☐ | — | |
| Knowledge selection | ☐ | ☐ | — | |
| Skill selection | ☐ | ☐ | — | |
| Settings | ☐ | ☐ | — | |
| Dialogs | ☐ | ☐ | — | |
| Dropdowns | ☐ | ☐ | — | |
| Cards | ☐ | ☐ | — | |
| Notifications | ☐ | ☐ | — | |
| Context menus | ☐ | ☐ | — | |
| Search | ☐ | ☐ | — | |
| Mobile/responsive | ☐ | ☐ | — | |
| Dark/light mode | ☐ | ☐ | — | |
| Auth | ☐ | ☐ | 1 | Cookie HttpOnly ETHAN |
| Temps réel | ☐ | ☐ | 3 | SSE/NATS au lieu de Socket.IO |
| Code interpreter | ☐ | ☐ | 3 | Exécution serveur |
| Terminal | ☐ | ☐ | 3 | Terminal serveur ETHAN |
| Agents/Missions/Goals | ☐ | ☐ | 4 | Capacités ETHAN natives |
| Observabilité | ☐ | ☐ | 4 | Logs/Flux/Health ETHAN |