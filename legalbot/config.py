"""Loads config.yaml once; resolves relative paths against the project root."""
from __future__ import annotations

import functools
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

# embedding / reranker models are cached locally; don't block on the HF Hub at startup
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


@functools.lru_cache(maxsize=1)
def load() -> dict:
    path = Path(os.environ.get("LEGALBOT_CONFIG", ROOT / "config.yaml"))
    cfg = yaml.safe_load(path.read_text())
    for key, value in cfg["paths"].items():
        p = Path(value)
        cfg["paths"][key] = p if p.is_absolute() else (ROOT / p)
    return cfg


def path(name: str) -> Path:
    if name == "db" and os.environ.get("LEGALBOT_DB"):   # e.g. a persistent disk on a hosting platform
        return Path(os.environ["LEGALBOT_DB"])
    return load()["paths"][name]
