"""Internal gRPC services: QueryProcessor, Retrieval, LLM (server-streaming tokens).

Hosted in one process for local use; each servicer can be split into its own process later
by starting this module with --only query|retrieval|llm on different ports.
"""
from __future__ import annotations

import argparse
import json
import logging
from concurrent import futures

import grpc

from . import config
from .llm import providers
from .query.processor import QueryProcessor
from .retrieval.engine import RetrievalEngine
from .rpc import legalbot_pb2 as pb
from .rpc import legalbot_pb2_grpc as rpc

log = logging.getLogger("legalbot.grpc")


class QueryServicer(rpc.QueryProcessorServicer):
    def __init__(self, engine: RetrievalEngine):
        self.qp = QueryProcessor(lambda: engine.manifests, voter=lambda q: engine.topic_votes(q))

    def Process(self, req, ctx):
        hist = [{"role": t.role, "content": t.content} for t in req.history]
        r = self.qp.process(req.message, hist, req.forced_intent, req.forced_topic)
        return pb.ProcessResponse(**r)


class RetrievalServicer(rpc.RetrievalServicer):
    def __init__(self, engine: RetrievalEngine):
        self.engine = engine

    def _maybe_reload(self):
        """Pick up a rebuilt index (e.g. after fix_gaps) without restarting the server."""
        f = config.path("indexes") / "build.json"
        try:
            m = f.stat().st_mtime
        except OSError:
            return
        if getattr(self, "_built", None) is None:
            self._built = m
        elif m != self._built:
            self._built = m
            self.engine.load()

    def Retrieve(self, req, ctx):
        self._maybe_reload()
        r = self.engine.retrieve(req.query, list(req.topics) or None, req.top_k or None)
        return pb.RetrieveResponse(sources=[pb.Source(**s) for s in r["sources"]], confidence=r["confidence"],
                                   debug_json=json.dumps(r["debug"], default=str))


class LLMServicer(rpc.LLMServicer):
    def Generate(self, req, ctx):
        yield pb.Token(info=f"{req.provider}:{req.model or 'default'}")
        try:
            for text in providers.generate(req.provider, req.system_prompt, req.user_prompt, req.model,
                                           req.api_key, req.max_tokens, web=req.web):
                if not ctx.is_active():  # client disconnected / stop pressed
                    return
                if text:
                    yield pb.Token(text=text)
            yield pb.Token(done=True)
        except Exception as e:
            log.exception("generation failed")
            yield pb.Token(error=str(e), done=True)


def serve(block: bool = True, engine: RetrievalEngine | None = None):
    cfg = config.load()["grpc"]
    engine = engine or RetrievalEngine()
    engine.load()
    if engine.sections:
        engine.retrieve("warm up embedding and reranker models", None)  # first real query stays fast
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16),
                         options=[("grpc.max_send_message_length", 64 << 20),
                                  ("grpc.max_receive_message_length", 64 << 20)])
    rpc.add_QueryProcessorServicer_to_server(QueryServicer(engine), server)
    rpc.add_RetrievalServicer_to_server(RetrievalServicer(engine), server)
    rpc.add_LLMServicer_to_server(LLMServicer(), server)
    server.add_insecure_port(f"{cfg['host']}:{cfg['port']}")  # localhost only
    server.start()
    log.info("gRPC services on %s:%s", cfg["host"], cfg["port"])
    if block:
        server.wait_for_termination()
    return server, engine


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    argparse.ArgumentParser().parse_args()
    serve()
