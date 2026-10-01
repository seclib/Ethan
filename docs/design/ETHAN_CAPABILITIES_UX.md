# ETHAN — Design UX des Capacités (Knowledge, Skills, Tools, Memory)

> **Statut** : Design
> **Référence** : `docs/architecture/ETHAN_KNOWLEDGE_SKILLS_TOOLS_MCP.md`
> **Principe** : La WebUI révèle les capacités ETHAN. Elle ne les définit pas. Chaque écran affiche l'état du Core et envoie des actions via l'API.

---

## 1. Principes UX

1. **Séparation stricte des concepts** : Memory ≠ Knowledge ≠ Conversation ≠ RAG.
2. **Sélection dans le chat** : chaque capacité est sélectionnable dans le composer (comme Open-WebUI).
3. **État visible** : activation/désactivation visible en un coup d'œil.
4. **Citations** : toute réponse utilisant du RAG affiche ses sources.
5. **Appels d'outils** : toute exécution d'outil est affichée (nom, durée, statut).

---

## 2. Navigation

```
Dashboard
├── Assistant (chat)
├── Knowledge        ← Collections + Documents
├── Skills           ← Liste + activation
├── Tools            ← Serveurs MCP + activation
├── Memory           ← Faits persistants
├── Documents        ← (alias Knowledge, pour compat)
├── Models / Providers
├── Agents / Missions / Goals
└── Settings
```

---

## 3. Écran Knowledge

### Objectif
Gérer les collections de documents et leur ingestion RAG.

