# Analyse UX — Open-WebUI comme référence visuelle pour ETHAN WebUI

**Date** : 11/08/2026  
**Statut** : Analyse UX — aucune modification de code  
**Référence** : `examples/open-webui` (v0.9.1)  
**Cible** : `interfaces/webui` (Next.js 15 + React 19)

---

## Objectif

ETHAN WebUI doit **rappeler Open-WebUI** visuellement, mais devenir le **cockpit graphique d'un OS IA** — un tableau de bord de contrôle pour le runtime ETHAN, pas seulement un chat.

---

## 1. Analyse de l'expérience utilisateur Open-WebUI

### 1.1 Layout général

**Open-WebUI** :
- Layout 3 colonnes : sidebar (gauche) + chat (centre) + panneaux contextuels (droite)
- Sidebar repliable (icône hamburger)
- Chat plein écran avec messages centrés
- Modales pour les paramètres, raccourcis, changelog
- Overlays pour onboarding, compte en attente

**ETHAN actuel** :
- Layout 2 colonnes : sidebar (gauche) + contenu (centre)
- Sidebar repliable avec groupes de navigation
- Pages dédiées par fonctionnalité (agents, missions, memory, etc.)
- Modales pour les dialogues

### 1.2 Sidebar

**Open-WebUI** :
- Liste des conversations (chats) avec recherche
- Dossiers de chats (création, renommage, suppression)
- Chats épinglés (pinned)
- Modèles épinglés (pinned models)
- Notes épinglées
- Canaux de discussion
- Menu utilisateur (profil, paramètres, raccourcis, déconnexion)
- Bouton "Nouveau chat"
- Import/export de chats
- Recherche globale (modale)

**ETHAN actuel** :
- Navigation par groupes : "Cognition & Interaction", "Orchestration & Engine", "Infrastructure & System"
- Icônes Lucide pour chaque entrée
- Pas de recherche
- Pas de dossiers
- Pas de menu utilisateur riche

### 1.3 Navigation

**Open-WebUI** :
- Navigation par URL (SvelteKit routing)
- Routes : `/` (chat), `/models`, `/workspace`, `/admin`, `/auth`
- Modales pour les actions secondaires (settings, shortcuts)
- Navigation contextuelle dans le chat (navbar)

**ETHAN actuel** :
- Navigation par URL (Next.js App Router)
- Routes : `/`, `/assistant`, `/memory`, `/knowledge`, `/documents`, `/planner`, `/missions`, `/agents`, `/tools`, `/plugins`, `/models`, `/providers`, `/terminal`, `/logs`, `/settings`
- Sidebar avec groupes
- Command palette (Ctrl+K)

### 1.4 Page chat

**Open-WebUI** :
- Messages centrés avec largeur max (~800px)
- Placeholder élégant avec suggestions
- Input riche : markdown, code, images, fichiers, web, notes, knowledge
- Streaming temps réel
- Actions par message : copier, régénérer, éditer, supprimer
- Sélecteur de modèles (dropdown avec recherche, épinglage)
- Contrôles : nouveau chat, partage, archivage
- Raccourcis clavier (Ctrl+Enter, etc.)
- Terminal intégré (xterm.js)
- Pyodide (exécution Python)

**ETHAN actuel** :
- Messages simples (texte)
- Input basique (textarea)
- Pas de streaming
- Pas de markdown
- Pas de sélecteur de modèles riche
- Pas de raccourcis clavier avancés
- Pas de terminal intégré

### 1.5 Sélection modèles

**Open-WebUI** :
- Dropdown avec recherche (Fuse.js)
- Liste des modèles avec icônes, descriptions
- Modèles épinglés en haut
- Modèles par défaut
- Modèles par utilisateur/groupe
- Actions : épingler, définir par défaut, télécharger (Ollama)
- Multi-sélection possible

**ETHAN actuel** :
- Sélecteur simple dans l'assistant
- Pas de recherche
- Pas d'épinglage
- Pas de modèles par défaut
- Pas de gestion des modèles

### 1.6 Paramètres

