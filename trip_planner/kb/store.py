import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from trip_planner.kb import CHROMA_DIR

EMBEDDING_MODEL = 'BAAI/bge-small-en-v1.5'
# EMBEDDING_MODEL = 'text-embedding-3-small'
COLLECTION_NAME = 'trip_kb'
BATCH_SIZE = 128


def get_collection(path=CHROMA_DIR, model=EMBEDDING_MODEL):
    """Open (or create) the persistent collection. Shared by the build script and the notebook."""
    client = chromadb.PersistentClient(path=str(path))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=SentenceTransformerEmbeddingFunction(model_name=model),
        metadata={'embedding_model': model, 'hnsw:space': 'cosine'},
    )
    stored_model = collection.metadata.get('embedding_model')
    if stored_model != model:
        raise RuntimeError(
            f'Collection was built with {stored_model}, not {model}. Rebuild with --reset.'
        )
    return collection


def reset_collection(path=CHROMA_DIR):
    client = chromadb.PersistentClient(path=str(path))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # nothing to delete


def upsert_chunks(collection, chunks):
    """Idempotent: chunk IDs are deterministic, so re-runs overwrite rather than duplicate."""
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        collection.upsert(
            ids=[c['id'] for c in batch],
            documents=[c['text'] for c in batch],
            metadatas=[c['metadata'] for c in batch],
        )


def query(collection, text, n_results=5, where=None):
    return collection.query(query_texts=[text], n_results=n_results, where=where)
