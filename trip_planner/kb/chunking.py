from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)


def chunk_document(doc):
    """Split a document into chunks. Short documents stay as a single chunk.

    Each chunk is prefixed with the park name so it is self-describing when retrieved on its own.
    """
    prefix = f'{doc["metadata"]["park_name"]}: '
    pieces = _splitter.split_text(doc['text'])
    return [
        {
            'id': f'{doc["id"]}#{i}',
            'text': prefix + piece,
            'metadata': {**doc['metadata'], 'chunk': i},
        }
        for i, piece in enumerate(pieces)
    ]


def chunk_documents(docs):
    return [chunk for doc in docs for chunk in chunk_document(doc)]
