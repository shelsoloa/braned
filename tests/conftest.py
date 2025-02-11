import os
from typing import Generator

import pytest

from braned.vector_stores.sqlite import SQLiteVectorStore


@pytest.fixture
def test_db_path(tmp_path: str):
    """Fixture to create a temporary database path."""
    return str(tmp_path / "test_vector_store.db")


@pytest.fixture
def vector_store(test_db_path: str) -> Generator[SQLiteVectorStore, None, None]:
    """Fixture to create a SQLiteVectorStore instance."""
    store = SQLiteVectorStore(
        database_path=test_db_path, table_name="test_vectors", embed_dim=4
    )

    yield store

    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
