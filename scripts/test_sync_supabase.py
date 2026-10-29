import json
import unittest
from urllib.error import HTTPError
from sync_supabase import build_rows, upsert

DOC = {'draws': [
    {'date': '2026-10-27', 'game': 'ultra', 'numbers': [1, 2, 3, 4, 5, 6], 'jackpot': 5.0, 'winners': 0,
     'source': 'x', 'notified': True},
    {'date': '2026-10-26', 'game': 'grand', 'numbers': [6, 5, 4, 3, 2, 1]},
]}

class Recorder:
    def __init__(self): self.calls = []
    def __call__(self, request, timeout=0):
        self.calls.append(request); return self
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self): return b''

class SyncTests(unittest.TestCase):
    def test_rows_are_uniform_sorted_and_omit_notified_and_source(self):
        rows = build_rows(DOC)
        self.assertEqual([r['game'] for r in rows], ['grand', 'ultra'])
        self.assertEqual({tuple(r) for r in rows}, {('date', 'game', 'numbers', 'jackpot', 'winners', 'prizes')})
        self.assertIsNone(rows[0]['jackpot'])
    def test_upsert_batches_and_sends_merge_headers(self):
        rec = Recorder(); rows = [{'date': f'2026-01-{i % 28 + 1:02d}', 'game': 'ultra'} for i in range(1200)]
        self.assertEqual(upsert('https://p.supabase.co/', 'k', rows, opener=rec), 1200)
        self.assertEqual(len(rec.calls), 3)
        first = rec.calls[0]
        self.assertTrue(first.full_url.endswith('/rest/v1/draws?on_conflict=date,game'))
        self.assertIn('merge-duplicates', first.get_header('Prefer'))
        self.assertEqual(len(json.loads(first.data)), 500)
    def test_http_error_is_reported_without_the_key(self):
        def boom(request, timeout=0):
            raise HTTPError(request.full_url, 401, 'nope', {}, __import__('io').BytesIO(b'{"message":"bad jwt"}'))
        with self.assertRaises(RuntimeError) as ctx:
            upsert('https://p.supabase.co', 'SECRETKEY', [{'a': 1}], opener=boom)
        self.assertIn('401', str(ctx.exception)); self.assertNotIn('SECRETKEY', str(ctx.exception))
if __name__ == '__main__': unittest.main()
