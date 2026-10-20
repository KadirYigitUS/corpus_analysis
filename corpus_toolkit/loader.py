"""The eight corpus loaders (lazy; nothing is parsed until a table is requested).

======================  ===============================================================
Method                  What you get
======================  ===============================================================
``load_all_english``    the 5 English source texts
``load_all_turkish``    the 5 Turkish translations + 3 Turkish indigenous novels
``load_translation_pairs``  5 aligned (English ⇄ Turkish) pairs – the parallel corpus
``load_indigenous``     the 3 indigenous Turkish novels
``load_all``            all 13 texts
``load_author_related`` every text related to author-translator(s): pairs + indigenous
``load_author_turkish`` only the Turkish texts (translations + indigenous) of author(s)
``load_text``           a single text by code or title
======================  ===============================================================

Every ``describe()`` prints the *full author names and book titles*.
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

import pandas as pd

from .alignment import AlignmentIndex
from .cache import CorpusCacheManager
from .config import CorpusPathConfig
from .lazy import LazyCorpusText, rss_mb
from .registry import INDIGENOUS, SOURCE, TRANSLATION, CorpusRegistry, PairSpec, TextRecord
from .textutil import LANG_EN, LANG_TR


@dataclass
class CorpusSelection:
    """An ordered group of lazy texts with a human-readable title."""

    title: str
    registry: CorpusRegistry
    texts: list[LazyCorpusText] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.texts)

    def __iter__(self) -> Iterator[LazyCorpusText]:
        return iter(self.texts)

    def __getitem__(self, code: str) -> LazyCorpusText:
        for t in self.texts:
            if t.record.code == code:
                return t
        raise KeyError(code)

    @property
    def codes(self) -> list[str]:
        return [t.record.code for t in self.texts]

    def describe(self) -> str:
        lines = [f"📚 {self.title} — {len(self)} text(s)"]
        lines += [f"  • {self.registry.display(t.record)}" for t in self.texts]
        out = "\n".join(lines)
        print(out)
        return out

    def iter_evicting(self) -> Iterator[LazyCorpusText]:
        """Yield texts one at a time and free each from RAM afterwards (memory-safe loop)."""
        for t in self.texts:
            try:
                yield t
            finally:
                t.evict()

    def evict_all(self) -> None:
        for t in self.texts:
            t.evict()

    def summary(self) -> pd.DataFrame:
        rows = []
        for t in self.texts:
            s = t.summary()
            rows.append({"author_translator": t.record.focal_name, "title": t.record.title,
                         "code": t.record.code, "language": t.record.language,
                         "type": t.record.corpus_type, "sentences": s["n_sentences"],
                         "tokens": s["n_tokens"]})
        return pd.DataFrame(rows)


@dataclass
class ParallelCorpus:
    """Aligned pairs; each item is ``(PairSpec, English text, Turkish text)``."""

    title: str
    registry: CorpusRegistry
    items: list[tuple[PairSpec, LazyCorpusText, LazyCorpusText]] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[tuple[PairSpec, LazyCorpusText, LazyCorpusText]]:
        return iter(self.items)

    def describe(self) -> str:
        lines = [f"🔗 {self.title} — {len(self)} pair(s)"]
        lines += [f"  • {self.registry.display_pair(p)}" for p, _, _ in self.items]
        out = "\n".join(lines)
        print(out)
        return out

    def evict_all(self) -> None:
        for _, e, t in self.items:
            e.evict()
            t.evict()

    def flatten(self) -> CorpusSelection:
        texts = [x for _, e, t in self.items for x in (e, t)]
        return CorpusSelection(self.title, self.registry, texts)


class CorpusLoader:
    """Entry point of the toolkit: builds registry + cache and hands out selections."""

    def __init__(self, config: CorpusPathConfig | None = None,
                 cache_policy: str | None = None, verbose: bool = True) -> None:
        self.config = config or CorpusPathConfig.from_env()
        self.config.ensure_dirs()
        self.cache = CorpusCacheManager(self.config.cache_dir)
        self.cache.apply_policy(cache_policy, verbose=verbose)
        self.registry = CorpusRegistry.from_config(self.config)
        self._lazy: dict[str, LazyCorpusText] = {}
        self._align: dict[str, AlignmentIndex] = {}
        self.verbose = verbose

    def alignment_index(self, pair: PairSpec) -> AlignmentIndex:
        """Coordinates ⇄ alignment-group lookups for ``pair`` (cached, a few thousand entries)."""
        if pair.pair_id not in self._align:
            self._align[pair.pair_id] = AlignmentIndex(pair)
        return self._align[pair.pair_id]

    # one LazyCorpusText per code, shared between selections
    def _lazy_for(self, rec: TextRecord) -> LazyCorpusText:
        if rec.code not in self._lazy:
            self._lazy[rec.code] = LazyCorpusText(rec, self.cache)
        return self._lazy[rec.code]

    def _selection(self, title: str, recs: Iterable[TextRecord]) -> CorpusSelection:
        return CorpusSelection(title, self.registry, [self._lazy_for(r) for r in recs])

    # ------------------------------------------------------------ 8 loaders
    def load_all_english(self) -> CorpusSelection:
        return self._selection("All English texts (sources)",
                               self.registry.select(language=LANG_EN))

    def load_all_turkish(self) -> CorpusSelection:
        return self._selection("All Turkish texts (translations + indigenous)",
                               self.registry.select(language=LANG_TR))

    def load_translation_pairs(self, author: str | None = None) -> ParallelCorpus:
        pairs = [p for p in self.registry.pairs.values()
                 if author is None or p.tur.focal_code == self.registry.resolve_author(author)]
        pairs.sort(key=lambda p: (p.tur.focal_code, p.tur.code))
        return ParallelCorpus("Translation pairs (parallel corpus)", self.registry,
                              [(p, self._lazy_for(p.eng), self._lazy_for(p.tur)) for p in pairs])

    def load_indigenous(self, author: str | None = None) -> CorpusSelection:
        return self._selection("Indigenous Turkish SF novels",
                               self.registry.select(corpus_type=INDIGENOUS, author=author))

    def load_all(self) -> CorpusSelection:
        return self._selection("All texts", self.registry.select())

    def load_author_related(self, author: str | None = None) -> CorpusSelection:
        """Translations' sources + translations + indigenous of ``author`` (or all focal authors)."""
        name = self.registry.author_names[self.registry.resolve_author(author)] if author else "all author-translators"
        return self._selection(f"Texts related to {name}", self.registry.select(author=author))

    def load_author_turkish(self, author: str | None = None) -> CorpusSelection:
        recs = [r for r in self.registry.select(language=LANG_TR, author=author)
                if r.corpus_type in (TRANSLATION, INDIGENOUS)]
        name = self.registry.author_names[self.registry.resolve_author(author)] if author else "all author-translators"
        return self._selection(f"Turkish texts of {name}", recs)

    def load_text(self, query: str) -> LazyCorpusText:
        return self._lazy_for(self.registry.resolve_text(query))

    # ----------------------------------------------------------------- misc
    def sources_of(self, author: str | None = None) -> CorpusSelection:
        return self._selection("English sources", self.registry.select(
            corpus_type=SOURCE, author=author))

    def memory_report(self) -> pd.DataFrame:
        rows = [{"code": c, "loaded": t.loaded, "table_mb": round(t.memory_mb(), 1)}
                for c, t in self._lazy.items()]
        df = pd.DataFrame(rows)
        if self.verbose:
            print(f"Process RSS: {rss_mb():.0f} MB | tables in RAM: "
                  f"{df['table_mb'].sum() if len(df) else 0:.0f} MB")
        return df

    def evict_all(self, *, verbose: bool = False) -> None:
        """Evict all loaded text tables from memory."""
        for t in self._lazy.values():
            t.evict(verbose=verbose)

    def rss_mb(self) -> float:
        """Current process resident set size in megabytes."""
        return rss_mb()

