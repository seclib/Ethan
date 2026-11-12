import pytest
from core.knowledge.agent_traces.types import filter_secrets

def test_known_secrets():
    # Test OpenAI key
    text = "My key is sk-12345678901234567890123456789012"
    redacted, detected = filter_secrets(text)
    assert "sk-" not in redacted
    assert "[REDACTED:OPENAI_KEY]" in detected

def test_generic_high_entropy_secret():
    # Test a random high-entropy string that doesn't match a known prefix
    # Mix of upper, lower, digits, length > 24
    secret = "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6" 
    text = f"Here is a secret: {secret}"
    redacted, detected = filter_secrets(text)
    assert secret not in redacted
    assert "[REDACTED:GENERIC_SECRET]" in detected

def test_normal_text_not_redacted():
    # Test that normal words are NOT redacted
    text = "This is a normal sentence with a long word like supercalifragilisticexpialidocious"
    redacted, detected = filter_secrets(text)
    assert redacted == text
    assert len(detected) == 0

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
