# ETHAN WebUI Initial Architecture Audit

## 1. Current Architecture (ETHAN WebUI)

The current WebUI is implemented as a modern React-based single-page application (SPA) using the Next.js framework.

### Technical Stack
- **Framework**: Next.js (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Primarily handled via React hooks and context (local state).
- **Communication**: REST API calls using `fetch` via a centralized `api-client.ts`.

### Architectural Pattern
- **Thin Client**: The WebUI acts purely as a visual layer. It contains virtually no business logic, orchestration, or data persistence.
- **Proxy Layer**: Next.js is configured as a proxy (`next.config.js`), rewriting `/api/*` requests to the ETHAN API.
- **Source of Truth**: All state, configurations, and data reside in the ETHAN Core/Runtime.

### API Surface Area
The current client interacts with the following ETHAN API domains:
- **Authentication**: Login, Logout, Refresh, Me.
- **Orchestration**: Agents, Goals, Skills.
- **Knowledge**: Memory (search/store), RAG (document ingestion/retrieval).
- **System**: Settings, LLM Providers, Flux (event stream).
- **State**: Chats and Messages.

---

## 2. Reference Architecture (Open-WebUI)

Open-WebUI is a full-stack AI interface designed for high flexibility and a rich user experience.

### Technical Stack
- **Frontend**: SvelteKit (Svelte)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Backend**: Python (FastAPI)
- **Database**: SQLite/PostgreSQL (via SQLAlchemy)

### Architectural Pattern
- **Rich Client**: The frontend contains significant logic for handling streaming, model configuration, and local state.
- **Integrated Backend**: Unlike the current ETHAN WebUI, Open-WebUI includes a powerful backend that manages users, chats, and RAG internally.
- **Provider Agnostic**: It is designed to connect to various LLM backends (Ollama, OpenAI, etc.).

### API Surface Area
Open-WebUI implements a very broad API surface in `src/lib/apis`:
- **Core**: Chats, Messages, Models.
- **Advanced**: Pipelines, Valves, Tools, Functions.
- **Management**: Users, Groups, Knowledge, Memories.
- **Infrastructure**: Webhooks, Analytics, Versioning.
