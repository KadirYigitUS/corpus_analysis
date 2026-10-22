"""Service for 8-group NER indexing and token-span hydration on Tab 2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from SPA.repositories.corpus_repository import CorpusRepository
from SPA.repositories.nda_cache_repository import (
    NdaCacheRepository,
    SafeNdaUnpickler,
    ensure_nda_app_modules,
)

NER_GROUP_MAP: dict[str, str] = {
    "PER": "PER",
    "PERSON": "PER",
    "ORG": "ORG",
    "NORP": "ORG",
    "LOC": "LOC",
    "GPE": "LOC",
    "MISC": "MISC",
    "FAC": "FAC",
    "PROD": "PROD",
    "PRODUCT": "PROD",
    "EVENT": "PROD",
    "WORK": "PROD",
    "WORK_OF_ART": "PROD",
    "DATE": "NUM",
    "TIME": "NUM",
    "CARD": "NUM",
    "CARDINAL": "NUM",
    "ORD": "NUM",
    "ORDINAL": "NUM",
    "PCT": "NUM",
    "PERCENT": "NUM",
    "MONEY": "NUM",
    "QTY": "NUM",
    "QUANTITY": "NUM",
    "NUM": "NUM",
    "LAW": "LAW",
    "LANG": "LAW",
    "LANGUAGE": "LAW",
}


def normalize_ner_group(raw_tag: str) -> tuple[str, str]:
    """Return (clean_tag, 8_group_code) from a raw BIO NER string."""
    if not raw_tag or raw_tag in ("O", "0", "None", "nan"):
        return "", ""
    clean = str(raw_tag).strip()
    if clean.startswith(("B-", "I-")):
        clean = clean[2:]
    clean_up = clean.upper()
    group = NER_GROUP_MAP.get(clean_up, "MISC" if clean_up else "")
    return clean_up, group


@dataclass
class PairNerIndex:
    """Compact in-memory NER index and token-span cache for one translation pair."""

    ai_groups: dict[int, frozenset[str]] = field(default_factory=dict)
    group_ais: dict[str, set[int]] = field(default_factory=dict)
    ai_tags_en: dict[int, list[str]] = field(default_factory=dict)
    ai_tags_tr: dict[int, list[str]] = field(default_factory=dict)
    ann_en: dict[int, list[list[dict[str, Any]]]] = field(default_factory=dict)
    ann_tr: dict[int, list[list[dict[str, Any]]]] = field(default_factory=dict)


class AlignmentNerService:
    """Indexes 8-group NER tags and token annotations per alignment row (ai)."""

    def __init__(
        self,
        corpus_repo: CorpusRepository,
        nda_repo: NdaCacheRepository,
    ) -> None:
        self._repo = corpus_repo
        self._corpus_repo = corpus_repo
        self._nda_repo = nda_repo
        self._cache: dict[str, PairNerIndex] = {}

    def get_pair_index(self, pair_code: str) -> PairNerIndex:
        """Build or return cached PairNerIndex for ``pair_code``."""
        pair_id = self._nda_repo._resolve_pair_id(pair_code)
        if pair_id in self._cache:
            return self._cache[pair_id]
        idx = self._build_index(pair_id)
        self._cache[pair_id] = idx
        return idx

    def matching_ais(self, pair_code: str, ner_category: str | None) -> set[int] | None:
        """Return set of alignment IDs matching ``ner_category`` (None if ALL/unset)."""
        if not ner_category or ner_category.upper() == "ALL":
            return None
        cat = ner_category.upper()
        p_idx = self.get_pair_index(pair_code)
        return p_idx.group_ais.get(cat, set())

    def get_row_annotations(
        self, pair_code: str, ai: int
    ) -> tuple[list[str], list[str], list[list[dict[str, Any]]], list[list[dict[str, Any]]]]:
        """Return (ner_en, ner_tr, ann_eng, ann_tur) for alignment ``ai``."""
        p_idx = self.get_pair_index(pair_code)
        return (
            p_idx.ai_tags_en.get(ai, []),
            p_idx.ai_tags_tr.get(ai, []),
            p_idx.ann_en.get(ai, []),
            p_idx.ann_tr.get(ai, []),
        )

    def _build_index(self, pair_id: str) -> PairNerIndex:
        p_idx = PairNerIndex()
        rows_file = self._nda_repo._cache_dir / pair_id / "scored_alignment_rows.pickle"
        if not rows_file.is_file():
            return p_idx

        nda_root = self._nda_repo._nda_root
        thesis_root = self._corpus_repo.loader.config.thesis_root
        ensure_nda_app_modules(nda_root, thesis_root)
        try:
            with open(rows_file, "rb") as fh:
                raw_rows = SafeNdaUnpickler(fh, nda_root).load()
        except Exception:
            return p_idx

        if not isinstance(raw_rows, dict):
            return p_idx

        for raw_ai, row in raw_rows.items():
            ai = int(raw_ai)
            groups: set[str] = set()
            en_sents, en_tags, en_grp = self._extract_side(getattr(row, "eng_tokens", []))
            tr_sents, tr_tags, tr_grp = self._extract_side(getattr(row, "tur_tokens", []))
            groups.update(en_grp)
            groups.update(tr_grp)
            if groups:
                p_idx.ai_groups[ai] = frozenset(groups)
                for g in groups:
                    p_idx.group_ais.setdefault(g, set()).add(ai)
            if en_tags:
                p_idx.ai_tags_en[ai] = en_tags
            if tr_tags:
                p_idx.ai_tags_tr[ai] = tr_tags
            if en_sents:
                p_idx.ann_en[ai] = en_sents
            if tr_sents:
                p_idx.ann_tr[ai] = tr_sents

        return p_idx

    @staticmethod
    def _extract_side(
        tok_list: list[Any],
    ) -> tuple[list[list[dict[str, Any]]], list[str], set[str]]:
        by_coord: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
        tags_seen: list[str] = []
        groups: set[str] = set()
        for t in tok_list or []:
            coord = (
                int(getattr(t, "ch_no", 1)),
                int(getattr(t, "p_no", 1)),
                int(getattr(t, "s_no", 1)),
            )
            clean_ner, grp = normalize_ner_group(str(getattr(t, "ner", "") or ""))
            if grp:
                groups.add(grp)
                label = f"{grp}:{getattr(t, 'surface', '')}"
                if label not in tags_seen:
                    tags_seen.append(label)
            tok_dict = {
                "t": str(getattr(t, "surface", "") or ""),
                "p": str(getattr(t, "pos", "") or ""),
                "n": grp or clean_ner or "O",
                "l": str(getattr(t, "lemma", "") or ""),
                "m": str(getattr(t, "morph", "") or ""),
                "d": str(getattr(t, "dep", "") or ""),
            }
            by_coord.setdefault(coord, []).append(tok_dict)
        sents = [by_coord[k] for k in sorted(by_coord.keys())]
        return sents, tags_seen[:12], groups
