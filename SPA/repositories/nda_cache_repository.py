"""Repository for safe NDA unpickling and overlay extraction."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

from corpus_toolkit.loader import CorpusLoader
from corpus_toolkit.parallel_view import NdaOverlay, _NdaSafeUnpickler
from SPA.models.config_dto import PathConfigDTO

SAFE_MODULE_PREFIXES = ("app.models", "builtins", "collections", "numpy", "pandas")


class SafeNdaUnpickler(_NdaSafeUnpickler):
    """Subclass with strict whitelist preventing execution of arbitrary classes."""

    def find_class(self, module: str, name: str) -> Any:
        if not any(module.startswith(p) for p in SAFE_MODULE_PREFIXES):
            raise pickle.UnpicklingError(f"Blocked unauthorized unpickle module: {module}.{name}")
        return super().find_class(module, name)


class NdaCacheRepository:
    """Safe retrieval of Neologism Dictionary Annotation pickled caches."""

    def __init__(
        self,
        loader: CorpusLoader,
        path_config: PathConfigDTO | None = None,
    ) -> None:
        self._loader = loader
        self._path_config = path_config
        self._cache_dir = (
            Path(path_config.nda_cache_dir)
            if path_config and path_config.nda_cache_dir
            else loader.config.thesis_root
            / "data"
            / "Neologism_Dictionary_Annotation_Cache"
        )
        self._nda_root = (
            loader.config.thesis_root
            / "scripts"
            / "Neologism_Dictionary_Annotation"
        )

    def _resolve_pair_id(self, pair_code: str) -> str:
        """Resolve composite codes (e.g. 'IR-IA_BR-SM') to canonical NDA cache folder ('I_Robot')."""
        try:
            from corpus_toolkit.parallel_view import _resolve_pair
            return _resolve_pair(self._loader, pair_code).pair_id
        except Exception:
            return pair_code

    def get_overlay_for_pair(self, pair_code: str) -> NdaOverlay:
        """Load NdaOverlay for a specific translation pair code."""
        return NdaOverlay.load(self._loader, self._resolve_pair_id(pair_code))

    def get_tripartite_dictionary(
        self, pair_code: str
    ) -> dict[str, list[dict[str, Any]]]:
        """Extract tripartite dictionary categories: linked, single_eng, single_tur."""
        pair_dir = self._cache_dir / self._resolve_pair_id(pair_code)
        dict_file = pair_dir / "initial_dictionary.pickle"
        if not dict_file.is_file():
            return {"linked": [], "single_eng": [], "single_tur": []}

        import sys
        import types

        added = [str(self._nda_root)] if str(self._nda_root) not in sys.path else []
        sys.path[:0] = added
        orig_app = sys.modules.get("app")
        app_pkg = types.ModuleType("app")
        app_pkg.__path__ = [str(self._nda_root / "app")]
        sys.modules["app"] = app_pkg
        try:
            with open(dict_file, "rb") as fh:
                unpickler = SafeNdaUnpickler(fh, self._nda_root)
                dict_model = unpickler.load()
        finally:
            if orig_app is not None:
                sys.modules["app"] = orig_app
            else:
                sys.modules.pop("app", None)
            for p in added:
                if p in sys.path:
                    sys.path.remove(p)

        entries = getattr(dict_model, "entries", {})
        linked: list[dict[str, Any]] = []
        single_eng: list[dict[str, Any]] = []
        single_tur: list[dict[str, Any]] = []

        for e_id, entry in entries.items():
            l_type = getattr(entry, "link_type", "auto")
            eng_toks = " ".join(
                [
                    str(getattr(t, "surface", getattr(t, "text", t)))
                    for t in getattr(entry, "eng_tokens", [])
                ]
            )
            tur_toks = " ".join(
                [
                    str(getattr(t, "surface", getattr(t, "text", t)))
                    for t in getattr(entry, "tur_tokens", [])
                ]
            )
            tags = list(getattr(entry, "tags", getattr(entry, "irrealia_tags", [])) or [])

            record = {
                "id": e_id,
                "eng": eng_toks,
                "tur": tur_toks,
                "link_type": l_type,
                "tags": tags,
                "notes": getattr(entry, "notes", ""),
            }

            if l_type in ("manual", "auto") and eng_toks and tur_toks:
                linked.append(record)
            elif l_type == "single_eng" or (eng_toks and not tur_toks):
                single_eng.append(record)
            elif l_type == "single_tur" or (tur_toks and not eng_toks):
                single_tur.append(record)

        return {
            "linked": linked,
            "single_eng": single_eng,
            "single_tur": single_tur,
        }

    def has_cache(self, pair_code: str) -> bool:
        """Check if pickled cache files exist for pair."""
        p_dir = self._cache_dir / self._resolve_pair_id(pair_code)
        return (p_dir / "scored_alignment_rows.pickle").is_file() or (
            p_dir / "initial_dictionary.pickle"
        ).is_file()
