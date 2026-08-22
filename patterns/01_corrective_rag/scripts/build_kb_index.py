#!/usr/bin/env python3
"""Learner-facing script to build a local Chroma Knowledge-Base index.

Demonstrates the offline document ingestion pipeline:
load documents -> chunk -> index into Chroma.
"""

import argparse
from pathlib import Path
import sys

import chromadb

from corrective_rag.infrastructure.embeddings.local_embedding import DefaultLocalEmbeddingFunction
from corrective_rag.infrastructure.ingestion.chunker import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DocumentChunker,
)
from corrective_rag.infrastructure.ingestion.chroma_indexer import ChromaIndexer
from corrective_rag.infrastructure.ingestion.document_loader import load_documents_from_directory


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest local Markdown fixture documents and index them into Chroma vector store."
    )
    parser.add_argument(
        "--snapshot-dir",
        type=str,
        default="data/kb_snapshot",
        help="Path to directory containing source documents (default: data/kb_snapshot).",
    )
    parser.add_argument(
        "--db-dir",
        type=str,
        default="data/chroma",
        help="Path to persistent Chroma database storage directory (default: data/chroma).",
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default="corrective-rag-kb",
        help="Chroma collection name (default: corrective-rag-kb).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Max character length per chunk (default: {DEFAULT_CHUNK_SIZE}).",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"Overlapping characters between adjacent chunks (default: {DEFAULT_CHUNK_OVERLAP}).",
    )

    args = parser.parse_args()

    snapshot_path = Path(args.snapshot_dir)
    if not snapshot_path.exists():
        print(f"Error: Snapshot directory '{args.snapshot_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"1. Loading source documents from '{args.snapshot_dir}'...")
    documents = load_documents_from_directory(snapshot_path)
    if not documents:
        print("No Markdown or text documents found to ingest.")
        sys.exit(0)
    print(f"   Loaded {len(documents)} source document(s).")

    print(f"2. Chunking documents (chunk_size={args.chunk_size}, chunk_overlap={args.chunk_overlap})...")
    chunker = DocumentChunker(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    all_chunks = []
    for doc in documents:
        chunks = chunker.chunk_document(doc)
        all_chunks.extend(chunks)
    print(f"   Created {len(all_chunks)} chunk(s).")

    print(f"3. Indexing chunks into Chroma at '{args.db_dir}' (collection: '{args.collection_name}')...")
    embedding_fn = DefaultLocalEmbeddingFunction()
    client = chromadb.PersistentClient(path=args.db_dir)
    collection = client.get_or_create_collection(
        name=args.collection_name,
        embedding_function=embedding_fn,
    )

    indexer = ChromaIndexer(collection=collection)
    indexed_count = indexer.index_chunks(all_chunks)

    print(f"\nSuccessfully indexed {indexed_count} chunk(s) into collection '{args.collection_name}'.")


if __name__ == "__main__":
    main()
