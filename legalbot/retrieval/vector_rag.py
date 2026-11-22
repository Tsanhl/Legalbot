"""Track B: Vector RAG — chunks + embeddings + FAISS.

Each chunk keeps breadcrumb metadata (parent section id, heading, chunk_index) so a
chunk hit can be expanded back to its parent section (FM3 fix).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

from ..kb import Section

log = logging.getLogger(__name__)


def make_chunks(sections: list[Section], size: int, overlap: int) -> list[dict]:
    chunks = []
    for si, sec in enumerate(sections):
        text = sec.content
        start, ci = 0, 0
        while start < len(text):
            piece = text[start : start + size]
            chunks.append({
                "section_idx": si, "source": sec.id, "heading": sec.title,
                "chunk_index": ci, "topic": sec.topic,
                # breadcrumb prefix gives the embedding the parent context
                "text": f"{sec.title}\n{piece}",
            })
            ci += 1
            if start + size >= len(text):
                break
            start += size - overlap
    return chunks


class VectorIndex:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self.index = None
        self.chunks: list[dict] = []

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _embed(self, texts: list[str], is_query: bool = False) -> np.ndarray:
        if is_query and "bge" in self.model_name:
            texts = ["Represent this sentence for searching relevant passages: " + t for t in texts]
        vecs = self.model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vecs, dtype="float32")

    def build(self, chunks: list[dict], cache_path: Path | None = None):
        """Embeds chunks, reusing cached vectors for unchanged text (sqlite: sha1(model+text) -> float32)."""
        import faiss
        import hashlib
        import sqlite3
        import time
        self.chunks = chunks
        keys = [hashlib.sha1((self.model_name + c["text"]).encode()).hexdigest() for c in chunks]
        cache = {}
        db = None
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(str(cache_path))
            db.execute("CREATE TABLE IF NOT EXISTS emb (k TEXT PRIMARY KEY, v BLOB)")
            for i in range(0, len(keys), 900):
                part = keys[i:i + 900]
                q = f"SELECT k, v FROM emb WHERE k IN ({','.join('?' * len(part))})"
                cache.update({k: np.frombuffer(v, dtype="float32") for k, v in db.execute(q, part)})
        todo = [i for i, k in enumerate(keys) if k not in cache]
        log.info("embedding %d new chunks (%d cached)", len(todo), len(chunks) - len(todo))
        t0 = time.time()
        for start in range(0, len(todo), 2048):
            batch = todo[start:start + 2048]
            vecs = self._embed([chunks[i]["text"] for i in batch])
            for i, v in zip(batch, vecs):
                cache[keys[i]] = v
            if db:
                db.executemany("INSERT OR REPLACE INTO emb VALUES (?, ?)",
                               [(keys[i], v.tobytes()) for i, v in zip(batch, vecs)])
                db.commit()
            done = start + len(batch)
            rate = done / max(time.time() - t0, 1e-6)
            log.info("  embedded %d/%d (%.0f/s, ~%.0f min left)", done, len(todo), rate, (len(todo) - done) / rate / 60)
        if db:
            db.close()
        vecs = np.stack([cache[k] for k in keys]).astype("float32") if chunks else np.zeros((0, 384), "float32")
        self.index = faiss.IndexFlatIP(vecs.shape[1])  # cosine on normalised vectors
        if len(vecs):
            self.index.add(vecs)
        return self

    def save(self, dir_: Path):
        import faiss
        faiss.write_index(self.index, str(dir_ / "faiss.index"))
        (dir_ / "chunks.jsonl").write_text("\n".join(json.dumps(c) for c in self.chunks))

    def load(self, dir_: Path) -> bool:
        import faiss
        fi, cj = dir_ / "faiss.index", dir_ / "chunks.jsonl"
        if not (fi.exists() and cj.exists()):
            return False
        self.index = faiss.read_index(str(fi))
        self.chunks = [json.loads(l) for l in cj.read_text().splitlines() if l.strip()]
        return True

    def _note_matrix(self):
        """Vectors of note chunks only (a few thousand), for a fast exact search over our own notes."""
        if getattr(self, "_notes", None) is None:
            ids = np.array([i for i, c in enumerate(self.chunks) if "/notes/" in c["source"]], dtype="int64")
            mat = np.vstack([self.index.reconstruct(int(i)) for i in ids]) if len(ids) else np.zeros((0, 384), "float32")
            self._notes = (ids, mat)
        return self._notes

    def search(self, query: str, top_k: int, topics: list[str] | None = None, kind: str | None = None) -> list[dict]:
        if not self.chunks:
            return []
        qv = self._embed([query], is_query=True)
        if kind == "note":
            ids, mat = self._note_matrix()
            sims = mat @ qv[0] if len(ids) else np.zeros(0)
            hits = []
            for j in np.argsort(-sims):
                c = self.chunks[int(ids[j])]
                if topics and c["topic"] not in topics:
                    continue
                hits.append({**{k2: c[k2] for k2 in ("section_idx", "source", "heading", "chunk_index")},
                             "similarity": round(float(sims[j]), 4), "distance": round(1 - float(sims[j]), 4),
                             "preview": c["text"][:160]})
                if len(hits) >= top_k:
                    break
            return hits
        k = min(len(self.chunks), top_k * (60 if topics else 1))
        sims, ids = self.index.search(qv, k)
        hits = []
        for sim, i in zip(sims[0], ids[0]):
            if i < 0:
                continue
            c = self.chunks[i]
            if topics and c["topic"] not in topics:
                continue
            if kind == "note" and "/notes/" not in c["source"]:
                continue
            hits.append({**{k2: c[k2] for k2 in ("section_idx", "source", "heading", "chunk_index")},
                         "similarity": round(float(sim), 4), "distance": round(1 - float(sim), 4),
                         "preview": c["text"][:160]})
            if len(hits) >= top_k:
                break
        return hits
