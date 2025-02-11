import pytest
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQuery, VectorStoreQueryMode
from braned.vector_stores.sqlite import SQLiteVectorStore


def create_test_node(node_id: str, text: str, embedding: list[float]) -> TextNode:
    """Helper function to create a test node."""
    return TextNode(
        text=text,
        id_=node_id,
        embedding=embedding,
        metadata={"test_key": "test_value"},
    )


def test_add_and_query_single_node(vector_store: SQLiteVectorStore):
    """Test adding a single node and querying it."""
    # Create a test node
    node = create_test_node("test1", "This is a test document", [1.0, 0.0, 0.0, 0.0])

    # Add node to store
    ids = vector_store.add([node])
    assert len(ids) == 1
    assert ids[0] == "test1"

    # Query the store
    query = VectorStoreQuery(
        query_embedding=[1.0, 0.0, 0.0, 0.0],
        similarity_top_k=1,
        mode=VectorStoreQueryMode.DEFAULT,
    )

    result = vector_store.query(query)

    assert len(result.nodes) == 1
    assert result.nodes[0].metadata["test_key"] == "test_value"
    assert result.ids[0] == "test1"
    assert len(result.similarities) == 1
    assert result.similarities[0] >= 0  # Distance should be non-negative


def test_add_multiple_nodes(vector_store: SQLiteVectorStore):
    """Test adding and querying multiple nodes."""
    nodes = [
        create_test_node("test1", "First document", [1.0, 0.0, 0.0, 0.0]),
        create_test_node("test2", "Second document", [0.0, 1.0, 0.0, 0.0]),
        create_test_node("test3", "Third document", [0.0, 0.0, 1.0, 0.0]),
    ]

    ids = vector_store.add(nodes)
    assert len(ids) == 3

    query = VectorStoreQuery(
        query_embedding=[1.0, 0.0, 0.0, 0.0],
        similarity_top_k=3,
        mode=VectorStoreQueryMode.DEFAULT,
    )

    result = vector_store.query(query)
    assert len(result.nodes) == 3
    assert len(result.similarities) == 3
    assert len(result.ids) == 3


def test_delete_node(vector_store: SQLiteVectorStore):
    """Test deleting a node."""
    node = create_test_node("test1", "This is a test document", [1.0, 0.0, 0.0, 0.0])

    vector_store.add([node])
    vector_store.delete("test1")

    query = VectorStoreQuery(
        query_embedding=[1.0, 0.0, 0.0, 0.0],
        similarity_top_k=1,
        mode=VectorStoreQueryMode.DEFAULT,
    )

    result = vector_store.query(query)
    assert len(result.nodes) == 0


def test_query_top_k(vector_store: SQLiteVectorStore):
    """Test querying with different top_k values."""
    nodes = [
        create_test_node("test1", "First document", [1.0, 0.0, 0.0, 0.0]),
        create_test_node("test2", "Second document", [0.9, 0.1, 0.0, 0.0]),
        create_test_node("test3", "Third document", [0.8, 0.2, 0.0, 0.0]),
    ]

    vector_store.add(nodes)

    query = VectorStoreQuery(
        query_embedding=[1.0, 0.0, 0.0, 0.0],
        similarity_top_k=2,
        mode=VectorStoreQueryMode.DEFAULT,
    )

    result = vector_store.query(query)
    assert len(result.nodes) == 2
    assert result.ids[0] == "test1"  # Should be closest to query vector


def test_invalid_query_mode(vector_store: SQLiteVectorStore):
    """Test that invalid query modes raise an exception."""
    query = VectorStoreQuery(
        query_embedding=[1.0, 0.0, 0.0, 0.0],
        similarity_top_k=1,
        mode=VectorStoreQueryMode.MMR,  # Unsupported mode
    )

    with pytest.raises(ValueError, match="Unsupported query mode"):
        vector_store.query(query)


def test_close_and_database_persistence(test_db_path):
    """Test that data persists after closing and reopening the database."""
    # Create first instance and add data
    store1 = SQLiteVectorStore(
        database_path=test_db_path, table_name="test_vectors", embed_dim=4
    )

    node = create_test_node("test1", "This is a test document", [1.0, 0.0, 0.0, 0.0])

    store1.add([node])

    # Create new instance with same database path
    store2 = SQLiteVectorStore(
        database_path=test_db_path, table_name="test_vectors", embed_dim=4
    )

    query = VectorStoreQuery(
        query_embedding=[1.0, 0.0, 0.0, 0.0],
        similarity_top_k=1,
        mode=VectorStoreQueryMode.DEFAULT,
    )

    result = store2.query(query)
    assert len(result.nodes) == 1
    assert result.ids[0] == "test1"