### Layout
```
┌─────────────────────────────────────────────┐
│ Knowledge                                    │
│ ┌──────────────┬──────────────────────────┐  │
│ │ Collections  │ Documents de la          │  │
│ │ [📚 Docs]    │ collection sélectionnée  │  │
│ │ [📄 Manuel]  │  - fichier.pdf (2.1 MB)  │  │
│ │ [+ Nouvelle] │  - notes.md (12 KB)      │  │
│ │              │  [+ Upload]              │  │
│ └──────────────┴──────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### Actions
- **Créer une collection** : nom + description.
- **Upload** : PDF, TXT, MD, DOCX → ingestion RAG (chunking + embeddings).
- **Supprimer** un document ou une collection.
- **Sélectionner** dans le chat via le composer (icône 📚).

### API consommée
- `GET/POST /v1/knowledge/collections`
- `GET/POST /v1/knowledge/collections/{id}/documents`
- `DELETE /v1/knowledge/collections/{id}/documents/{doc_id}`
- `POST /v1/rag/retrieve` (aperçu retrieval)

---

## 4. Écran Skills

### Objectif
Lister, créer, éditer et activer les skills injectées dans le system prompt.

### Layout
```
┌─────────────────────────────────────────────┐
│ Skills                                       │
│ ┌─────────────────────────────────────────┐  │
│ │ ⚡ Code Review        [● Actif] [✎] [🗑] │  │
│ │    Analyse le code et propose des fixes │  │
│ ├─────────────────────────────────────────┤  │
│ │ ⚡ Traduction          [○ Inactif] [✎]   │  │
│ │    Traduit entre langues                │  │
│ └─────────────────────────────────────────┘  │
│ [+ Nouvelle skill]                            │
└─────────────────────────────────────────────┘
```

### Actions
- **Créer** : nom + description + contenu Markdown.
- **Éditer** : éditeur Markdown avec aperçu.
- **Activer/désactiver** : toggle.
- **Sélectionner** dans le chat via le composer (icône ⚡).

### API consommée
- `GET/POST /v1/skills`
- `GET/PUT/DELETE /v1/skills/{id}`
- `POST /v1/skills/{id}/toggle`

---

## 5. Écran Tools / MCP

### Objectif
Configurer les serveurs d'outils (MCP) et activer les outils disponibles.

### Layout
```
┌─────────────────────────────────────────────┐
│ Tools / MCP                                  │
│ ┌─────────────────────────────────────────┐  │
│ │ 🔌 Serveur MCP Local    [● Connecté]    │  │
│ │    http://localhost:8000/mcp            │  │
│ │    ┌─────────────────────────────────┐  │  │
│ │    │ ☑ web_search   Recherche web    │  │  │
│ │    │ ☑ read_file    Lecture fichier  │  │  │
│ │    │ ☐ write_file   Écriture fichier │  │  │
│ │    └─────────────────────────────────┘  │  │
│ ├─────────────────────────────────────────┤  │
│ │ 🔌 Serveur GitHub        [○ Déconnecté] │  │
│ │    https://api.github.com/mcp           │  │
│ └─────────────────────────────────────────┘  │
│ [+ Ajouter un serveur]                       │
└─────────────────────────────────────────────┘
```

### Actions
- **Ajouter un serveur** : nom + URL + type d'auth.
- **Activer/désactiver** un serveur ou un outil individuel.
- **Tester la connexion**.
- **Affichage dans le chat** : cartes d'appels d'outils (nom, durée, statut).

### API consommée
- `GET/POST /v1/tools/servers`
- `GET/PUT/DELETE /v1/tools/servers/{id}`
- `PUT /v1/tools/servers/{id}/status`

---

## 6. Écran Memory

### Objectif
Gérer les faits persistants sur l'utilisateur, distincts des documents.

### Layout
```
┌─────────────────────────────────────────────┐
│ Memory                                       │
│ ┌─────────────────────────────────────────┐  │
│ │ 🧠 L'utilisateur préfère Python         │  │
│ │    Ajouté il y a 3 jours        [🗑]    │  │
│ ├─────────────────────────────────────────┤  │
│ │ 🧠 Projet actif : ETHAN WebUI           │  │
│ │    Ajouté il y a 1 semaine      [🗑]    │  │
│ └─────────────────────────────────────────┘  │
│ [+ Ajouter un fait]                          │
│ [🔍 Rechercher...]                           │
└─────────────────────────────────────────────┘
```

### Actions
- **Ajouter un fait** : texte libre.
- **Supprimer** un fait.
- **Rechercher** dans les faits.
- **Injection** : les faits actifs sont injectés dans le system prompt du chat.

### API consommée
- `GET/POST /v1/memory/facts`
- `DELETE /v1/memory/facts/{id}`
- `GET /v1/memory/search`

---

## 7. Sélection dans le Chat (Composer)

Le composer affiche des boutons de sélection pour chaque capacité :

```
┌─────────────────────────────────────────────┐
│ [📎] [📚] [⚡] [🔌] [🧠]                     │
│ ┌─────────────────────────────────────────┐  │
│ │ Message...                        ⏎ Entrée│  │
│ └─────────────────────────────────────────┘  │
│ [Envoyer]                                    │
└─────────────────────────────────────────────┘
```

- **📎** : fichiers locaux (upload temporaire).
- **📚** : collections Knowledge sélectionnées.
- **⚡** : skills actives sélectionnées.
- **🔌** : outils MCP activés.
- **🧠** : faits mémoire (toujours actifs, indicateur).

### Payload envoyé au pipeline
```json
{
  "message": "...",
  "chat_id": "...",
  "provider_id": "ollama",
  "model": "qwen2.5-coder",
  "skill_ids": ["skill-1"],
  "collection_ids": ["collection-1"],
  "tool_ids": ["tool-1"],
  "file_ids": []
}
```

---

## 8. Affichage dans le Chat

### Citations RAG
Sous la réponse, une section "Sources" liste les documents utilisés :
```
Sources
[1] Documentation ETHAN — architecture.md
[2] Manuel utilisateur — chapitre 3
```

### Appels d'outils
Chaque appel d'outil est une carte :
```
🔌 web_search — Recherche "ETHAN architecture"
   ✓ Succès · 1.2s
```

### Faits mémoire
Indicateur discret dans le header du message assistant :
```
🧠 2 faits mémoire utilisés
```

---

## 9. Règles de non-mélange

| Écran | Contient | Ne contient PAS |
|---|---|---|
| Knowledge | Collections, documents, ingestion | Faits personnels, historique chat |
| Skills | Skills, activation, édition | Documents, outils |
| Tools | Serveurs MCP, outils, activation | Skills, documents |
| Memory | Faits persistants utilisateur | Documents, historique chat |
| Assistant | Chat, sélection capacités, citations | Gestion des capacités |

---

## 10. Implémentation (ordre)

1. **Core** : `KnowledgeCollection` (collections de documents RAG).
2. **Core** : injection des faits mémoire dans le `ChatPipeline`.
3. **API** : routes `/v1/knowledge/collections`.
4. **WebUI** : page Knowledge (collections + upload).
5. **WebUI** : page Skills (liste + activation + édition).
6. **WebUI** : page Tools (serveurs + activation).
7. **WebUI** : page Memory (faits).
8. **WebUI** : sélecteurs dans le composer + affichage citations/outils.