**Open-WebUI** :
- Modale avec onglets : General, Interface, Audio, Data Controls, Personalization, Connections, Integrations, Account, About
- Recherche dans les paramètres
- Interface : thème, langue, densité, mode contraste
- Audio : TTS, STT
- Data Controls : export/import, suppression
- Personalization : modèles par défaut, suggestions
- Connections : providers LLM, connexions
- Integrations : Google Drive, OneDrive, etc.
- Account : profil, avatar, mot de passe

**ETHAN actuel** :
- Page Settings basique
- Section AI Providers (configuration providers)
- Pas de recherche
- Pas de thèmes
- Pas d'audio
- Pas de data controls

### 1.7 Composants

**Open-WebUI** (~200 composants) :
- **Common** : Badge, Button, Checkbox, CodeEditor, ConfirmDialog, Drawer, Dropdown, EmojiPicker, FileItem, Folder, ImagePreview, Loader, Modal, Pagination, PDFViewer, RichTextInput, Select, Selector, SensitiveInput, Spinner, Switch, Tags, Textarea, Tooltip, Valves
- **Chat** : Chat, Messages, MessageInput, ModelSelector, Navbar, SettingsModal, ShareChatModal, ShortcutsModal, Suggestions, Tags, ToolServersModal, XTerminal
- **Layout** : Sidebar, Navbar, Overlays (AccountPending, UpdateInfoToast)
- **Admin** : Users, Models, Config, etc.
- **Workspace** : Documents, Knowledge, Tools, Functions, Skills

**ETHAN actuel** (~30 composants) :
- **UI** : Alert, Avatar, Badge, Button, Card, CommandPalette, Dialog, Input, Progress, Separator, Skeleton, Spinner, Switch, Table, Textarea, Toast, Tooltip
- **Layout** : Sidebar, Topbar, GlobalCommandPalette, GlobalInspector, GlobalShortcuts, MissionControlOverlay, AtmosphereLayer
- **Shared** : EventStream, MetricCard, ModelSelector, TasksWidget

### 1.8 Thèmes

**Open-WebUI** :
- Thème clair/sombre/système
- Thèmes personnalisés (rosepine, rosepine-dawn)
- Mode contraste élevé
- Personnalisation par utilisateur
- CSS variables

**ETHAN actuel** :
- Thème sombre par défaut
- ThemeProvider (clair/sombre)
- Pas de thèmes personnalisés
- Pas de mode contraste

### 1.9 Interactions

**Open-WebUI** :
- Animations fluides (fade, slide, fly)
- Drag & drop (sortablejs pour les chats)
- Raccourcis clavier complets
- Tooltips contextuels
- Notifications toast (svelte-sonner)
- Streaming temps réel
- Autoscroll des messages
- Édition inline des messages

**ETHAN actuel** :
- Animations Framer Motion (page transitions)
- Command palette (Ctrl+K)
- Raccourcis clavier basiques
- Toasts (custom)
- Pas de drag & drop
- Pas de streaming

### 1.10 Responsive

**Open-WebUI** :
- Breakpoint mobile (768px)
- Sidebar masquée sur mobile
- Chat plein écran sur mobile
- Modales adaptatives
- Menu hamburger

**ETHAN actuel** :
- Sidebar repliable
- Layout adaptatif
- Pas de breakpoint mobile dédié

### 1.11 Notifications

**Open-WebUI** :
- Toasts (svelte-sonner) : succès, erreur, info
- Notifications de mise à jour
- Notifications de téléchargement de modèles
- Bannières système
- Notifications audio

**ETHAN actuel** :
- Toasts custom (success, error, warning, info)
- Pas de notifications système
- Pas de bannières

### 1.12 États système

**Open-WebUI** :
- Spinner/Loader pendant les chargements
- États vides élégants (placeholder)
- États d'erreur avec messages clairs
- Indicateurs de connexion (socket)
- Indicateurs de téléchargement de modèles
- Indicateurs d'utilisation (usage pool)

**ETHAN actuel** :
- Spinner basique
- États vides simples
- États d'erreur basiques
- Pas d'indicateurs système riches

---

## 2. Éléments à conserver exactement

### 2.1 Depuis Open-WebUI

