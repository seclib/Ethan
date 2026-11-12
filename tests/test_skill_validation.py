import pytest
import asyncio
from core.skills.store import SkillStore

async def run_test(coro):
    return await coro

def test_create_skill_invalid_name():
    store = SkillStore()
    # Test name missing
    try:
        asyncio.run(store.create_skill({"kind": "prompt"}))
        pytest.fail("Should have raised ValueError for missing name")
    except ValueError as e:
        assert "Le nom de la skill est obligatoire" in str(e)
    
    # Test name empty
    try:
        asyncio.run(store.create_skill({"name": "  ", "kind": "prompt"}))
        pytest.fail("Should have raised ValueError for empty name")
    except ValueError as e:
        assert "Le nom de la skill est obligatoire" in str(e)

def test_create_skill_invalid_valves():
    store = SkillStore()
    # Valves must be a dict
    try:
        asyncio.run(store.create_skill({"name": "Test", "valves": "not-a-dict"}))
        pytest.fail("Should have raised ValueError for invalid valves")
    except ValueError as e:
        assert "Les valves doivent être un objet JSON" in str(e)

def test_create_skill_success():
    store = SkillStore()
    data = {
        "name": "Valid Skill",
        "kind": "prompt",
        "valves": {"temp": 0.7},
        "tags": ["test", "verified"]
    }
    skill = asyncio.run(store.create_skill(data))
    assert skill["name"] == "Valid Skill"
    assert skill["valves"] == {"temp": 0.7}
    assert "test" in skill["tags"]

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
