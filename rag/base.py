"""Contracts for the future RAG (Retrieval Augmented Generation) module.

Nothing here is used yet. These interfaces fix the shape of the pieces so
they can be built one by one later without touching the API or the engine:

    documents/  --DocumentLoader-->  Document
    Document    --TextSplitter---->  Chunk (small passages)
    Chunk       --Embedder-------->  vector
    vectors     --VectorStore----->  search(question) -> best Chunks
    best Chunks + question  -->  prompt sent to the InferenceEngine
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Document:
    """A source document (book, law, decree, technical manual...)."""

    doc_id: str
    text: str
    source: Path
    metadata: dict = field(default_factory=dict)  # ex: {"type": "décret", "date": "2024-01-01"}


@dataclass(frozen=True)
class Chunk:
    """A small passage of a document, the unit stored in the vector base."""

    chunk_id: str
    doc_id: str
    text: str
    metadata: dict = field(default_factory=dict)


class DocumentLoader(Protocol):
    def load(self, path: Path) -> list[Document]: ...


class TextSplitter(Protocol):
    def split(self, document: Document) -> list[Chunk]: ...


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class VectorStore(Protocol):
    def add(self, chunks: list[Chunk], vectors: list[list[float]]) -> None: ...

    def search(self, vector: list[float], top_k: int) -> list[Chunk]: ...
