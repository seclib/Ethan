# Open-WebUI — Référence UX

## Nature de l'expérience

L'UX observée est une SPA desktop-first à densité élevée, conçue comme une surface de travail conversationnelle : la conversation reste centrale, tandis que les capacités (modèle, sources, tools, fichiers, paramètres, artefacts) apparaissent à proximité de l'action sous forme de menus, badges, panneaux et modals. Les composants source sont Svelte/Tailwind; cette référence décrit leurs comportements, pas une reproduction graphique à partir d'une capture.

## Shell et navigation

| Zone | Comportement observé | Composants responsables |
|---|---|---|
| Shell | hauteur `100dvh`, contenu scrollable, sidebar et contenu flexibles; toasts globaux et modals hors du flux. | `routes/(app)/+layout.svelte`, root `+layout.svelte` |
| Sidebar | ouverte sur desktop selon `localStorage.sidebar`, fermée par défaut mobile; bouton compact quand fermée, overlay/mobile drawer quand ouverte. | `layout/Sidebar.svelte`, stores `showSidebar`, `mobile`, `sidebarWidth` |
| Navigation secondaire | Workspace/Admin : onglets horizontaux scrollables, actif par pathname; menu hamburger sur mobile. | `workspace/+layout.svelte`, `admin/+layout.svelte` |
| Gating | l'item n'est pas affiché si feature/permission absente et la page redirige au montage. | layout Workspace/Admin, `Sidebar.svelte` |
| Commandes globales | recherche, nouveau chat, focus composer, copie dernière réponse/code, sidebar, settings, temporaire, régénération. | `shortcuts.ts`, `(app)/+layout.svelte` |

La sidebar n'est pas seulement une navigation : elle est la bibliothèque opérationnelle de l'utilisateur. Elle mélange entrées applicatives épinglables, favoris de modèles, notes, channels, dossiers et l'historique de chats. Le résultat est une continuité entre « commencer », « retrouver », et « organiser » plutôt qu'une page Conversations séparée.

## Parcours principal : de l'intention à la réponse

```text
Choisir modèle(s) → préparer contexte → écrire/joindre → envoyer
            ↓                              ↓
  badges/toggles dans le composer    nœud user + placeholder assistant
                                           ↓
                        statuts, tool calls, sources, contenu en flux
                                           ↓
                   actions de réponse, branche, sauvegarde, follow-ups
```

### Composer

Le composer est riche mais reste visuellement une seule zone de saisie. `RichTextInput` reçoit le focus global; le menu d'entrée concentre les actions secondaires : joindre un fichier/une page, choisir une knowledge base, une conversation, une note, une intégration ou un terminal. Les sélections deviennent des éléments visibles et supprimables au-dessus/près de l'input au lieu d'être cachées dans un formulaire.

Les commandes slash couvrent prompts, modèles, knowledge, skills et emojis. La sélection d'une skill écrit une mention structurée dans l'éditeur, ce qui rend son activation lisible avant envoi. Les toggles Web Search, image generation, code interpreter et tools n'apparaissent que si le modèle et les permissions les rendent pertinents. Le bouton principal devient arrêt lorsque `generating` est vrai; une queue permet de conserver de nouveaux messages plutôt que de bloquer la saisie.

Les entrées physiques sont traitées : collage de texte volumineux, drop, presse-papiers image, micro/dictée et voice mode. Des modals demandent les variables de prompt ou les confirmations d'actions; l'interface ne remplit pas silencieusement une variable manquante.

### Sélecteur de modèles

Le sélecteur est un popover ancré au bouton, porté dans le DOM pour éviter les problèmes de clipping. Il combine recherche textuelle Fuse, tags, type de connexion, modèles épinglés, métadonnées/capabilities et un menu contextuel (épingle, lien, éditer suivant droits). Il accepte plusieurs sélecteurs : le modèle principal peut devenir une comparaison multi-réponses. « Set as default » et épingler produisent une préférence utilisateur, pas une modification globale du catalogue.

### Réponses et transparence d'exécution

Le message assistant est structuré en couches : en-tête identité/modèle, statut, contenu Markdown et parties spéciales (code, reasoning/details, tool calls, citations, fichiers, tasks, web results, follow-ups), puis une barre d'actions au survol. Les deltas s'ajoutent sans faire disparaître les contrôles; les sources apparaissent en citations plutôt qu'en texte noyé dans la réponse.

