"""Build the trip planner knowledge base: fetch -> chunk -> embed -> store.

Usage (from the repo root):
    uv run python scripts/build_kb.py                 # build, using cached raw data if present
    uv run python scripts/build_kb.py --refresh       # re-fetch from the NPS API
    uv run python scripts/build_kb.py --reset         # drop the collection first (e.g. after changing the embedding model)
    uv run python scripts/build_kb.py --query "easy sunrise hikes with kids"   # smoke test only
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from trip_planner.kb import store
from trip_planner.kb.chunking import chunk_documents
from trip_planner.kb.sources import nps


def print_results(results):
    for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
        print(f'[{dist:.3f}] {meta["park_name"]} ({meta["doc_type"]})')
        print(f'    {doc[:200].replace(chr(10), " ")}...')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--refresh', action='store_true', help='re-fetch raw data instead of using the cache')
    parser.add_argument('--reset', action='store_true', help='delete the collection before building')
    parser.add_argument('--query', help='run a test query against the existing collection and exit')
    parser.add_argument('-n', type=int, default=5, help='number of results for --query')
    args = parser.parse_args()

    if args.query:
        print_results(store.query(store.get_collection(), args.query, args.n))
        return

    if args.reset:
        store.reset_collection()

    docs = nps.load_documents(refresh=args.refresh)
    chunks = chunk_documents(docs)
    print(f'{len(docs)} documents -> {len(chunks)} chunks')

    collection = store.get_collection()
    store.upsert_chunks(collection, chunks)
    print(f'Collection "{collection.name}" now holds {collection.count()} chunks')


if __name__ == '__main__':
    main()
