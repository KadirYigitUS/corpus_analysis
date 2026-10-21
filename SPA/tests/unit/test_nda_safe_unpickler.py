"""Test security isolation and safe unpickling of NDA caches."""

import io
import pickle

import pytest

from SPA.repositories.corpus_repository import CorpusRepository
from SPA.repositories.nda_cache_repository import (
    NdaCacheRepository,
    SafeNdaUnpickler,
)


def test_nda_safe_unpickler_blocks_unauthorized_classes():
    """Verify that SafeNdaUnpickler refuses arbitrary execution payloads."""
    repo = CorpusRepository()
    nda_root = (
        repo.loader.config.thesis_root
        / "scripts"
        / "Neologism_Dictionary_Annotation"
    )

    # Malicious payload trying to unpickle os.system
    class Exploit:
        def __reduce__(self):
            import os

            return (os.system, ("echo compromised",))

    malicious_bytes = pickle.dumps(Exploit())

    unpickler = SafeNdaUnpickler(io.BytesIO(malicious_bytes), nda_root)

    with pytest.raises(pickle.UnpicklingError):
        unpickler.load()


def test_nda_cache_repository_extraction():
    """Verify NdaCacheRepository safely parses tripartite dictionary."""
    repo = CorpusRepository()
    nda_repo = NdaCacheRepository(repo.loader)

    pair_code = "IR-IA_BR-SM"
    dict_data = nda_repo.get_tripartite_dictionary(pair_code)

    assert "linked" in dict_data
    assert "single_eng" in dict_data
    assert "single_tur" in dict_data
    assert isinstance(dict_data["linked"], list)
