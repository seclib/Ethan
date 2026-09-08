"""tests/test_search.py — Unified search across ETHAN domains."""

import pytest
from core.search import SearchManager, SearchType


@pytest.fixture
def search_manager():
    return SearchManager()


@pytest.fixture
def search_manager_with_mocks():
    """SearchManager with mocked dependencies."""
    knowledge = MockKnowledgeManager()
    chat = MockChatStore()
    rag = MockRAGPipeline()
    return SearchManager(
        knowledge_manager=knowledge,
        chat_store=chat,
        rag_pipeline=rag,
    )


class MockKnowledgeManager:
    async def search(self, query, limit=20):
        return [
            {"id": "n1", "label": "Test Node", "content": "test content", "source": "src", "node_type": "note", "created_at": "2024-01-01"},
        ]

    async def list_collections(self):
        return [
            {"id": "c1", "name": "Test Collection", "description": "A test collection", "document_ids": ["d1", "d2"]},
        ]


class MockChatStore:
    async def list_chats(self):
        return [
            {"id": "chat1", "title": "Test Chat", "created_at": "2024-01-01"},
        ]

    class _store:
        @staticmethod
        async def list(domain):
            return [
                {"id": "msg1", "content": "test message", "chat_id": "chat1", "created_at": "2024-01-01"},
            ]


class MockRAGPipeline:
    async def retrieve(self, query, top_k=10):
        return [
            {"chunk": {"id": "ch1", "content": "test chunk"}, "document_title": "Doc", "score": 0.9},
        ]


@pytest.mark.asyncio
async def test_search_empty_query_returns_empty(search_manager):
    result = await search_manager.search("", SearchType.KNOWLEDGE)
    assert result["total"] == 0
    assert result["results"] == []


@pytest.mark.asyncio
async def test_search_unknown_type_returns_empty(search_manager):
    result = await search_manager.search("test", "unknown_type")
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_search_knowledge_with_mock(search_manager_with_mocks):
    result = await search_manager_with_mocks.search("test", SearchType.KNOWLEDGE)
    assert result["type"] == "knowledge"
    assert result["total"] == 1
    assert result["results"][0]["title"] == "Test Node"


@pytest.mark.asyncio
async def test_search_library_with_mock(search_manager_with_mocks):
    result = await search_manager_with_mocks.search("test", SearchType.LIBRARY)
    assert result["type"] == "library"
    assert result["total"] >= 1


@pytest.mark.asyncio
async def test_search_conversation_with_mock(search_manager_with_mocks):
    result = await search_manager_with_mocks.search("test", SearchType.CONVERSATION)
    assert result["type"] == "conversation"
    assert result["total"] >= 1


@pytest.mark.asyncio
async def test_search_web_without_provider_returns_error(search_manager):
    result = await search_manager.search("test", SearchType.WEB)
    assert result["total"] == 0
    assert "error" in result


@pytest.mark.asyncio
async def test_search_web_with_provider():
    async def mock_web_search(query, limit=10):
        return [{"title": "Result", "url": "http://example.com"}]

    manager = SearchManager(web_search_fn=mock_web_search)
    result = await manager.search("test", SearchType.WEB)
    assert result["type"] == "web"
    assert result["total"] == 1
    assert result["results"][0]["title"] == "Result"