| Élément | Raison |
|---------|--------|
| **Placeholder du chat** | Suggestions élégantes, centré, invite à l'action |
| **Sélecteur de modèles** | Dropdown avec recherche, épinglage, descriptions |
| **Input riche** | Markdown, code, fichiers, images, web, notes, knowledge |
| **Actions par message** | Copier, régénérer, éditer, supprimer |
| **Streaming temps réel** | Affichage progressif des réponses |
| **Raccourcis clavier** | Ctrl+Enter, Ctrl+K, etc. |
| **Tooltips contextuels** | Aide au survol |
| **Toasts** | Notifications succès/erreur/info |
| **Thème clair/sombre** | Bascule système |
| **Modale de paramètres** | Onglets + recherche |
| **Menu utilisateur** | Profil, paramètres, raccourcis, déconnexion |
| **États vides** | Placeholder élégants |
| **Spinner/Loader** | Indicateurs de chargement |
| **Terminal intégré** | xterm.js |
| **Éditeur riche** | Tiptap (ProseMirror) |

### 2.2 Depuis ETHAN actuel

| Élément | Raison |
|---------|--------|
| **Sidebar par groupes** | Navigation claire par domaines ETHAN |
| **Command palette** | Accès rapide aux actions |
| **Mission Control Overlay** | Vue d'ensemble des missions |
| **Global Inspector** | Inspection des agents/goals/missions |
| **Atmosphere Layer** | Ambiance visuelle unique |
| **Pages dédiées** | Agents, missions, memory, knowledge, etc. |
| **WebSocket Provider** | Événements temps réel ETHAN |

---

## 3. Éléments à améliorer

| Élément | Amélioration |
|---------|--------------|
| **Sidebar** | Ajouter recherche, dossiers, chats épinglés, modèles épinglés |
| **Navigation** | Ajouter breadcrumbs, navigation contextuelle |
| **Page chat** | Ajouter streaming, markdown, code highlighting, actions par message |
| **Sélection modèles** | Ajouter recherche, épinglage, descriptions, modèles par défaut |
| **Paramètres** | Ajouter onglets, recherche, thèmes, audio, data controls |
| **Composants** | Ajouter Dropdown, Select, Switch, Tooltip, Modal, Drawer, ConfirmDialog |
| **Thèmes** | Ajouter thèmes personnalisés, mode contraste élevé |
| **Interactions** | Ajouter drag & drop, animations fluides, édition inline |
| **Responsive** | Ajouter breakpoint mobile, sidebar masquée sur mobile |
| **Notifications** | Ajouter bannières système, notifications de mise à jour |
| **États système** | Ajouter indicateurs de connexion, d'utilisation, de téléchargement |

---

## 4. Éléments à remplacer

| Élément | Remplacement |
|---------|--------------|
| **Backend Open-WebUI** | API ETHAN (interfaces/api) — pas de backend dans la WebUI |
| **Stockage Open-WebUI** | Stores ETHAN (core/state) — pas de base de données dans la WebUI |
| **Auth Open-WebUI** | Auth ETHAN (core/auth) — JWT via cookie HttpOnly |
| **Gestion modèles Open-WebUI** | ProviderManager ETHAN (core/llm) |
| **Gestion providers Open-WebUI** | ProviderManager ETHAN (core/llm) |
| **RAG Open-WebUI** | RAG ETHAN (core/rag) |
| **Mémoire Open-WebUI** | Mémoire ETHAN (core/memory, core/facts) |
| **WebSocket Open-WebUI** | WebSocket ETHAN (bus NATS) |
| **Svelte stores** | Zustand + React Context |
| **SvelteKit routing** | Next.js App Router |

---

## 5. Nouvelles pages nécessaires pour ETHAN

### 5.1 Pages existantes à enrichir

