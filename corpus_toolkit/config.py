"""Path and runtime configuration.

Nothing in the toolkit hard-codes an absolute path.  Locations are derived from the
thesis workspace root (auto-detected as ``<repo>/../..``) and can be overridden with
environment variables so the repository stays portable:

``CORPUS_THESIS_ROOT``   thesis workspace root (holds ``corpus/`` and ``data/``)
``CORPUS_DATA_DIR``      output root (default ``<thesis>/data/corpus_analysis``)
``CORPUS_AUTHOR_CODES``  comma separated author-translator codes (default ``SM,ZB,OK``)
``CORPUS_CACHE_POLICY``  ``keep`` | ``clear`` | ``ask`` (default ``ask``; falls back to ``keep``
                         whenever no interactive stdin is available, e.g. nbconvert/CI)
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

#: Bump when the on-disk cache layout or derived-column semantics change.
SCHEMA_VERSION = "2"
TOOLKIT_VERSION = "0.1.0"

#: Focal author-translators of this sub-corpus (codes as stored in the metadata TSVs).
DEFAULT_AUTHOR_CODES: tuple[str, ...] = ("SM", "ZB", "OK")

CACHE_POLICIES = ("keep", "clear", "ask")


def _default_thesis_root() -> Path:
    # corpus_toolkit/config.py -> corpus_toolkit -> corpus_analysis -> scripts -> <thesis>
    return Path(__file__).resolve().parents[3]


@dataclass
class CorpusPathConfig:
    """Resolved filesystem layout used by every toolkit component."""

    thesis_root: Path = field(default_factory=_default_thesis_root)
    data_root: Path | None = None
    author_codes: tuple[str, ...] = DEFAULT_AUTHOR_CODES

    def __post_init__(self) -> None:
        self.thesis_root = Path(self.thesis_root).expanduser().resolve()
        if self.data_root is None:
            self.data_root = self.thesis_root / "data" / "corpus_analysis"
        self.data_root = Path(self.data_root).expanduser().resolve()
        self.author_codes = tuple(c.strip() for c in self.author_codes if c.strip())

    @classmethod
    def from_env(cls) -> "CorpusPathConfig":
        """Build a configuration honouring the ``CORPUS_*`` environment variables."""
        root = os.environ.get("CORPUS_THESIS_ROOT")
        data = os.environ.get("CORPUS_DATA_DIR")
        codes = os.environ.get("CORPUS_AUTHOR_CODES")
        kwargs: dict[str, object] = {}
        if root:
            kwargs["thesis_root"] = Path(root)
        if data:
            kwargs["data_root"] = Path(data)
        if codes:
            kwargs["author_codes"] = tuple(codes.split(","))
        return cls(**kwargs)  # type: ignore[arg-type]

    # ---- source corpus -------------------------------------------------
    @property
    def translation_tsv(self) -> Path:
        return self.thesis_root / "corpus" / "SF_Novels" / "txt_translation_book_locations.tsv"

    @property
    def indigenous_tsv(self) -> Path:
        return self.thesis_root / "corpus" / "SF_Novels" / "txt_indigenous_book_locations.tsv"

    @property
    def aligned_root(self) -> Path:
        return self.thesis_root / "data" / "alignment"

    @property
    def indigenous_root(self) -> Path:
        return self.thesis_root / "data" / "indigenous"

    # ---- outputs -------------------------------------------------------
    @property
    def cache_dir(self) -> Path:
        assert self.data_root is not None
        return self.data_root / ".cache"

    @property
    def reports_dir(self) -> Path:
        assert self.data_root is not None
        return self.data_root / "reports"

    @property
    def tables_dir(self) -> Path:
        assert self.data_root is not None
        return self.data_root / "tables"

    @property
    def figures_dir(self) -> Path:
        assert self.data_root is not None
        return self.data_root / "figures"

    def ensure_dirs(self) -> None:
        """Create the output directory tree (idempotent)."""
        for directory in (self.cache_dir, self.reports_dir, self.tables_dir, self.figures_dir):
            directory.mkdir(parents=True, exist_ok=True)


def cache_policy_from_env(default: str = "ask") -> str:
    """Return the validated ``CORPUS_CACHE_POLICY`` value."""
    value = os.environ.get("CORPUS_CACHE_POLICY", default).strip().lower()
    return value if value in CACHE_POLICIES else default
