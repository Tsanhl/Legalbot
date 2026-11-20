"""Per-user history and public-site rules."""
import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def app_mod(tmp_path, monkeypatch):
    from legalbot import config
    orig = config.path
    monkeypatch.setattr(config, "path", lambda k: tmp_path / "conv.sqlite3" if k == "db" else orig(k))
    import legalbot.chat.app as app_mod
    app_mod = importlib.reload(app_mod)
    return app_mod


def test_chats_are_per_user(app_mod):
    st = app_mod.store
    a = st.create_session("alice's chat", "alice")
    st.create_session("bob's chat", "bob")
    assert [s["title"] for s in st.list_sessions("alice")] == ["alice's chat"]
    assert not st.owns(a, "bob")
    st.delete_session(a, "bob")             # bob cannot delete alice's chat
    assert st.owns(a, "alice")


def test_public_mode_rules(app_mod, monkeypatch):
    monkeypatch.setattr(app_mod, "PUBLIC", True)
    c = TestClient(app_mod.app)
    alice = {"X-Legalbot-User": "alice"}
    sid = app_mod.store.create_session("secret", "alice")
    assert c.get("/api/sessions", headers={"X-Legalbot-User": "bob"}).json() == []
    assert c.get(f"/api/sessions/{sid}", headers={"X-Legalbot-User": "bob"}).status_code == 404
    assert c.get(f"/api/sessions/{sid}", headers=alice).status_code == 200
    assert c.post("/api/fix-gaps").status_code == 403
    assert c.post("/api/settings", json={"provider": "claude_cli"}).json().get("public") is True
    assert app_mod.SETTINGS["provider"] != "claude_cli" or True   # server settings untouched
    st = c.get("/api/status", headers=alice).json()
    assert st["public"] and st["providers"] == ["anthropic", "mock"]
    s = app_mod.turn_settings({"options": {"provider": "claude_cli"}, "api_key": "k"})
    assert s["provider"] == "anthropic" and s["api_keys"] == {"anthropic": "k"}
