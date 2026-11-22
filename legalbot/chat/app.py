"""Chat Service: WebSocket for the token pipeline + small REST API + static frontend."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .. import config
from ..obs import improve
from ..kb import load_manifests
from ..obs import trace as obs
from .conversation_store import ConversationStore
from .orchestrator import Orchestrator

log = logging.getLogger("legalbot.chat")
FRONTEND = config.ROOT / "frontend"
SECRETS = config.ROOT / "data" / "secrets.json"

app = FastAPI(title="Legal bot")
store = ConversationStore(config.path("db"))
orch: Orchestrator | None = None
SETTINGS: dict = {"provider": config.load()["llm"]["default_provider"], "strict": False, "models": {}, "api_keys": {}}
# Public mode (a shared website): every visitor brings their own API key, kept in their browser; chats are per visitor;
# no server-wide settings, no Claude/Codex logins, no gap-fixing jobs, logs only of your own questions.
PUBLIC = os.environ.get("LEGALBOT_PUBLIC", "") == "1" or bool(config.load()["chat"].get("public"))
PUBLIC_PROVIDERS = ["anthropic", "mock"]
RATE = {"per_hour": int(os.environ.get("LEGALBOT_RATE_PER_HOUR", "30")), "log": {}}


def uid_of(request_or_ws) -> str:
    """Anonymous per-browser id (localStorage) sent as X-Legalbot-User; 'local' for the single-user desktop setup."""
    u = request_or_ws.headers.get("x-legalbot-user") or request_or_ws.query_params.get("uid") or ""
    u = re.sub(r"[^a-zA-Z0-9_-]", "", u)[:64]
    return u if (u and PUBLIC) else ("local" if not PUBLIC else (u or "anon"))


def _rate_ok(uid: str) -> bool:
    import time as _t
    now = _t.time()
    log_ = [t for t in RATE["log"].get(uid, []) if now - t < 3600]
    RATE["log"][uid] = log_
    if len(log_) >= RATE["per_hour"]:
        return False
    log_.append(now)
    return True


def turn_settings(msg: dict) -> dict:
    """Settings for one question. Public: provider + key come from the visitor's browser, never stored."""
    if not PUBLIC:
        return SETTINGS
    opts = msg.get("options") or {}
    prov = opts.get("provider") if opts.get("provider") in PUBLIC_PROVIDERS else "anthropic"
    key = str(msg.get("api_key") or "")[:300]
    return {"provider": prov, "strict": bool(opts.get("strict", False)), "models": {},
            "api_keys": {prov: key} if key else {}}


def _load_secrets():
    if SECRETS.exists():
        try:
            SETTINGS["api_keys"].update(json.loads(SECRETS.read_text()))
        except Exception:
            pass


_load_secrets()


@app.on_event("startup")
async def _startup():
    global orch
    orch = Orchestrator(store)


# ------------------------------------------------------------------ WebSocket
@app.websocket("/ws")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    lock = asyncio.Lock()
    task: asyncio.Task | None = None

    async def send(ev: dict):
        async with lock:
            await ws.send_text(json.dumps(ev, default=str))

    user_id = uid_of(ws)

    async def run(msg):
        try:
            msg = {**msg, "user_id": user_id}
            st = turn_settings(msg)
            if PUBLIC:
                if st["provider"] == "anthropic" and not st["api_keys"].get("anthropic"):
                    await send({"type": "error", "message": "Add your Claude API key in ☰ → Model settings (it stays in your browser)."})
                    await send({"type": "done", "fallback": "error", "answer": "⚠️ No API key set: open ☰ → Model settings and paste your Claude API key.",
                                "validation": {"verdict": "n/a"}})
                    return
                if not _rate_ok(user_id):
                    await send({"type": "done", "fallback": "error", "answer": "⚠️ Hourly limit reached on this public site; try again later.",
                                "validation": {"verdict": "n/a"}})
                    return
            msg["options"] = {**(msg.get("options") or {}), "provider": st["provider"]}
            await orch.handle(msg, st, send)
        except asyncio.CancelledError:
            await send({"type": "stopped"})
        except Exception as e:
            log.exception("turn failed")
            await send({"type": "error", "message": f"{type(e).__name__}: {e}"})
            await send({"type": "done", "fallback": "error", "answer": f"⚠️ {e}", "validation": {"verdict": "n/a"}})

    try:
        while True:
            msg = json.loads(await ws.receive_text())
            kind = msg.get("type")
            if kind == "ping":
                await send({"type": "pong"})
            elif kind == "ask":
                if task and not task.done():
                    await send({"type": "error", "message": "still answering — press Stop first"})
                    continue
                task = asyncio.create_task(run(msg))
            elif kind == "stop" and task and not task.done():
                task.cancel()
    except WebSocketDisconnect:
        if task and not task.done():
            task.cancel()


# ------------------------------------------------------------------ REST
@app.get("/api/sessions")
def sessions(request: Request):
    return store.list_sessions(uid_of(request))


@app.get("/api/sessions/{sid}")
def session(sid: str, request: Request):
    if not store.owns(sid, uid_of(request)):
        raise HTTPException(404)
    return store.messages(sid)


@app.delete("/api/sessions/{sid}")
def delete_session(sid: str, request: Request):
    store.delete_session(sid, uid_of(request))
    return {"ok": True}


