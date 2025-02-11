import os

import openai
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.indices import VectorStoreIndex
from loguru import logger
from dotenv import load_dotenv

from braned.vector_stores.sqlite import SQLiteVectorStore

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def main():
    documents = SimpleDirectoryReader(
        input_files=["data/me.md"],
    ).load_data()
    logger.debug(f"Loaded {len(documents)} documents")

    vector_store = SQLiteVectorStore(
        database_path="local.db",
        table_name="vec_files",
        embed_dim=1536,
    )
    logger.debug("Vector store initialized")

    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    logger.debug("Storage context initialized")

    index = VectorStoreIndex(
        documents,
        storage_context=storage_context,
        show_progress=True,
    )
    logger.debug("Index initialized")

    query = "What is my name and how old am I?"
    logger.debug(f"Querying index: {query}")

    query_engine = index.as_query_engine()
    response = query_engine.query(query)
    logger.debug(f"Response: {response}")


if __name__ == "__main__":
    main()
