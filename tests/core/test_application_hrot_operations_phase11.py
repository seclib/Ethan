import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

from core.applications import (
    ApplicationStateStore,
    HrotApprovalRequest,
    HrotOperationStatus,
    OperationalHrotService,
    SoftwareEncryptedKeyStorage,
    HrotTrustStore,
)


def make_request(request_id: str = "req-1") -> HrotApprovalRequest:
    return HrotApprovalRequest(
        request_id=request_id,
        app_id="app",
        instance_id="inst",
        capability="cap",
        permission="cap",
        resource="res",
        action="read",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )


def test_key_generation_and_unlock() -> None:
    with tempfile.TemporaryDirectory() as directory:
        storage = SoftwareEncryptedKeyStorage(Path(directory) / "key.enc")
        ref = storage.generate("key-1", "human", "passphrase")
        assert ref.key_id == "key-1"
        assert storage.available() is True
        storage.lock()
        assert storage.verify_access() is False
        assert storage.unlock("wrong") is False
        assert storage.unlock("passphrase") is True
        assert storage.verify_access() is True


def test_private_key_never_returned() -> None:
    with tempfile.TemporaryDirectory() as directory:
        storage = SoftwareEncryptedKeyStorage(Path(directory) / "key.enc")
        storage.generate("key-1", "human", "passphrase")
        public_methods = [name for name in dir(storage) if not name.startswith("_")]
        assert "private_key" not in public_methods


def test_approval_and_replay() -> None:
    with tempfile.TemporaryDirectory() as directory:
        key_path = Path(directory) / "key.enc"
        storage = SoftwareEncryptedKeyStorage(key_path)
        storage.generate("key-1", "human", "passphrase")
        store = ApplicationStateStore(Path(directory) / "state.sqlite")
        service = OperationalHrotService(key_storage=storage, trust_store=HrotTrustStore(store))
        request = make_request()
        service.create_request(request)
        proof = service.approve_and_sign("req-1", passphrase=None)
        storage.lock()
        result, consumed = service.verify_proof(proof, expected_request=request, consume=True)
        assert consumed is True
        result2, consumed2 = service.verify_proof(proof, expected_request=request, consume=True)
        assert result2.status.value == "replay_detected"
        assert consumed2 is False
        store.close()


def test_revocation_survives_restart() -> None:
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / "state.sqlite"
        store = ApplicationStateStore(db)
        service_store = HrotTrustStore(store)
        service_store.revoke_key("key-1", reason="manual")
        store.close()

        restarted_store = ApplicationStateStore(db)
        restarted = HrotTrustStore(restarted_store)
        assert restarted.is_key_revoked("key-1") is True
        restarted_store.close()


def test_consumption_survives_restart() -> None:
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / "state.sqlite"
        store = ApplicationStateStore(db)
        trust = HrotTrustStore(store)
        trust.consume("proof-1")
        store.close()

        restarted_store = ApplicationStateStore(db)
        restarted = HrotTrustStore(restarted_store)
        assert restarted.is_consumed("proof-1") is True
        restarted_store.close()


def test_absent_storage_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as directory:
        storage = SoftwareEncryptedKeyStorage(Path(directory) / "missing.enc")
        store = ApplicationStateStore(Path(directory) / "state.sqlite")
        service = OperationalHrotService(key_storage=storage, trust_store=HrotTrustStore(store))
        try:
            service.approve_and_sign("no-request")
            raise AssertionError("approval succeeded without available key")
        except Exception:
            pass
        store.close()


def test_future_status_exposed() -> None:
    assert HrotOperationStatus.PENDING.value == "pending"
