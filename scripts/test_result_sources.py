from datetime import date,datetime
from pathlib import Path
import copy
import json
from urllib.error import HTTPError
import unittest
from result_sources import parse_fallback,corroborate,urls_for,expected_draws,PH
from update_results import collect_results,SOURCE

DAY=date(2026,11,1)
TAYO='''<h1>Lotto results for Sunday, November 1, 2026</h1><table>
<tr><td>Ultra Lotto 6/58</td><td><span>14</span><span>34</span><span>54</span><span>18</span><span>05</span><span>46</span></td><td>₱468,922,422.10</td><td>0 · rolls over</td></tr>
<tr><td>Super Lotto 6/49</td><td>44 16 40 19 27 32</td><td>₱78,612,615.50</td><td>0</td></tr></table>'''
SUMMIT='''<table><tr><th>Ultra Lotto 6/58</th><th>November 1, 2026</th></tr>
<tr><td>Winning Numbers</td><td>14-34-54-18-05-46</td></tr><tr><td>Jackpot Prize</td><td>₱468,922,422.10</td></tr><tr><td>Jackpot Winner(s)</td><td>0</td></tr></table>
<table><tr><th>Super Lotto 6/49</th><th>November 1, 2026</th></tr><tr><td>Winning Numbers</td><td>44-16-40-19-27-32</td></tr><tr><td>Jackpot Prize</td><td>₱78,612,615.50</td></tr><tr><td>Jackpot Winner(s)</td><td>0</td></tr></table>'''
class SourceTests(unittest.TestCase):
    def parse(self,html,provider):return parse_fallback(html,DAY,provider,urls_for(DAY)[provider])
    def test_nested_numbers_and_agreement(self):
        a=self.parse(TAYO,0);b=self.parse(SUMMIT,1);rows,conflicts=corroborate(a,b)
        self.assertEqual(len(rows),2);self.assertEqual(conflicts,[])
        self.assertEqual(rows[0]['numbers'],[44,16,40,19,27,32])
        self.assertEqual(len(rows[0]['verifiedSources']),2)
    def test_wrong_date_placeholder_and_invalid_numbers(self):
        self.assertEqual(self.parse(TAYO.replace('Sunday, November 1','Saturday, October 31')+'<a>November 1, 2026</a>',0),[])
        self.assertEqual(self.parse(SUMMIT.replace('November 1','October 31'),1),[])
        self.assertEqual(len(self.parse(TAYO.replace('44 16 40 19 27 32','9:00 PM'),0)),1)
        self.assertEqual(len(self.parse(SUMMIT.replace('14-34-54','14-14-54'),1)),1)
    def test_disagreement_is_not_published(self):
        rows,conflicts=corroborate(self.parse(TAYO,0),self.parse(SUMMIT.replace('14-34-54','14-35-54'),1))
        self.assertEqual([r['game'] for r in rows],['super']);self.assertEqual(len(conflicts),1)
    def test_publisher_grace_period(self):
        early=expected_draws(datetime(2026,11,2,21,20,tzinfo=PH))
        late=expected_draws(datetime(2026,11,2,21,45,tzinfo=PH))
        self.assertNotIn(('2026-11-02','grand'),early);self.assertIn(('2026-11-02','grand'),late)
    def test_403_uses_verified_fallback_and_keeps_existing_history(self):
        old=json.loads((Path(__file__).parent.parent/'results.json').read_text())
        old['draws']=[r for r in old['draws'] if (r['date'],r['game'])!=('2026-11-01','ultra')]
        before=copy.deepcopy(old)
        def fetch(url):
            if url==urls_for(DAY)[0]:return TAYO
            if url==urls_for(DAY)[1]:return SUMMIT
            raise HTTPError(url,403,'Forbidden',{},None)
        updated,health=collect_results(old,datetime(2026,11,2,8,tzinfo=PH),fetch=fetch)
        self.assertEqual(old,before);self.assertEqual(len(updated['draws']),len(old['draws'])+1)
        self.assertEqual(health['status'],'ok');self.assertEqual(health['mode'],'cross-checked fallback')
        for row in before['draws']:self.assertIn(row,updated['draws'])
    def test_total_outage_preserves_history_and_reports_failure(self):
        old=json.loads((Path(__file__).parent.parent/'results.json').read_text())
        def fetch(url):raise HTTPError(url,403,'Forbidden',{},None)
        updated,health=collect_results(old,datetime(2026,11,2,8,tzinfo=PH),fetch=fetch)
        self.assertEqual(updated,old);self.assertEqual(health['status'],'degraded')
if __name__=='__main__':unittest.main()
