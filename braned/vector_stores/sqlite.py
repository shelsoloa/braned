import json
from typing import Any

import sqlite3
import sqlite_vec

from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    VectorStoreQuery,
    VectorStoreQueryMode,
    VectorStoreQueryResult,
)
from llama_index.core.vector_stores.utils import (
    metadata_dict_to_node,
    node_to_metadata_dict,
)
from llama_index.core.schema import BaseNode
from loguru import logger
from pydantic import PrivateAttr


class SQLiteVectorStore(BasePydanticVectorStore):
    """
    A vector store implementation using SQLite with sqlite-vec extension.
    This allows for efficient similarity search directly in the database.
    """

    stores_text: bool = True
    flat_metadata: bool = False

    database_path: str
    table_name: str
    embed_dim: int

    _connection: sqlite3.Connection | None = PrivateAttr(default=None)

    def __init__(
        self,
        database_path: str,
        table_name: str = "vec_files",
        embed_dim: int = 512,
    ):
        table_name = table_name.lower()

        super().__init__(
            database_path=database_path,
            table_name=table_name,
            embed_dim=embed_dim,
        )

        self._initialize()

    def _initialize(self) -> None:
        if self._connection is None:
            self._connection = sqlite3.connect(self.database_path)

            # load sqlite-vec extension
            self._connection.enable_load_extension(True)
            sqlite_vec.load(self._connection)
            self._connection.enable_load_extension(False)
            logger.debug(f"Connected to {self.database_path}")

            (vec_version,) = self._connection.execute("SELECT vec_version()").fetchone()
            logger.debug(f"sqlite-vec version: {vec_version}")

            # create vec_files table if it doesn't exist
            self._connection.execute(
                f"""
                create virtual table if not exists {self.table_name} using vec0 (
                    node_id text primary key,
                    embedding float[{self.embed_dim}],
                    +content text,
                    +metadata text
                );
                """
            )

    @property
    def client(self) -> Any:
        if not self._client:
            return None
        return self._client

    def _node_to_sqlite_row(self, node: BaseNode) -> str:
        """Convert a node to a sqlite row

        Returns a string in order of node_id, embedding, metadata, content.
        """
        node_id = node.node_id
        embedding = str(node.embedding)
        metadata = node_to_metadata_dict(
            node, remove_text=True, flat_metadata=self.flat_metadata
        )
        content = node.text
        return f"('{node_id}', '{embedding}', '{json.dumps(metadata)}', '{content}')"

    def add(
        self,
        nodes: list[BaseNode],
        **kwargs: Any,
    ) -> list[str]:
        insert_values = ",".join([self._node_to_sqlite_row(n) for n in nodes])

        print(insert_values)

        self._connection.execute(
            f"""
            insert into {self.table_name} (node_id, embedding, metadata, content)
            values 
                {insert_values};
            """
        )
        self._connection.commit()

        return [n.node_id for n in nodes]

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        self._connection.execute(
            f"""
            delete from
                {self.table_name}
            where
                node_id = '{ref_doc_id}';
            """
        )
        self._connection.commit()

    def query(
        self,
        query: VectorStoreQuery,
        **kwargs: Any,
    ) -> VectorStoreQueryResult:
        if query.mode != VectorStoreQueryMode.DEFAULT:
            raise ValueError(f"Unsupported query mode: {query.mode}")

        rows = self._connection.execute(
            f"""
            select 
                node_id,
                content,
                metadata,
                distance
            from 
                {self.table_name}
            where
                embedding match '{str(query.query_embedding)}'
            order by
                distance
            limit {query.similarity_top_k};
            """
        ).fetchall()

        # Convert db rows to query result
        nodes = []
        similarities = []
        ids = []
        for row in rows:
            print("--------------------------------")
            print(row[0])
            print(row[1])
            print(row[2])
            print(row[3])
            print("--------------------------------")

            ids.append(row[0])

            # Convert metadata to node
            nodes.append(
                metadata_dict_to_node(json.loads(row[2])),
            )

            similarities.append(row[3])

        return VectorStoreQueryResult(
            nodes=nodes,
            similarities=similarities,
            ids=ids,
        )
