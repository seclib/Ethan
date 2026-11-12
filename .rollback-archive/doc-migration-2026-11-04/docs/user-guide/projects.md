# Projects

A **Project** in ETHAN is a conversation container with a knowledge scope and an
execution context. It is owned by the Core (`core/projects/ProjectManager`) and
persisted through `CoreRecordStore` (PostgreSQL durable + Redis cache). The WebUI
only projects the state and sends user actions — it never owns project logic.

## What a Project contains

| Element | Description |
|---------|-------------|
| **Conversations** | Every chat created in a project carries `project_id` (ChatStore Core). Each conversation keeps its own history and message tree. |
| **Instructions** | Free-form context injected at the top of the Core prompt for every conversation of the project. |
| **Files** | Documents uploaded to the project are extracted, chunked and embedded by the single Core RAG pipeline (`core/rag`). Delete purges the shared index. |
| **Knowledge** | RAG collection ids (`knowledge_ids`, mirrored in `collection_ids`). |
| **Skills / Tools** | Ids merged with the explicit chat selection (the request always wins). |
| **Agent** | Default agent whose persona/provider/model/skills complement the request. |
| **Provider / Model** | Default execution engine applied when the request does not specify one. |

All associations are **ids only** — no resource is copied (AGENTS.md rule).

## Using Projects from the chat

1. Open the chat (`/`). The project selector lives in the conversation's
   secondary bar (next to agent/provider/model).
2. Create a project with **+** — it is created *and activated* immediately.
3. Every new conversation (and every message sent) is automatically scoped to
   the active project: the Core resolves the project context server-side.
4. Switching projects filters the conversation list to that project only
   (conversation isolation). Chats without a project keep working
   (virtual "no project" scope).
5. **Manage project** in the selector opens the project workspace.

> The project selection is a session preference persisted in the browser
> (`localStorage`). Business state always lives in the Core; if the project was
> deleted, the stale preference is purged automatically.

## Project workspace

`/projects` lists your projects. `/projects/[id]` is the project cockpit:

- **Instructions** — name, description and the project prompt.
- **Files** — drag & drop upload, indexing status, deletion.
- **Conversations** — every conversation of the project; click to open it in
  the chat, or create a new one inside the project.
- **Configuration** — default provider/model/agent and knowledge/skills/tools
  scope.

## Execution semantics (Core-owned)

- The **conversation's project wins**: an existing conversation always keeps its
  project; a request can only attach an orphan conversation, never reassign one.
- Project context is merged, never copied: instructions are injected into the
  system prompt, skills/tools/knowledge ids are merged with the request
  selection, and provider/model defaults apply only when the request is silent.
- Instructions are **not** written into the conversation history — two
  conversations in the same project never share messages.
- Permissions: projects and their documents are scoped by `user_id`; a user can
  neither read nor mutate another user's project.

## API surface (v1)

```
GET    /v1/projects                    list (user-scoped)
POST   /v1/projects                    create
GET    /v1/projects/default            virtual "General (Default)" fallback
GET    /v1/projects/{id}               get
PATCH  /v1/projects/{id}               partial update
DELETE /v1/projects/{id}               delete (conversations preserved)
GET    /v1/projects/{id}/context       resolved execution context
GET    /v1/projects/{id}/documents     project documents
POST   /v1/projects/{id}/documents     multipart upload → Core RAG pipeline
DELETE /v1/projects/{id}/documents/{doc_id}
GET    /v1/projects/active             current selection fallback
POST   /v1/projects/active             validate selection

GET    /chats?project_id={id}          conversations of a project
GET    /chats?unassigned=true          conversations without a project (default scope)
POST   /chats                          create (accepts project_id)
```

Chat completions accept `project_id` (top-level or inside `metadata`) in both
the streaming (`POST /v1/chat/completions/stream`) and non-streaming
(`POST /v1/chat/completions`) endpoints.

See also: [ADR-3003 — Projects domain](../architecture/adr/ADR-3003-projects-domain.md).
