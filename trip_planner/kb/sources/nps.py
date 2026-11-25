"""Fetch National Park Service data (https://www.nps.gov/subjects/developer/api-documentation.htm)."""
import json
import os
import time

import requests

from trip_planner.kb import RAW_DIR

BASE_URL = 'https://developer.nps.gov/api/v1'
PAGE_SIZE = 50

# Endpoints available to fetch. Only 'parks' is wired into the pipeline so far.
ENDPOINTS = ['parks', 'thingstodo', 'places', 'campgrounds']


def _get_page(endpoint, api_key, start):
    resp = requests.get(
        f'{BASE_URL}/{endpoint}',
        params={'limit': PAGE_SIZE, 'start': start},
        headers={'X-Api-Key': api_key},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_endpoint(endpoint, refresh=False):
    """Return all records for an endpoint, using the cached JSON in data/raw/ unless refresh is set."""
    cache_path = RAW_DIR / 'nps' / f'{endpoint}.json'
    if cache_path.exists() and not refresh:
        return json.loads(cache_path.read_text())

    api_key = os.getenv('NPS_API_KEY')
    if not api_key:
        raise RuntimeError('NPS_API_KEY is not set (get a free key at developer.nps.gov)')

    records, start = [], 0
    while True:
        page = _get_page(endpoint, api_key, start)
        records.extend(page['data'])
        start += PAGE_SIZE
        if start >= int(page['total']):
            break
        time.sleep(0.2)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(records, indent=2))
    return records


def park_to_document(park):
    """Normalize a /parks record to {id, text, metadata}."""
    activities = [a['name'] for a in park.get('activities', [])]
    topics = [t['name'] for t in park.get('topics', [])]
    parts = [
        f'{park["fullName"]} ({park["designation"]}) in {park["states"]}.',
        park.get('description', ''),
        f'Weather: {park["weatherInfo"]}' if park.get('weatherInfo') else '',
        f'Directions: {park["directionsInfo"]}' if park.get('directionsInfo') else '',
        f'Activities: {", ".join(activities)}.' if activities else '',
        f'Topics: {", ".join(topics)}.' if topics else '',
    ]
    return {
        'id': f'nps-park-{park["parkCode"]}',
        'text': '\n'.join(p.strip() for p in parts if p and p.strip()),
        'metadata': {
            'source': 'nps',
            'doc_type': 'park',
            'park_code': park['parkCode'],
            'park_name': park['fullName'],
            'states': park['states'],
            'designation': park['designation'],
            'activities': '|'.join(activities),
            'source_url': park.get('url', ''),
        },
    }


def load_documents(refresh=False):
    return [park_to_document(p) for p in fetch_endpoint('parks', refresh)]
