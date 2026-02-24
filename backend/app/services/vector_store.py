import asyncio
import inspect
import time
import uuid
from collections.abc import AsyncGenerator
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from langchain_qdrant import QdrantVectorStore

from app.core.config import settings
from app.core.logging import get_logger
from app.services.embeddings import EMBEDDING_DIMENSION, get_embeddings

logger = get_logger(__name__)
T = TypeVar("T")

COLLECTION_NAME = "rfp_demo_collection"


def _ensure_initialized(method: Callable[..., T]) -> Callable[..., T]:
    """Decorador que inicializa el vector store antes de ejecutar el metodo."""
    if inspect.isasyncgenfunction(method):
        @wraps(method)
        async def asyncgen_wrapper(self: "RAGService", *args, **kwargs):
            if self._vector_store is None:
                await self._initialize()
            async for item in method(self, *args, **kwargs):
                yield item

        return asyncgen_wrapper

    @wraps(method)
    async def wrapper(self: "RAGService", *args, **kwargs) -> T:
        if self._vector_store is None:
            await self._initialize()
        return await method(self, *args, **kwargs)
    return wrapper


class RAGService:
    """Servicio de RAG con Qdrant in-memory como vector store.

    Zero-maintenance solution for ephemeral containers.
    Data is stored entirely in RAM and will be wiped on restart.
    """

    def __init__(self):
        self._client: QdrantClient | None = None
        self._vector_store: QdrantVectorStore | None = None
        self._embeddings = get_embeddings()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    async def _initialize(self) -> None:
        """Inicializa el cliente Qdrant in-memory y el vector store."""
        try:
            self._client = QdrantClient(location=":memory:")

            collections = await asyncio.to_thread(self._client.get_collections)
            collection_names = [c.name for c in collections.collections]

            if COLLECTION_NAME not in collection_names:
                logger.info(f"Creando colección '{COLLECTION_NAME}' en Qdrant in-memory")
                await asyncio.to_thread(
                    self._client.create_collection,
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIMENSION,
                        distance=Distance.COSINE,
                    ),
                )

            self._vector_store = QdrantVectorStore(
                client=self._client,
                collection_name=COLLECTION_NAME,
                embedding=self._embeddings,
            )

            logger.info("Qdrant in-memory inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando Qdrant in-memory: {e}")
            raise

    async def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embeds all texts using parallel API calls batched by embedding_batch_size."""
        batch_size = settings.embedding_batch_size
        batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
        # Fire all embedding API requests concurrently
        results = await asyncio.gather(
            *[asyncio.to_thread(self._embeddings.embed_documents, batch) for batch in batches]
        )
        # Flatten list-of-lists
        return [vector for batch_vectors in results for vector in batch_vectors]

    async def warmup(self) -> None:
        """Pre-calienta la API de embeddings y el vector store para la primera solicitud."""
        if self._vector_store is None:
            await self._initialize()
        # Single dummy call to load the remote model into memory
        await asyncio.to_thread(self._embeddings.embed_query, "warmup")
        logger.info("Embeddings pre-calentados correctamente")

    @_ensure_initialized
    async def ingest_document(self, file_path: Path, original_filename: str | None = None) -> int:
        """Procesa un PDF y sube los chunks al vector store in-memory.

        Optimizations:
        - PDF loading and splitting run in a thread pool to not block the event loop
        - All chunks are embedded in parallel batches via concurrent API calls
        - All vectors are inserted in a single Qdrant upsert call
        """
        source_name = original_filename or file_path.name
        t_start = time.monotonic()

        try:
            loader = PyPDFLoader(str(file_path))
            pages = await asyncio.to_thread(loader.load)
            t_parsed = time.monotonic()

            chunks = await asyncio.to_thread(self._splitter.split_documents, pages)
            t_split = time.monotonic()

            if not chunks:
                logger.warning(f"No se generaron chunks de '{source_name}'")
                return 0

            for chunk in chunks:
                chunk.metadata["source"] = source_name

            # Embed all chunks — parallel batches saturate the API concurrently
            texts = [chunk.page_content for chunk in chunks]
            vectors = await self._embed_texts(texts)
            t_embed = time.monotonic()

            # Single upsert for all points (one round-trip to Qdrant)
            points = self._build_points(chunks, vectors)
            await asyncio.to_thread(
                self._client.upsert,
                collection_name=COLLECTION_NAME,
                points=points,
            )
            t_upsert = time.monotonic()

            elapsed = t_upsert - t_start
            logger.info(
                f"Ingestados {len(chunks)} chunks de '{source_name}' en {elapsed:.1f}s "
                f"(parse={t_parsed - t_start:.1f}s, split={t_split - t_parsed:.1f}s, "
                f"embed={t_embed - t_split:.1f}s, upsert={t_upsert - t_embed:.1f}s)"
            )
            return len(chunks)
        except Exception as e:
            logger.error(f"Error procesando documento '{file_path}': {e}")
            raise

    @_ensure_initialized
    async def ingest_document_streaming(
        self, file_path: Path, original_filename: str | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Procesa un PDF con eventos de progreso via async generator.

        Yields dicts con llaves: phase, message, y datos opcionales.
        Fases: parsing -> splitting -> embedding -> indexing -> done.
        """
        source_name = original_filename or file_path.name
        t_start = time.monotonic()

        try:
            # Phase 1: Parse PDF
            yield {"phase": "parsing", "message": "Extrayendo texto del PDF..."}
            loader = PyPDFLoader(str(file_path))
            pages = await asyncio.to_thread(loader.load)

            # Phase 2: Split into chunks
            yield {"phase": "splitting", "message": f"Dividiendo {len(pages)} paginas en chunks..."}
            chunks = await asyncio.to_thread(self._splitter.split_documents, pages)

            if not chunks:
                logger.warning(f"No se generaron chunks de '{source_name}'")
                yield {"phase": "done", "message": "Sin contenido extraible", "chunks": 0, "elapsed_seconds": 0}
                return

            for chunk in chunks:
                chunk.metadata["source"] = source_name

            # Phase 3: Embed in batches with progress
            texts = [chunk.page_content for chunk in chunks]
            batch_size = settings.embedding_batch_size
            batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
            total_batches = len(batches)

            all_vectors: list[list[float]] = []
            for idx, batch in enumerate(batches, 1):
                yield {
                    "phase": "embedding",
                    "message": f"Generando embeddings... (lote {idx}/{total_batches})",
                    "batch_current": idx,
                    "batch_total": total_batches,
                }
                batch_vectors = await asyncio.to_thread(self._embeddings.embed_documents, batch)
                all_vectors.extend(batch_vectors)

            # Phase 4: Index into Qdrant
            yield {"phase": "indexing", "message": "Indexando en vector store..."}
            points = self._build_points(chunks, all_vectors)
            await asyncio.to_thread(
                self._client.upsert,
                collection_name=COLLECTION_NAME,
                points=points,
            )

            elapsed = time.monotonic() - t_start
            logger.info(f"Ingestados {len(chunks)} chunks de '{source_name}' en {elapsed:.1f}s (streaming)")
            yield {
                "phase": "done",
                "message": f"Documento procesado ({len(chunks)} chunks en {elapsed:.1f}s)",
                "chunks": len(chunks),
                "elapsed_seconds": round(elapsed, 1),
            }
        except Exception as e:
            logger.error(f"Error procesando documento '{file_path}': {e}")
            yield {"phase": "error", "message": f"Error: {str(e)}"}
            raise

    @staticmethod
    def _build_points(chunks: list[Document], vectors: list[list[float]]) -> list[PointStruct]:
        """Construye PointStruct list para upsert en Qdrant."""
        return [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "page_content": chunk.page_content,
                    "metadata": chunk.metadata,
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]

    @_ensure_initialized
    async def similarity_search(self, query: str, k: int = 10) -> list[Document]:
        """Busca documentos relevantes para una query."""
        try:
            results = await asyncio.to_thread(
                self._vector_store.similarity_search_with_score,
                query,
                k=k,
            )
            return [
                Document(
                    page_content=doc.page_content,
                    metadata={
                        "source": doc.metadata.get("source", ""),
                        "page": doc.metadata.get("page", 0),
                        "score": score,
                    },
                )
                for doc, score in results
            ]
        except Exception as e:
            logger.error(f"Error en similarity_search: {e}")
            raise

    async def health_check(self) -> bool:
        """Verifica que el servicio esté operativo."""
        try:
            if self._client is None:
                await self._initialize()
            await asyncio.to_thread(self._client.get_collections)
            return True
        except Exception:
            return False

    @_ensure_initialized
    async def clear_index(self) -> bool:
        """Elimina todos los vectores recreando la colección."""
        try:
            await asyncio.to_thread(
                self._client.recreate_collection,
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )

            self._vector_store = QdrantVectorStore(
                client=self._client,
                collection_name=COLLECTION_NAME,
                embedding=self._embeddings,
            )

            logger.info("Colección recreada exitosamente (datos limpiados)")
            return True
        except Exception as e:
            logger.error(f"Error limpiando colección: {e}")
            return False

    @_ensure_initialized
    async def get_stats(self) -> dict:
        """Obtiene estadisticas de la colección."""
        try:
            collection_info = await asyncio.to_thread(
                self._client.get_collection,
                collection_name=COLLECTION_NAME,
            )
            return {
                "total_vectors": collection_info.points_count,
                "dimension": EMBEDDING_DIMENSION,
            }
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {"error": str(e)}

    @_ensure_initialized
    async def get_indexed_documents(self) -> list[dict]:
        """Obtiene lista de documentos indexados con metadata básica.

        Returns:
            Lista de dicts con 'name' (source) y 'chunks' (count estimado).
        """
        try:
            records, _ = await asyncio.to_thread(
                self._client.scroll,
                collection_name=COLLECTION_NAME,
                limit=1000,
                with_payload=True,
            )

            source_counts: dict[str, int] = {}
            for record in records:
                if record.payload:
                    source = record.payload.get("metadata", {}).get("source", "unknown")
                    source_counts[source] = source_counts.get(source, 0) + 1

            documents = [
                {"name": source, "chunks": count}
                for source, count in source_counts.items()
            ]

            logger.debug(f"Found {len(documents)} indexed documents")
            return documents
        except Exception as e:
            logger.error(f"Error obteniendo documentos indexados: {e}")
            return []


@lru_cache
def get_rag_service() -> RAGService:
    """Retorna instancia singleton del RAGService."""
    return RAGService()
