"""Upsert results.json draws into the Supabase `draws` table (idempotent).

Runs in the update workflow with a service-role key kept in GitHub Secrets:
  SUPABASE_URL                 e.g. https://<project>.supabase.co
  SUPABASE_SERVICE_ROLE_KEY    never put this in config.js or any browser file

Without both variables it exits quietly, so forks and local runs are unaffected.
`notified` is not sent: it keeps its database value (default false).
"""
import argparse
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BATCH = 500
FIELDS = ('date', 'game', 'numbers', 'jackpot', 'winners', 'prizes')


def build_rows(document):
    """One uniform-key row per draw, as PostgREST bulk upserts require."""
    rows = {}
    for draw in document.get('draws', []):
        row = {field: draw.get(field) for field in FIELDS}
        rows[(row['date'], row['game'])] = row
    return [rows[key] for key in sorted(rows)]


def upsert(url, key, rows, opener=urlopen):
    endpoint = url.rstrip('/') + '/rest/v1/draws?on_conflict=date,game'
    headers = {'apikey': key, 'Authorization': 'Bearer ' + key,
               'Content-Type': 'application/json',
               'Prefer': 'resolution=merge-duplicates,return=minimal'}
    for start in range(0, len(rows), BATCH):
        body = json.dumps(rows[start:start + BATCH]).encode()
        try:
            with opener(Request(endpoint, data=body, headers=headers, method='POST'), timeout=30) as response:
                response.read()
        except HTTPError as error:  # never echo headers: they carry the key
            raise RuntimeError(f'Supabase rejected the upsert: HTTP {error.code} {error.read()[:300].decode("utf-8", "replace")}') from None
        except URLError as error:
            raise RuntimeError(f'Supabase unreachable: {error.reason}') from None
    return len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=Path('results.json'))
    args = parser.parse_args()
    url, key = os.environ.get('SUPABASE_URL', ''), os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
    if not url or not key:
        print('Supabase sync skipped: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set')
        return 0
    if not url.startswith('https://'):
        print('SUPABASE_URL must start with https://', file=sys.stderr)
        return 1
    rows = build_rows(json.loads(args.input.read_text()))
    if not rows:
        print('No draws to sync')
        return 0
    try:
        print(f'Synced {upsert(url, key, rows)} draws to Supabase')
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
