"""Chroma vector database retriever adapter.

Implements the Retriever domain port via structural subtyping without importing
Chroma in Domain or Application layers.
"""

from collections.abc import Sequence
from typing import Any

import chromadb

from corrective_rag.domain.entities.document import Document
from corrective_rag.domain.entities.question import Question

DEFAULT_TOP_K = 4


class ChromaRetriever:
    """Infrastructure retriever implementation backed by a Chroma vector collection.

    Note on Structural Subtyping:
        This class structurally satisfies the Domain `Retriever` protocol contract
        (`retrieve(self, question: Question) -> Sequence[Document]`) without explicit
        class inheritance. Application code depends on the `Retriever` protocol interface,
        maintaining Clean Architecture boundary isolation.
    """

    def __init__(
        self,
        collection: chromadb.Collection,
        top_k: int = DEFAULT_TOP_K,
    ) -> None:
        """Initialize ChromaRetriever with a target collection and candidate count.

        Args:
            collection: Chroma Collection instance containing indexed chunks.
            top_k: Number of nearest neighbor candidates to retrieve (must be > 0).

        Raises:
            ValueError: If top_k <= 0.
        """
        if top_k <= 0:
            raise ValueError(f"top_k must be > 0, got {top_k}.")

        self._collection = collection
        self._top_k = top_k

    @property
    def top_k(self) -> int:
        """Return configured top_k candidate limit."""
        return self._top_k

    def retrieve(self, question: Question) -> Sequence[Document]:
        """Retrieve top-k candidate documents from Chroma relevant to the user question.

        Args:
            question: Domain Question entity containing query text.

        Returns:
            Ordered sequence of provider-neutral Domain Document entities.
            Returns an empty sequence if collection is empty or no candidates match.
        """
        # If collection is empty, return empty sequence safely
        if self._collection.count() == 0:
            return []

        # Limit requested n_results to collection item count if collection has fewer items
        effective_k = min(self._top_k, self._collection.count())

        results = self._collection.query(
            query_texts=[question.text],
            n_results=effective_k,
            include=["documents", "metadatas", "distances"],
        )

        documents_list = results.get("documents")
        if not documents_list or not documents_list[0]:
            return []

        doc_texts = documents_list[0]
        metadatas_list = results.get("metadatas")
        metadatas = metadatas_list[0] if metadatas_list else []
        distances_list = results.get("distances")
        distances = distances_list[0] if distances_list else []

        domain_documents: list[Document] = []
        for i, text in enumerate(doc_texts):
            meta: dict[str, Any] = dict(metadatas[i]) if i < len(metadatas) and metadatas[i] else {}
            
            source = str(meta.get("source", "chroma_kb"))
            title_val = meta.get("document_title")
            title = str(title_val) if title_val is not None else None

            # Preserve vector distance in metadata if available
            doc_metadata: dict[str, object] = dict(meta)
            if i < len(distances) and distances[i] is not None:
                doc_metadata["retrieval_distance"] = float(distances[i])

            domain_documents.append(
                Document(
                    content=text,
                    source=source,
                    title=title,
                    metadata=doc_metadata,
                )
            )

        return domain_documents
