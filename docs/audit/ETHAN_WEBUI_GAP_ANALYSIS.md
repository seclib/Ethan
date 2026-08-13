# ETHAN WebUI Gap Analysis

This document compares the features and API capabilities of the current ETHAN API vs the requirements of the Open-WebUI frontend.

## 1. Feature Mapping

| Open-WebUI Feature | ETHAN API Status | Gap / Requirement |
| :--- | :--- | :--- |
| **Chat Interface** | ✅ Supported | Basic chat history and messaging are implemented. |
| **Model Selection** | ✅ Supported | `getProviders` and `getProviderModels` provide this. |
| **User Auth** | ✅ Supported | Login/Logout/Me implemented. |
| **RAG / Knowledge** | ⚠️ Partial | ETHAN has RAG documents, but Open-WebUI's "Knowledge" system is more complex. |
| **Memory** | ✅ Supported | Memory search/ingest implemented. |
| **Tools / Functions** | ⚠️ Partial | ETHAN has Skills, but Open-WebUI's "Tools" system is more integrated into the chat flow. |
| **Pipelines** | ❌ Missing | Open-WebUI Pipelines are a core feature; ETHAN has no equivalent "pipeline" definition. |
| **Valves** | ❌ Missing | Configuration for pipelines. |
| **User Groups** | ❌ Missing | ETHAN currently has a flat user model. |
| **Analytics** | ❌ Missing | No usage analytics in ETHAN API. |

## 2. API Shape Mismatches

### Model Configuration
Open-WebUI expects a very detailed model configuration object (including `meta`, `params`, etc.). ETHAN's `ProviderModel` is simpler.
- **Gap**: Need to map `ProviderModel` $\rightarrow$ `OpenWebUIModelConfig`.

### Chat Persistence
Open-WebUI uses a specific chat/message schema. ETHAN's `core/state/chats.py` uses a different structure.
- **Gap**: Need a translation layer for chat history to prevent UI breakage.

### RAG Ingestion
Open-WebUI's "Knowledge" system allows for complex document management. ETHAN's `/api/v1/rag/documents` is a simpler list.
- **Gap**: Implementation of folders or tags for RAG documents in ETHAN API.

## 3. Critical Gaps to Address Before Fork

1. **Pipeline Equivalent**: Define how ETHAN handles "Pipelines" (complex tool chains) to satisfy the Open-WebUI frontend.
2. **Schema Translation**: Implement a middleware to transform ETHAN API responses into Open-WebUI expected shapes.
3. **Advanced User Management**: If groups/permissions are needed for the WebUI, ETHAN API must be extended.
