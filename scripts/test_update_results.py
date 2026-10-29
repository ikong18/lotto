import copy
from datetime import date
import unittest
from update_results import parse_results, merge_results

HTML = '''<table><tr><th>LOTTO GAME</th><th>COMBINATIONS</th><th>DRAW DATE</th><th>JACKPOT (PHP)</th><th>WINNERS</th></tr>
<tr><td>Ultra Lotto 6/58</td><td>55-12-48-22-38-40</td><td>10/27/2026</td><td>449,844,291.78</td><td>0</td></tr>
<tr><td>Superlotto 6/49</td><td>04-03-22-37-17-24</td><td>10/27/2026</td><td>70,236,247.62</td><td>0</td></tr>
<tr><td>3D Lotto 9PM</td><td>8-3-8</td><td>10/27/2026</td><td>4,500</td><td>145</td></tr></table>'''
class ImporterTests(unittest.TestCase):
    def parse(self, html=HTML): return parse_results(html, date(2026,10,28))
    def test_official_table_and_digit_game_exclusion(self):
        rows=self.parse();self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['numbers'],[55,12,48,22,38,40])
        self.assertEqual(rows[1]['game'],'super')
        self.assertEqual(rows[0]['jackpot'],449844291.78)
    def test_invalid_page_and_all_bad_rows_fail(self):
        for html in ['<html>Unavailable</html>',HTML.replace('10/27/2026','10/27/2027')]:
            with self.assertRaises(ValueError):self.parse(html)
    def test_one_bad_row_is_skipped_not_fatal(self):
        for bad in ['55-55-48','59-12-48']:
            skipped=[];rows=parse_results(HTML.replace('55-12-48',bad),date(2026,10,28),skipped)
            self.assertEqual([r['game'] for r in rows],['super']);self.assertEqual(len(skipped),1)
        skipped=[];rows=parse_results(HTML.replace('449,844,291.78','n/a'),date(2026,10,28),skipped)
        self.assertEqual(len(rows),1);self.assertEqual(len(skipped),1)
    def test_conflicting_duplicate_keeps_first(self):
        dup=HTML.replace('</table>','<tr><td>Ultra Lotto 6/58</td><td>01-02-03-04-05-06</td><td>10/27/2026</td><td>1</td><td>0</td></tr></table>')
        skipped=[];rows=parse_results(dup,date(2026,10,28),skipped)
        ultra=[r for r in rows if r['game']=='ultra'];self.assertEqual(len(ultra),1)
        self.assertEqual(ultra[0]['numbers'],[55,12,48,22,38,40]);self.assertEqual(len(skipped),1)
    def test_merge_preserves_history_prizes_and_notification(self):
        incoming=self.parse();old={'draws':[{**incoming[0],'notified':True,'prizes':{'3':[12,100]}},{'date':'2026-01-01','game':'lotto','numbers':[1,2,3,4,5,6]}]}
        original=copy.deepcopy(old);result=merge_results(old,incoming)
        self.assertEqual(old,original);self.assertEqual(len(result['draws']),3)
        ultra=next(d for d in result['draws'] if d['game']=='ultra')
        self.assertTrue(ultra['notified']);self.assertEqual(ultra['prizes'],{'3':[12,100]})
        self.assertEqual(merge_results(result,incoming),result)
if __name__=='__main__':unittest.main()