| Page | Enrichissement |
|------|----------------|
| **Dashboard** | Widgets temps réel : état des agents, missions actives, métriques système, flux d'événements |
| **Assistant** | Chat complet avec streaming, markdown, sélecteur de modèles, actions par message |
| **Memory** | Vue mémoire : faits, événements, recherche, visualisation graphique |
| **Knowledge** | Vue knowledge : graphe de connaissances, recherche, connexions |
| **Documents** | Gestion documents : upload, ingestion RAG, statut d'indexation |
| **Planner** | Vue planner : goals, plans, étapes, progression |
| **Missions** | Vue missions : liste, détail, étapes, approbations |
| **Agents** | Vue agents : liste, détail, statut, exécution, historique |
| **Tools** | Vue tools : liste, test, SkillLab |
| **Plugins** | Vue plugins : liste, installation, activation |
| **Models** | Vue modèles : liste réelle depuis ProviderManager, statut, téléchargement |
| **Providers** | Vue providers : configuration, test de connexion, modèles disponibles |
| **Terminal** | Terminal intégré (xterm.js) |
| **Logs** | Vue logs : flux d'événements, filtres, recherche |
| **Settings** | Paramètres avec onglets : General, Interface, Providers, Data Controls, Account |

### 5.2 Nouvelles pages

| Page | Description |
|------|-------------|
| **/system** | Vue système : état des services (NATS, Redis, PostgreSQL, API, Kernel, Modules), métriques, santé |
| **/automations** | Vue automatisations : règles, déclencheurs, actions |
| **/channels** | Vue canaux : discussions par canal, membres |
| **/notes** | Vue notes : notes épinglées, recherche |
| **/prompts** | Vue prompts : prompts prédéfinis, templates |
| **/audit** | Vue audit : journal d'audit, filtres, recherche |
| **/approvals** | Vue approbations : demandes en attente, historique |
| **/costs** | Vue coûts : budget, consommation par provider/modèle |
| **/telemetry** | Vue télémétrie : traces, métriques, observabilité |

---

## 6. Design system ETHAN

### 6.1 Principes

1. **Cockpit d'OS IA** : la WebUI est un tableau de bord de contrôle, pas juste un chat
2. **Clarté** : chaque page montre l'état réel du système ETHAN
3. **Contrôle** : l'utilisateur peut agir sur chaque élément (démarrer, arrêter, configurer)
4. **Temps réel** : les données sont mises à jour en continu via WebSocket
5. **Hiérarchie** : navigation claire par domaines (Cognition, Orchestration, Infrastructure)

### 6.2 Palette

- **Fond** : sombre (#0a0a0f) avec accents subtils
- **Primaire** : bleu ETHAN (#3b82f6)
- **Succès** : vert (#22c55e)
- **Erreur** : rouge (#ef4444)
- **Avertissement** : ambre (#f59e0b)
- **Texte** : blanc/gris (#f8fafc, #94a3b8)
- **Bordure** : gris foncé (#1e293b)

### 6.3 Typographie

- **Titres** : Inter (sans-serif, bold)
- **Corps** : Inter (sans-serif, regular)
- **Code** : JetBrains Mono (monospace)
- **Tailles** : 12px (caption), 14px (body), 16px (subtitle), 20px (title), 28px (h1)

### 6.4 Composants

- **Sidebar** : 280px, repliable, groupes, recherche, dossiers
- **Topbar** : 56px, breadcrumbs, actions contextuelles, menu utilisateur
- **Cards** : fond #111827, bordure #1e293b, radius 12px
- **Buttons** : primary (bleu), secondary (gris), ghost (transparent), danger (rouge)
- **Modals** : fond #111827, radius 16px, overlay #00000080
- **Toasts** : coin supérieur droit, auto-dismiss
- **Tooltips** : fond #1e293b, texte blanc, radius 6px

---

## 7. Conclusion

Open-WebUI est une **excellente référence UX** pour le chat IA. ETHAN WebUI doit en **reprendre les patterns UI** (placeholder, sélecteur de modèles, input riche, streaming, actions par message, raccourcis, thèmes) tout en **étendant la vision** vers un **cockpit d'OS IA** avec des pages dédiées pour chaque capacité ETHAN (agents, missions, memory, knowledge, RAG, providers, système).

La WebUI ETHAN actuelle (Next.js + React) est une **base solide** qui peut être enrichie progressivement avec les patterns UX d'Open-WebUI, sans avoir à forker le projet entier.