Actions disponibles suivant permissions et état : éditer ou sauvegarder une copie, copier, synthèse vocale, évaluer, régénérer (avec menu de variante/prompt), supprimer, déclencher les actions déclarées par le modèle. Le contenu édité préserve les blocs `details` grâce à un pré/post-traitement, ce qui évite de détruire l'historique de raisonnement lors d'une correction visuelle.

## Gestion de contexte : révéler ce qui influencera la réponse

| Contexte | Signal UX | Affordance de gestion |
|---|---|---|
| Fichiers | chips/items avec progression et erreur de traitement | retirer avant envoi, overlay de fichiers, preview/file nav |
| Knowledge | menu et commande dédiés; citations après retrieval | sélectionner collections/fichiers, gérer bases dans Workspace |
| Skills | mention dans l'input | supprimer la mention ou gérer activation/contenu dans Workspace |
| Tools/MCP | bouton outils/serveurs et modal de sélection | sélectionner, configurer valves ou connexions selon droits |
| Dossier/projet | chat déplacé dans dossier, knowledge/system prompt du projet appliqués au backend | menu de chat pour déplacer/archiver; arbre de dossiers sidebar |
| Paramètres modèle | Chat Controls, Valves, settings | panneau redimensionnable et préférences persistées |

Ce modèle rend l'état manipulable sans imposer une page de configuration avant chaque réponse. Les données métiers restent toutefois côté serveur : la clarté UX ne doit pas être confondue avec une source de vérité frontend.

## Knowledge, workspace et administration

Le Workspace propose une UX de registre : liste/recherche/pagination, création explicite, vue détail et menu par ressource. Les éléments partagent des patterns : `ViewSelector`, tags, visibilité, access control, import/export, clone et confirmation des suppressions. Les éditeurs modèles, skills et tools font porter le contenu technique dans un panneau dédié, séparé de la liste pour limiter les modifications accidentelles.

Knowledge est une navigation à deux niveaux : liste de bases puis page d'une base contenant ses fichiers, ajout de texte, import/upload, reindex/reset et permissions. Les fichiers ont un cycle visible « upload → processing stream → disponible/erreur » au lieu d'être supposés utilisables dès le drop.

L'administration est volontairement isolée sous `/admin` : Users, Analytics, Evaluations, Functions et Settings sont accessibles par une barre secondaire. Les permissions déterminent à la fois l'accès à la route et l'existence des contrôles ordinaires; les opérations à portée large passent par confirmations/modals.

## Menus et états transitoires

Open-WebUI privilégie les overlays spécialisés au changement de page pour les actions contextuelles : recherche, chats archivés/partagés, fichiers, tagging, partage, réglages, raccourcis, commandes de terminal, configuration de valves, authentification OAuth et confirmations. Les stores `show*` constituent l'état de présentation; les données sont rechargées depuis API après mutations importantes.

Les notifications `svelte-sonner` signalent succès, erreur de connexion, manque de permission et reconnexion. Le layout racine affiche une alerte de reconnexion Socket.IO et recharge le client si version/deployment ID changent. L'état « compte pending » bloque l'applicatif, et une migration IndexedDB montre un écran guidé pour exporter/supprimer les anciens chats locaux.

## Responsive et accessibilité implémentés

- Breakpoint métier à `768px` : sidebar mobile fermée, navs secondaires scrollables, boutons toggle visibles; les panes de contrôle sont désactivés/fermés sur mobile.
- Les popovers et modals ont labels/aria sur les boutons les plus critiques, focus via DOM (`chat-input`, selector) et fermeture par Escape avec les raccourcis globaux.
- Les actions denses sont souvent invisibles jusqu'au survol, mais restent des boutons, avec tooltip et libellé accessible lorsque défini.
- Thème `system` et préférences UI sont centralisés; Interface Settings couvre échelle de texte, contraste, direction de chat, largeur, code, rich input, background et comportements de scroll.

## Contraintes de conception à conserver dans ETHAN

1. Garder un composer unique, mais montrer les contextes actifs comme objets concrets.
2. Faire du chat un arbre persistant et navigable : régénérer ou éditer ne doit pas écraser silencieusement une branche.
3. Distinguer le résultat conversationnel des traces d'exécution (sources, tool calls, tâches), tout en les rendant inspectables.
4. Réserver Workspace à la gestion durable des capacités, et Admin à la configuration système; ne pas mélanger ces scopes dans le chat.
5. Appliquer les permissions avant d'afficher une action et de nouveau au backend : l'absence visuelle n'est pas une frontière de sécurité.
6. Utiliser les overlays pour garder le contexte du chat, mais fournir une route stable pour chaque ressource éditable.
