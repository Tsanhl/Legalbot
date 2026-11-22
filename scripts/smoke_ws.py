"""Smoke test the WebSocket token pipeline end to end (server must be running)."""
import asyncio, json, sys
import websockets

PROVIDER = sys.argv[1] if len(sys.argv) > 1 else "mock"

async def ask(ws, m, sid=None, **opt):
    await ws.send(json.dumps({"type": "ask", "session_id": sid, "message": m,
                              "options": {"provider": PROVIDER, "strict": True, **opt}}))
    print(f"\nQ: {m}")
    tokens = 0
    while True:
        ev = json.loads(await ws.recv())
        t = ev["type"]
        if t == "session": sid = ev["session_id"]
        elif t == "meta": print(f"  intent={ev['intent']} topics={ev['topics']} follow_up={ev['is_follow_up']}\n  rewritten: {ev['rewritten_query']}")
        elif t == "sources": print(f"  confidence={ev['confidence']} sources={[s['label'] + ':' + s['id'] for s in ev['sources']]}")
        elif t == "token": tokens += 1
        elif t == "error": print("  ERROR", ev["message"])
        elif t == "done":
            print(f"  tokens={tokens} verdict={ev['validation']['verdict']} fallback={ev['fallback'] or '-'} total_ms={ev.get('total_ms')}")
            if ev.get("answer"): print("  answer:", ev["answer"][:160].replace("\n", " "))
            return sid

async def main():
    async with websockets.connect("ws://127.0.0.1:8800/ws") as ws:
        sid = await ask(ws, "Explain what Article 102 TFEU prohibits")
        await ask(ws, "and how is that position defined?", sid)
        await ask(ws, "What is the limitation period for defamation claims in English law?", sid)
        await ask(ws, "what's the weather like today")

asyncio.run(main())
