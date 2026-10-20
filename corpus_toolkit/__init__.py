"""corpus_toolkit — educational, memory-preserving corpus analysis of Turkish SF author-translators."""

from .config import SCHEMA_VERSION, TOOLKIT_VERSION, CorpusPathConfig
from .errors import CorpusDataError, CorpusSelectionError, CorpusToolkitError
from .loader import CorpusLoader, CorpusSelection, ParallelCorpus
from .parallel_view import NdaOverlay, parallel_html, show_parallel
from .registry import CorpusRegistry, TextRecord
from .table_view import (
    disable_interactive_tables,
    enable_interactive_tables,
    show_table,
    table_html,
)
from .tokenview import TokenView

__version__ = TOOLKIT_VERSION
__all__ = [
    "CorpusLoader",
    "CorpusSelection",
    "ParallelCorpus",
    "CorpusRegistry",
    "TextRecord",
    "TokenView",
    "CorpusPathConfig",
    "CorpusToolkitError",
    "CorpusDataError",
    "CorpusSelectionError",
    "NdaOverlay",
    "parallel_html",
    "show_parallel",
    "table_html",
    "show_table",
    "enable_interactive_tables",
    "disable_interactive_tables",
    "SCHEMA_VERSION",
    "TOOLKIT_VERSION",
    "__version__",
]
