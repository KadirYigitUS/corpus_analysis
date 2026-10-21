"""Corpus repository wrapping CorpusLoader and content-addressed Parquet cache."""

from __future__ import annotations

import os
from typing import Any

from corpus_toolkit.loader import CorpusLoader, LazyCorpusText
from corpus_toolkit.tokenview import TokenView
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO


class CorpusRepository:
    """Encapsulates CorpusLoader access, LRU cache eviction, and text retrieval."""

    def __init__(self, data_root: str | None = None) -> None:
        os.environ.setdefault("CORPUS_CACHE_POLICY", "keep")
        self._loader = CorpusLoader()

    @property
    def loader(self) -> CorpusLoader:
        return self._loader

    def get_inventory_table(self) -> list[dict[str, Any]]:
        """Return the complete metadata inventory table from CorpusRegistry."""
        inv = self._loader.registry.inventory()
        return inv.to_dict(orient="records")

    def get_cache_info(self) -> dict[str, Any]:
        """Return cache entries, memory consumption, and active policy."""
        return self._loader.cache.info()

    def evict_cache(self, keep_latest_n: int = 0) -> int:
        """Evict cached Parquet entries."""
        return self._loader.cache.clear()


    def get_rss_mb(self) -> float:
        """Return current resident set size (RSS) in megabytes."""
        return self._loader.rss_mb()

    def get_texts_by_scope(
        self, scope_dto: CorpusScopeDTO
    ) -> list[LazyCorpusText]:
        """Retrieve LazyCorpusText objects based on the requested scope."""
        scope = scope_dto.scope
        if scope == "all":
            return self._loader.load_all()
        elif scope == "all_en":
            return self._loader.load_all_english()
        elif scope == "all_tr":
            return self._loader.load_all_turkish()
        elif scope == "trans_en":
            return list(self._loader.load_all_english())
        elif scope == "trans_tr":
            return [
                t for t in self._loader.load_all_turkish()
                if getattr(t.record, "corpus_type", "") == "translation"
            ]
        elif scope == "indig_tr":
            return list(self._loader.load_indigenous())
        elif scope == "pairs":
            texts: list[LazyCorpusText] = []
            for spec, eng, tur in self._loader.load_translation_pairs():
                if scope_dto.pair_code and scope_dto.pair_code not in (
                    spec.pair_id, f"{spec.eng.code}_{spec.tur.code}"
                ):
                    continue
                texts.extend([eng, tur])
            return texts
        elif scope == "single" and scope_dto.text_code:
            return [self._loader.load_text(scope_dto.text_code)]
        return list(self._loader.load_all())

    def get_token_view(
        self, text: LazyCorpusText, params: TokenViewParamsDTO
    ) -> TokenView:
        """Construct TokenView with specified 32-combination matrix parameters."""
        return TokenView(
            text=text,
            field=params.field,
            filter_function_words=params.filter_function_words,
            mode=params.mode,
            punct=params.punct,
        )

    def get_text_tokens_matrix(
        self, texts: list[LazyCorpusText], params: TokenViewParamsDTO
    ) -> dict[str, list[str]]:
        """Extract token or lemma sequences for a list of texts under TokenView parameters."""
        result: dict[str, list[str]] = {}
        for t in texts:
            view = self.get_token_view(t, params)
            code = getattr(t, "code", getattr(getattr(t, "record", None), "code", str(t)))
            result[code] = [str(x) for x in view.forms]
        return result
