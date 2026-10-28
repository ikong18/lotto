from datetime import datetime, timedelta
import json
from pathlib import Path
from random import Random
import tempfile
import unittest
from weekly_plan import create_plan, ensure_plan, week_start, PH, GAMES

class PlanTests(unittest.TestCase):
    def test_full_week_budget_distribution_and_slots(self):
        for seed in range(100):
            now=datetime(2026,11,2,7,tzinfo=PH);p=create_plan(now,rng=Random(seed))
            self.assertEqual(p['totalCost'],300);self.assertEqual(len(p['lines']),12)
            counts={g:sum(x['game']==g for x in p['lines']) for g in GAMES}
            self.assertEqual(sorted(counts.values()),[2,2,2,3,3])
            self.assertEqual(len({x['id'] for x in p['lines']}),12)
            for x in p['lines']:
                self.assertEqual(len(set(x['numbers'])),6)
                self.assertTrue(all(1<=n<=GAMES[x['game']][0] for n in x['numbers']))
                self.assertIn(datetime.fromisoformat(x['drawAt']).weekday(),GAMES[x['game']][1])
                self.assertGreater(datetime.fromisoformat(x['betAt']),now)
                self.assertEqual(datetime.fromisoformat(x['drawAt']).hour,21)
    def test_partial_week_no_catchup(self):
        p=create_plan(datetime(2026,10,28,15,tzinfo=PH),rng=Random(0))
        self.assertEqual(len(p['lines']),10);self.assertEqual(p['totalCost'],250)
        p=create_plan(datetime(2026,11,1,20,tzinfo=PH));self.assertEqual(p['lines'],[])
    def test_persistence_rollover_and_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'sets.json').write_text('{"costPerPlay":25}')
            t=datetime(2026,11,2,7,tzinfo=PH)
            one,changed=ensure_plan(root,t);self.assertTrue(changed)
            two,changed=ensure_plan(root,t+timedelta(days=2));self.assertFalse(changed);self.assertEqual(one,two)
            (root/'weekly-plan.json').unlink();recovered,_=ensure_plan(root,t+timedelta(days=2));self.assertEqual(one,recovered)
            following,_=ensure_plan(root,t+timedelta(days=7));self.assertNotEqual(one['weekStart'],following['weekStart'])
    def test_timezone_and_cost_limits(self):
        self.assertEqual(str(week_start(datetime.fromisoformat('2026-11-01T16:00:00+00:00'))),'2026-11-02')
        self.assertLessEqual(create_plan(datetime(2026,11,2,7,tzinfo=PH),cost=30)['totalCost'],300)
        for cost in [0,-1,float('inf'),float('nan'),301]:
            with self.assertRaises((ValueError,OverflowError)):create_plan(datetime(2026,11,2,tzinfo=PH),cost=cost)
        with self.assertRaises(ValueError):create_plan(datetime(2026,11,2,tzinfo=PH),budget=500)
if __name__=='__main__':unittest.main()
