"""LLM providers. All yield text deltas so the gRPC LLM service can stream them.

  anthropic   Claude API (key from UI or ANTHROPIC_API_KEY / `ant auth login`)
  claude_cli  your Claude Code subscription: `claude -p --output-format stream-json`, no tools
  codex_cli   your Codex subscription: `codex exec --json --sandbox read-only`
  mock        offline extractive answer, for tests and UI work (no model call)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterator

from .. import config

RESET = "\x00RESET\x00"   # stream marker: discard the text streamed so far
SANDBOX_DIR = config.ROOT / "data" / "llm_sandbox"  # neutral cwd: no project files / CLAUDE.md visible


# web mode: search anywhere, but only open pages on official / reputable legal sites
WEB_DOMAINS = ["legislation.gov.uk", "caselaw.nationalarchives.gov.uk", "bailii.org", "supremecourt.uk",
               "judiciary.uk", "gov.uk", "eur-lex.europa.eu", "curia.europa.eu", "hudoc.echr.coe.int",
               "lawcom.gov.uk", "parliament.uk", "citizensadvice.org.uk", "which.co.uk", "cps.gov.uk"]


def generate(provider: str, system: str, prompt: str, model: str = "", api_key: str = "",
             max_tokens: int = 0, web: bool = False) -> Iterator[str]:
    pcfg = config.load()["llm"]["providers"].get(provider, {})
    if provider == "anthropic":
        yield from _anthropic(system, prompt, model or pcfg["model"], api_key, max_tokens or pcfg["max_tokens"], pcfg, web)
    elif provider == "claude_cli":
        yield from _claude_cli(system, prompt, model or pcfg.get("model", ""), pcfg, web)
    elif provider == "codex_cli":
        yield from _codex_cli(system, prompt, model or pcfg.get("model", ""), pcfg)
    elif provider == "mock":
        yield from _mock(prompt)
    else:
        raise ValueError(f"unknown provider {provider!r}")


# ---------------------------------------------------------------- Claude API
def _anthropic(system, prompt, model, api_key, max_tokens, pcfg, web=False) -> Iterator[str]:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    kwargs = dict(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": prompt}],
        thinking={"type": "adaptive"},
        output_config={"effort": pcfg.get("effort", "high")},
    )
    if web:
        kwargs["tools"] = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 5,
                            "allowed_domains": WEB_DOMAINS}]
    if pcfg.get("server_fallbacks"):
        kwargs.update(betas=["server-side-fallback-2026-07-01"], fallbacks="default")
    try:
        with client.beta.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
            final = stream.get_final_message()
            if final.stop_reason == "refusal":
                yield "\n\n[The model declined this request.]"
            elif final.stop_reason == "max_tokens":
                yield "\n\n[Answer truncated at max_tokens.]"
    except anthropic.AuthenticationError:
        raise RuntimeError("Claude API: invalid or missing API key (set it in Settings, or ANTHROPIC_API_KEY)")
    except anthropic.RateLimitError:
        raise RuntimeError("Claude API: rate limited, try again shortly")
    except anthropic.APIStatusError as e:
        raise RuntimeError(f"Claude API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        raise RuntimeError("Claude API: network connection failed")


# ---------------------------------------------------------------- CLI helpers
def _spawn(cmd: list[str], stdin_text: str, timeout: int) -> Iterator[str]:
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    # use the subscription login; drop Claude Code session markers so the CLI runs even when this
    # server was started from inside Claude Code / the Claude desktop app
    drop = {"ANTHROPIC_API_KEY", "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SSE_PORT"}
    env = {k: v for k, v in os.environ.items() if k not in drop}
    exe = shutil.which(cmd[0]) or shutil.which(Path(cmd[0]).name, path=f"{Path.home()}/.local/bin:{Path.home()}/.npm-global/bin:/opt/homebrew/bin")
    if not exe:
        raise RuntimeError(f"{cmd[0]} not found on PATH — install it or set the full path in config.yaml")
    cmd = [exe, *cmd[1:]]
    proc = subprocess.Popen(cmd, cwd=SANDBOX_DIR, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, env=env, bufsize=1)
    assert proc.stdin and proc.stdout
    proc.stdin.write(stdin_text)
    proc.stdin.close()
    try:
        for line in proc.stdout:
            yield line
        proc.wait(timeout=timeout)
    finally:
        if proc.poll() is None:
            proc.kill()
    if proc.returncode not in (0, None):
        err = (proc.stderr.read() if proc.stderr else "")[-800:]
        raise RuntimeError(f"{Path(cmd[0]).name} exited {proc.returncode}: {err.strip()}")


def _claude_cli(system, prompt, model, pcfg, web=False) -> Iterator[str]:
    tools = ["--tools", "WebSearch,WebFetch",
             "--allowedTools", "WebSearch", *[f"WebFetch(domain:{d})" for d in WEB_DOMAINS]] if web else ["--tools", ""]
    cmd = [pcfg.get("binary", "claude"), "-p", "--output-format", "stream-json", "--verbose",
           "--include-partial-messages", *tools, "--no-session-persistence",
           "--system-prompt", system]
    if model:
        cmd += ["--model", model]
    streamed = False
    for line in _spawn(cmd, prompt, pcfg.get("timeout_sec", 900)):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "stream_event":
            e = ev.get("event", {})
            # a new assistant message after text was written (e.g. it searched the web, then started over):
            # the earlier text was a draft, so tell the caller to discard it
            if e.get("type") == "message_start" and streamed:
                yield RESET
                streamed = False
                continue
            if e.get("type") == "content_block_delta" and e.get("delta", {}).get("type") == "text_delta":
                streamed = True
                yield e["delta"]["text"]
        elif ev.get("type") == "result":
            if ev.get("is_error"):
                raise RuntimeError(f"claude CLI: {ev.get('result') or ev.get('subtype')}")
            if not streamed and ev.get("result"):
                yield ev["result"]


def _codex_cli(system, prompt, model, pcfg) -> Iterator[str]:
    cmd = [pcfg.get("binary", "codex"), "exec", "--json", "--sandbox", "read-only", "--skip-git-repo-check"]
    if model:
        cmd += ["--model", model]
    cmd.append("-")  # read prompt from stdin
    full = f"<system_instructions>\n{system}\n</system_instructions>\n\n{prompt}"
    for line in _spawn(cmd, full, pcfg.get("timeout_sec", 900)):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = ev.get("item") or {}
        if ev.get("type") == "item.completed" and item.get("type") in ("agent_message", "assistant_message"):
            yield item.get("text", "")
        elif ev.get("type") == "error":
            raise RuntimeError(f"codex CLI: {ev.get('message')}")


# ---------------------------------------------------------------- mock
def _mock(prompt: str) -> Iterator[str]:
    """Extractive stand-in: first sentences of each document, with labels. Proves the pipeline."""
    docs = re.findall(r'<document label="(S\d+)"[^>]*>\n(.*?)\n(.*?)</document>', prompt, re.S)
    if not docs:
        yield "The knowledge base does not contain material on this question."
        return
    yield ("**Test mode (no model): these are the passages the model would answer from. "
           "Choose a model in ☰ → Model to get a written answer.**\n\n")
    for label, title, body in docs[:4]:
        sent = re.split(r"(?<=[.!?])\s+", body.strip())[:2]
        yield f"- **{title.strip()}**: {' '.join(sent)[:400]} [{label}]\n"
