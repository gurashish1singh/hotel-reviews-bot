from __future__ import annotations

import os

import pandas as pd
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_ollama import OllamaEmbeddings

DEFAULT_DB_LOCATION = "./vector_db/chroma_langchain_db"


# TODO: make this more generic
def vectorize(
    file_path: str,
    collection_name: str,
    db_location: str = DEFAULT_DB_LOCATION,
) -> VectorStoreRetriever:
    """
    Takes in a CSV path, name of vector store collection, and
    a location to persist the embeddings.
    """
    df = pd.read_json(file_path)
    df.columns = list(map(str.lower, df.columns))
    # TODO: refactor to check for new changes
    add_documents: bool = not os.path.exists(db_location)
    # TODO: store model name in env
    embedddings = OllamaEmbeddings(model="mxbai-embed-large")
    vector_store = Chroma(
        collection_name=collection_name,
        persist_directory=db_location,
        embedding_function=embedddings,
    )

    if add_documents:
        documents = []
        ids = []

        for row in df.itertuples():
            _id = row.Index
            document = Document(
                page_content=f"positive: {row.positive_text}\n\nnegative: {row.negative_text}",
                metadata={
                    "title": row.title,
                    "rating": row.score_value,
                    "reviewed_date": row.reviewed_date,
                    "helpful_count": row.helpful_count,
                    "room_type": row.room_type,
                },
                id=str(_id),
            )
            ids.append(str(_id))
            documents.append(document)

        vector_store.add_documents(documents=documents, ids=ids)

    return vector_store.as_retriever(
        # N number of documents to pass in to llm
        search_kwargs={"k": 20},
    )
