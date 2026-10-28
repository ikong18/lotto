"""Import validated major-game results from PCSO; preserve historical metadata."""
import argparse
from datetime import date, datetime, timezone
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen

SOURCE = 'https://www.pcso.gov.ph/SearchLottoResult.aspx'
GAMES = {'6/58': ('ultra', 58), '6/55': ('grand', 55), '6/49': ('super', 49),
         '6/45': ('mega', 45), '6/42': ('lotto', 42)}

class Rows(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows = []; self.row = None; self.cell = None
    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self.row = []
        elif tag in ('td', 'th') and self.row is not None: self.cell = []
    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)
    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split())); self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.rows.append(self.row); self.row = None

def parse_results(html, today=None):
    parser = Rows(); parser.feed(html); draws = {}
    for cells in parser.rows:
        if len(cells) != 5: continue
        match = re.search(r'6/(58|55|49|45|42)\b', cells[0])
        if not match: continue
        game, maximum = GAMES[match[0]]
        numbers = [int(n) for n in re.split(r'\s*[-–]\s*', cells[1])]
        day = datetime.strptime(cells[2], '%m/%d/%Y').date()
        jackpot = float(cells[3].replace(',', '').replace('₱', '').strip())
        winners = int(cells[4].replace(',', ''))
        if (len(numbers) != 6 or len(set(numbers)) != 6 or
            any(n < 1 or n > maximum for n in numbers) or
            not math.isfinite(jackpot) or jackpot < 0 or winners < 0 or
            day > (today or date.today())):
            raise ValueError(f'Invalid PCSO row: {game} {day}')
        row = dict(date=day.isoformat(), game=game, numbers=numbers,
                   jackpot=jackpot, winners=winners, source=SOURCE)
        key = (row['date'], game)
        if key in draws and draws[key] != row: raise ValueError('Conflicting PCSO rows')
        draws[key] = row
    if not draws: raise ValueError('No major-game results found; refusing to overwrite data')
    return list(draws.values())

def merge_results(document, incoming):
    rows = {(d['date'], d['game']): dict(d) for d in document['draws']}
    for draw in incoming:
        key = (draw['date'], draw['game'])
        rows[key] = {**rows.get(key, {}), **draw}
    merged = {**document, 'draws': sorted(rows.values(), key=lambda d: (d['date'], d['game']))}
    return merged

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--html', type=Path)
    ap.add_argument('--output', type=Path, default=Path('results.json')); args = ap.parse_args()
    if args.html: html = args.html.read_text()
    else:
        for attempt in range(3):
            try:
                with urlopen(Request(SOURCE, headers={'User-Agent': 'LottoTracker/1.0 results checker'}), timeout=30) as r:
                    html = r.read().decode('utf-8-sig')
                break
            except Exception:
                if attempt == 2: raise
                time.sleep(2 ** attempt)
    incoming = parse_results(html)
    old = json.loads(args.output.read_text())
    merged = merge_results(old, incoming)
    if merged != old:
        merged['updatedAt'] = datetime.now(timezone.utc).isoformat()
        tmp = args.output.with_suffix('.tmp'); tmp.write_text(json.dumps(merged, indent=2) + '\n')
        tmp.replace(args.output)
    print(f"Checked {len(incoming)} PCSO rows; latest draw {max(d['date'] for d in incoming)}")

if __name__ == '__main__': main()
