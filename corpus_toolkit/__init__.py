"""corpus_toolkit — educational, memory-preserving corpus analysis of Turkish SF author-translators."""

from .config import SCHEMA_VERSION, TOOLKIT_VERSION, CorpusPathConfig
from .errors import CorpusDataError, CorpusSelectionError, CorpusToolkitError
from .loader import CorpusLoader, CorpusSelection, ParallelCorpus
from .registry import CorpusRegistry, TextRecord
from .tokenview import TokenView

__version__ = TOOLKIT_VERSION
__all__ = [
    "CorpusLoader", "CorpusSelection", "ParallelCorpus", "CorpusRegistry", "TextRecord",
    "TokenView", "CorpusPathConfig", "CorpusToolkitError", "CorpusDataError",
    "CorpusSelectionError", "SCHEMA_VERSION", "TOOLKIT_VERSION", "__version__",
]
