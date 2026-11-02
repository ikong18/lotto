"""Import validated major-game results from PCSO; preserve historical metadata."""
import argparse
from datetime import date, datetime
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re

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
            self.row.append(' '.join(' '.join(self.cell).split())); self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.rows.append(self.row); self.row = None

def parse_row(cells, today):
    """Parse one 5-cell PCSO table row; return None for non-major games."""
    match = re.search(r'6/(58|55|49|45|42)\b', cells[0])
    if not match: return None
    game, maximum = GAMES[match[0]]
    numbers = [int(n) for n in re.split(r'\s*[-–]\s*', cells[1])]
    day = datetime.strptime(cells[2], '%m/%d/%Y').date()
    jackpot = float(cells[3].replace(',', '').replace('₱', '').strip())
    winners = int(cells[4].replace(',', ''))
    if (len(numbers) != 6 or len(set(numbers)) != 6 or
        any(n < 1 or n > maximum for n in numbers) or
        not math.isfinite(jackpot) or jackpot < 0 or winners < 0 or day > today):
        raise ValueError(f'Invalid PCSO row: {game} {day}')
    return dict(date=day.isoformat(), game=game, numbers=numbers,
                jackpot=jackpot, winners=winners, source=SOURCE)

def parse_results(html, today=None, skipped=None):
    """Return every valid major-game row. A malformed row is skipped (and recorded in
    `skipped`) instead of aborting the whole import; no valid rows at all still fails."""
    today = today or date.today()
    parser = Rows(); parser.feed(html); draws = {}; conflicts=set()
    skipped = skipped if skipped is not None else []
    for cells in parser.rows:
        if len(cells) != 5: continue
        try:
            row = parse_row(cells, today)
        except (ValueError, IndexError) as error:
            skipped.append(f'{cells[0]} | {cells[2]}: {error}'); continue
        if row is None: continue
        key = (row['date'], row['game'])
        if key in conflicts: continue
        if key in draws and {**draws[key], 'numbers': sorted(draws[key]['numbers'])} != {**row, 'numbers': sorted(row['numbers'])}:
            skipped.append(f'{row["game"]} {row["date"]}: conflicting rows quarantined');conflicts.add(key);draws.pop(key);continue
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

def collect_results(old, now, fetch=None, force_fallback=False):
    from result_sources import fetch_text, expected_draws, fallback_results, same_result
    fetch=fetch or fetch_text; notes=[]; primary=[]
    if not force_fallback:
        try: primary=parse_results(fetch(SOURCE),today=now.date(),skipped=notes)
        except Exception as error: notes.append('PCSO unavailable: '+type(error).__name__+(' '+str(error.code) if hasattr(error,'code') else ''))
    existing={(r['date'],r['game']):r for r in old['draws']}
    official={(r['date'],r['game']):r for r in primary}
    expected=expected_draws(now)
    missing=expected-(existing.keys()|official.keys())
    dates={datetime.fromisoformat(k[0]).date() for k in missing}
    if not primary:
        # Recheck the latest scheduled date for each game, even when no rows are missing.
        dates.update(datetime.fromisoformat(max(day for day,g in expected if g==game)).date() for game in {g for _,g in expected})
    fallback,conflicts,errors=fallback_results(dates,fetch=fetch) if dates else ([],[],[])
    notes+=errors
    incoming=list(primary)
    for row in fallback:
        k=(row['date'],row['game'])
        if k in official:continue
        if k in existing:
            if not same_result(existing[k],row):conflicts.append('|'.join(k))
            continue  # Never downgrade an existing official/provenanced record to a mirror.
        incoming.append(row)
    merged=merge_results(old,incoming)
    remaining=sorted(expected-{(r['date'],r['game']) for r in merged['draws']})
    healthy=not remaining and not conflicts and bool(primary or fallback)
    health={'checkedAt':now.isoformat(), 'status':'ok' if healthy else 'degraded',
            'mode':'official' if primary else 'cross-checked fallback' if fallback else 'unavailable',
            'missingDraws':[{'date':d,'game':g} for d,g in remaining],
            'conflicts':sorted(set(conflicts)), 'notes':notes,
            'latestByGame':{g:max((r['date'] for r in merged['draws'] if r['game']==g),default=None) for g,_ in GAMES.values()}}
    return merged,health

def atomic_json(path, value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)

def main():
    from result_sources import PH
    ap=argparse.ArgumentParser();ap.add_argument('--html',type=Path)
    ap.add_argument('--output',type=Path,default=Path('results.json'))
    ap.add_argument('--status',type=Path,default=Path('update-status.json'))
    ap.add_argument('--force-fallback',action='store_true',help='Test public-source agreement without contacting PCSO')
    ap.add_argument('--dry-run',action='store_true');args=ap.parse_args()
    old=json.loads(args.output.read_text());now=datetime.now(PH)
    if args.html:
        notes=[];incoming=parse_results(args.html.read_text(),today=now.date(),skipped=notes)
        merged=merge_results(old,incoming);health=None
    else:merged,health=collect_results(old,now,force_fallback=args.force_fallback)
    if merged!=old:merged['updatedAt']=now.isoformat()
    if not args.dry_run:
        if merged!=old:atomic_json(args.output,merged)
        if health:atomic_json(args.status,health)
    print(f"Draws retained: {len(merged['draws'])}; latest {max(d['date'] for d in merged['draws'])}")
    if health:
        print(json.dumps(health,indent=2))
        if health['status']!='ok':raise SystemExit(1)

if __name__=='__main__':main()
