"""Start everything locally:  python -m legalbot.run
   gRPC services (Query / Retrieval / LLM) + Chat Service (FastAPI + WebSocket + frontend).
   --grpc-only / --chat-only to run them as separate processes.
"""
from __future__ import annotations

import argparse
import logging

import uvicorn

from . import config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grpc-only", action="store_true")
    ap.add_argument("--chat-only", action="store_true")
    ap.add_argument("--host", help="chat host (default from config.yaml; 0.0.0.0 inside a container)")
    ap.add_argument("--port", type=int, help="chat port (default from config.yaml)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    grpc_server = None  # keep a reference: a garbage-collected grpc.Server stops serving
    if not args.chat_only:
        from .grpc_server import serve
        grpc_server, _engine = serve(block=args.grpc_only)
    if not args.grpc_only:
        c = dict(config.load()["chat"])
        c["host"], c["port"] = args.host or c["host"], args.port or c["port"]
        print(f"\n  Legal bot →  http://{c['host']}:{c['port']}\n")
        uvicorn.run("legalbot.chat.app:app", host=c["host"], port=c["port"], log_level="info")


if __name__ == "__main__":
    main()
