"""Run the five manual test questions through the live chat (server must be running) and save the answers.

  python scripts/run_manual_tests.py [provider]     -> eval/runs/manual-<timestamp>/q1.md ... + summary.json
"""
import asyncio, json, sys, time
from pathlib import Path
import websockets

PROVIDER = sys.argv[1] if len(sys.argv) > 1 else "claude_cli"
QS = [
    ("q1-everyday-consumer", "I bought a laptop from a shop in the UK 5 weeks ago and it keeps shutting down. The shop says I can only have it repaired. Is that right?"),
    ("q2-trusts-study", "What is the difference between knowing receipt and dishonest assistance?"),
    ("q2b-follow-up", "and what remedy does the claimant get in each?"),
    ("q3-land-pq", "Ethel contributed £50,000 to the purchase of a registered house held in the sole name of her son Tom. Tom granted his neighbour Zahid an express right of way by deed, which was never registered. Tom later mortgaged the house to Bank plc without telling Ethel, who lives there. Tom has defaulted. Advise Bank plc. (1,000 words)"),
    ("q4-medicine-essay", "\"The right to determine what shall be done with, or to, one's body is a fundamental right in our society.\" Critically examine the extent to which English law reflects this view. (1,500 words)"),
    ("q5-criminal-pq", "During a cup final, Tony skids into Hamza \"to stop him scoring\", breaking Hamza's nose. Carlos shouts at Tony \"I'm going to get you for that\"; Tony backs away. Johannes, enraged at a refereeing decision, swings a metal pole at Carlos but drops it; it hits the referee, Oti, who suffers a brain injury needing surgery. Discuss criminal liability and the defence of consent. (1,500 words)"),
]


# realistic student / user requests (run with:  python scripts/run_manual_tests.py claude_cli r)
QS += [
    ("r1-case-summary", "Summarise Guest v Guest for my revision notes in about 150 words: facts, what the Supreme Court decided, and why it matters."),
    ("r2-essay-plan", "Give me an essay plan (headings and the argument under each, no full essay) for: \"Should the Keck distinction between selling arrangements and product requirements be abandoned?\""),
    ("r3-improve-paragraph", "Improve this paragraph so it reads like a first-class essay and tell me what you changed: \"In Dassonville the court said MEQRs are all trading rules which hinder trade. This is very wide. Then Keck came and it limited it. But Keck is confusing and there's grey areas so the law is a mess.\""),
    ("r4-everyday-tenancy", "My landlord hasn't returned my deposit two months after I moved out of my flat in England. What can I do?"),
    ("r5-revision-list", "What are the key cases on actual occupation under Schedule 3 paragraph 2 LRA 2002 and what does each one decide? Keep it short, I'm revising."),
]


async def ask(ws, q, sid):
    await ws.send(json.dumps({"type": "ask", "session_id": sid, "message": q,
                              "options": {"provider": PROVIDER, "strict": False}}))
    r = {"answer": "", "sources": [], "t0": time.time()}
    while True:
        ev = json.loads(await asyncio.wait_for(ws.recv(), 1200))
        t = ev["type"]
        if t == "session": sid = ev["session_id"]
        elif t == "meta": r.update(intent=ev["intent"], topics=ev["topics"], rewritten=ev["rewritten_query"])
        elif t == "sources": r.update(confidence=ev["confidence"], sources=[s["id"] for s in ev["sources"]])
        elif t == "mode": r["mode"] = ev["mode"]
        elif t == "token": r["answer"] += ev["text"]
        elif t == "error": r["error"] = ev["message"]
        elif t == "done":
            r.update(mode=ev.get("mode", r.get("mode")), validation=ev["validation"], secs=round(time.time() - r.pop("t0")))
            if ev.get("answer"): r["answer"] = ev["answer"]
            return sid, r


async def main():
    out = Path(__file__).resolve().parents[1] / "eval" / "runs" / time.strftime("manual-%Y%m%d-%H%M")
    out.mkdir(parents=True, exist_ok=True)
    summary, sid = [], None
    async with websockets.connect("ws://127.0.0.1:8800/ws", max_size=None, ping_interval=None) as ws:
        only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
        for name, q in QS:
            if only and not any(name.startswith(o) for o in only):
                continue
            sid, r = await ask(ws, q, sid if name.endswith("follow-up") else None)
            words = len(r["answer"].split())
            (out / f"{name}.md").write_text(f"# {name}\n\n**Q:** {q}\n\nintent={r.get('intent')} topics={r.get('topics')} "
                                            f"mode={r.get('mode')} conf={r.get('confidence')} verdict={r['validation'].get('verdict')} "
                                            f"words={words} secs={r['secs']}\n\nsources: {r['sources']}\n\n---\n\n{r['answer']}\n")
            summary.append({k: r.get(k) for k in ("intent", "topics", "mode", "confidence", "secs", "error")} |
                           {"name": name, "words": words, "verdict": r["validation"].get("verdict")})
            print(json.dumps(summary[-1]), flush=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print("saved", out)

asyncio.run(main())
