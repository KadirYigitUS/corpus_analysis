"""Content-addressed on-disk cache (``<data_root>/.cache``).

*Why a cache?*  Un-pickling and ``literal_eval``-ing the list-valued columns of a 80 000-token
novel takes seconds; doing it for 13 texts, every time a notebook restarts, wastes minutes.
Derived columns are therefore stored once as Parquet and re-used.

Design rules (see ``docs/METRICS.md`` §cache):

* **Content-addressed** – the key hashes ``SCHEMA_VERSION``, the source file's size+mtime and
  the call arguments, so editing a pickle or changing the schema invalidates entries.
* **Atomic writes** – data is written to a temp file and ``os.replace``-d, so an interrupted
  kernel can never leave a half-written entry.
* **Policy** – ``keep`` | ``clear`` | ``ask`` (``ask`` falls back to ``keep`` when no stdin is
  available so ``nbconvert`` never blocks).
* **Budget** – oldest entries are evicted when the cache exceeds ``max_mb``.
"""

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from .config import SCHEMA_VERSION, cache_policy_from_env


def file_signature(path: Path) -> str:
    """``size:mtime_ns`` of a file -- cheap change detector (no hashing of 40 MB files)."""
    st = Path(path).stat()
    return f"{st.st_size}:{st.st_mtime_ns}"


class CorpusCacheManager:
    """Read/write/clear derived data under ``cache_dir``."""

    def __init__(self, cache_dir: Path, max_mb: float = 2048.0) -> None:
        self.dir = Path(cache_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.max_mb = max_mb

    # ------------------------------------------------------------------ keys
    def key(self, namespace: str, *parts: Any) -> str:
        """Stable key ``<namespace>-<sha256[:20]>`` from ``parts`` + schema version."""
        blob = json.dumps([SCHEMA_VERSION, *map(str, parts)], ensure_ascii=False)
        return f"{namespace}-{hashlib.sha256(blob.encode()).hexdigest()[:20]}"

    def _path(self, key: str, suffix: str) -> Path:
        return self.dir / f"{key}{suffix}"

    # ----------------------------------------------------------- dataframes
    def has(self, key: str, suffix: str = ".parquet") -> bool:
        return self._path(key, suffix).is_file()

    def load_frame(self, key: str) -> pd.DataFrame | None:
        path = self._path(key, ".parquet")
        if not path.is_file():
            return None
        try:
            path.touch()  # refresh LRU timestamp
            return pd.read_parquet(path)
        except Exception:  # corrupted entry -> behave as a miss
            path.unlink(missing_ok=True)
            return None

    def save_frame(self, key: str, frame: pd.DataFrame) -> Path:
        return self._atomic(key, ".parquet", lambda p: frame.to_parquet(p, index=False))

    # ----------------------------------------------------------------- json
    def load_json(self, key: str) -> Any | None:
        path = self._path(key, ".json")
        if not path.is_file():
            return None
        try:
            path.touch()
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            path.unlink(missing_ok=True)
            return None

    def save_json(self, key: str, obj: Any) -> Path:
        def write(p: Path) -> None:
            p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        return self._atomic(key, ".json", write)

    def _atomic(self, key: str, suffix: str, writer: Any) -> Path:
        target = self._path(key, suffix)
        fd, tmp = tempfile.mkstemp(dir=self.dir, suffix=".tmp")
        os.close(fd)
        try:
            writer(Path(tmp))
            os.replace(tmp, target)
        finally:
            Path(tmp).unlink(missing_ok=True)
        self.enforce_budget()
        return target

    # ----------------------------------------------------------- management
    def entries(self) -> list[Path]:
        return sorted((p for p in self.dir.iterdir() if p.suffix in {".parquet", ".json"}),
                      key=lambda p: p.stat().st_mtime)

    def size_mb(self) -> float:
        return sum(p.stat().st_size for p in self.entries()) / 1e6

    def enforce_budget(self) -> None:
        """Evict least-recently-used entries until under ``max_mb``."""
        for p in self.entries():
            if self.size_mb() <= self.max_mb:
                break
            p.unlink(missing_ok=True)

    def info(self) -> dict[str, Any]:
        return {"dir": str(self.dir), "entries": len(self.entries()),
                "size_mb": round(self.size_mb(), 2), "budget_mb": self.max_mb}

    def clear(self) -> int:
        """Delete every cache entry (the *user-requested* feature); returns count removed."""
        if self.dir.name != ".cache":
            raise RuntimeError(f"Refusing to clear cache: directory '{self.dir}' is not named '.cache'")
        n = 0
        for p in list(self.dir.iterdir()):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
                n += 1
            elif p.suffix in {".parquet", ".json", ".tmp"}:
                p.unlink(missing_ok=True)
                n += 1
        return n


    def apply_policy(self, policy: str | None = None, *, verbose: bool = True) -> str:
        """Honour ``keep|clear|ask``; returns the action taken (``'kept'`` / ``'cleared'``)."""
        policy = (policy or cache_policy_from_env()).lower()
        if policy == "ask":
            try:
                answer = input(f"Cache at {self.dir} holds {self.info()['entries']} entries "
                               f"({self.size_mb():.0f} MB). Clear it? [y/N] ").strip().lower()
                policy = "clear" if answer in {"y", "yes", "e", "evet"} else "keep"
            except (EOFError, NotImplementedError, OSError):
                policy = "keep"
        if policy == "clear":
            removed = self.clear()
            if verbose:
                print(f"🧹 Cache cleared ({removed} items removed).")
            return "cleared"
        if verbose:
            print(f"📦 Cache kept: {self.info()}")
        return "kept"
