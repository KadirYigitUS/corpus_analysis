"""Exception hierarchy for the corpus toolkit."""


class CorpusToolkitError(Exception):
    """Base class for all toolkit errors."""


class CorpusDataError(CorpusToolkitError):
    """Raised when a corpus file is missing, malformed or internally inconsistent."""


class CorpusSelectionError(CorpusToolkitError):
    """Raised when a user selection (author, text, option) cannot be resolved."""