class Rename(BaseModel):
    title: str


@app.patch("/api/sessions/{sid}")
def rename(sid: str, body: Rename, request: Request):
    store.rename_session(sid, body.title, uid_of(request))
    return {"ok": True}


class Feedback(BaseModel):
    message_id: str
    session_id: str
    rating: int               # 1 / -1
    category: str = ""        # FM code if negative
    comment: str = ""


@app.post("/api/feedback")
def feedback(fb: Feedback, request: Request):
    if not store.owns(fb.session_id, uid_of(request)):
        raise HTTPException(404)
    store.add_feedback(fb.message_id, fb.session_id, fb.rating, fb.category, fb.comment)
    m = store.get_message(fb.message_id)
    tid = (m or {}).get("meta", {}).get("trace_id")
    t = obs.find_trace(tid) if tid else None
    path = None
    if t:
        if fb.rating < 0:
            obs.enqueue_review(t, f"thumbs_down:{fb.category}")
        path = improve.record_feedback(t, fb.rating, fb.comment or "", fb.category or "")
    return {"ok": True, "saved": str(path.relative_to(config.ROOT)) if path else None}


FIX_JOB: dict = {"proc": None}


@app.post("/api/fix-gaps")
def fix_gaps_start():
    if PUBLIC:
        raise HTTPException(403, "not available on the public site")
    """Start the 'fix knowledge gaps with Claude' job in the background (uses your Claude login, Sonnet)."""
    import subprocess
    import sys
    p = FIX_JOB["proc"]
    if p is not None and p.poll() is None:
        return {"started": False, "message": "already running"}
    log = config.path("review_queue") / "gap_fixes" / "last_run.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    FIX_JOB["proc"] = subprocess.Popen([sys.executable, "-m", "legalbot.fix_gaps"], cwd=config.ROOT,
                                       stdout=open(log, "w"), stderr=subprocess.STDOUT)
    return {"started": True}


@app.get("/api/fix-gaps")
def fix_gaps_status():
    from ..obs.improve import root
    st = root() / "gap_fixes" / "status.json"
    data = json.loads(st.read_text()) if st.exists() else {"state": "never run"}
    p = FIX_JOB["proc"]
    data["running"] = p is not None and p.poll() is None
    from ..fix_gaps import open_gaps
    data["open_gaps"] = len(open_gaps())
    return data


class Issue(BaseModel):
    trace_id: str
    failure_mode: str
    note: str = ""
    expected_source: str = ""


@app.post("/api/issues")
def issue(body: Issue):
    folder = obs.file_issue(body.trace_id, body.failure_mode, body.note, body.expected_source)
    return {"ok": True, "folder": str(folder.relative_to(config.ROOT))}


@app.get("/api/failure-modes")
def failure_modes():
    return obs.FAILURE_MODES


@app.get("/api/traces")
def traces(request: Request, limit: int = 50):
    mine = store.session_ids(uid_of(request))
    return [t for t in obs.recent_traces(limit * 4) if t.get("session_id") in mine][:limit]


@app.get("/api/traces/{trace_id}")
def trace(trace_id: str, request: Request):
    t = obs.find_trace(trace_id)
    if not t or t.get("session_id") not in store.session_ids(uid_of(request)):
        raise HTTPException(404)
    return t


@app.get("/api/status")
def status():
    idx = config.path("indexes") / "build.json"
    manifests = load_manifests(config.path("kb"))
    return {
        "index": json.loads(idx.read_text()) if idx.exists() else None,
        "topics": [{"slug": s, "name": m.get("name", s), "last_updated": str(m.get("last_updated", "")),
                    "last_indexed": str(m.get("last_indexed", ""))} for s, m in manifests.items()],
        "providers": PUBLIC_PROVIDERS if PUBLIC else list(config.load()["llm"]["providers"]) + ["mock"],
        "public": PUBLIC,
        "settings": ({"provider": "anthropic", "strict": False, "models": {}, "keys_set": []} if PUBLIC else
                     {**{k: v for k, v in SETTINGS.items() if k != "api_keys"},
                      "keys_set": [k for k, v in SETTINGS["api_keys"].items() if v]}),
        "review_queue": _count(config.path("review_queue") / "pending.jsonl"),
    }


class SettingsIn(BaseModel):
    provider: str | None = None
    strict: bool | None = None
    model: str | None = None
    api_key: str | None = None      # for the selected provider; "" clears
    remember_key: bool = False


@app.post("/api/settings")
def set_settings(s: SettingsIn):
    if PUBLIC:   # nothing is stored server-side on the public site
        return {"ok": True, "public": True}
    if s.provider:
        SETTINGS["provider"] = s.provider
    if s.strict is not None:
        SETTINGS["strict"] = s.strict
    prov = SETTINGS["provider"]
    if s.model is not None:
        SETTINGS["models"][prov] = s.model
    if s.api_key is not None:
        SETTINGS["api_keys"][prov] = s.api_key
        if s.remember_key:
            SECRETS.parent.mkdir(parents=True, exist_ok=True)
            SECRETS.write_text(json.dumps({k: v for k, v in SETTINGS["api_keys"].items() if v}))
            os.chmod(SECRETS, 0o600)
    return {"ok": True}


def _count(p: Path) -> int:
    return sum(1 for _ in p.open()) if p.exists() else 0


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")
