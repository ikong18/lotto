"""Generate one immutable, uniformly sampled weekly plan. Never places bets."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from secrets import SystemRandom

PH = timezone(timedelta(hours=8))
GAMES = {'ultra': (58, {1, 4, 6}), 'grand': (55, {0, 2, 5}),
         'super': (49, {1, 3, 6}), 'mega': (45, {0, 2, 4}),
         'lotto': (42, {1, 3, 5})}  # Python weekdays: Monday = 0

def week_start(now):
    local = now.astimezone(PH)
    return local.date() - timedelta(days=local.weekday())

def create_plan(now, cost=25, budget=300, rng=None):
    if now.tzinfo is None: raise ValueError('Timezone-aware timestamp required')
    if not isinstance(cost, (int, float)) or not 0 < cost <= budget or round(cost * 100) != cost * 100:
        raise ValueError('Invalid ordinary-line cost')
    if not 0 <= budget <= 300: raise ValueError('Weekly cap cannot exceed PHP 300')
    rng = rng or SystemRandom()
    start = week_start(now); capacity = min(12, int(round(budget * 100)) // int(round(cost * 100)))
    slots = {}
    for game, (_, weekdays) in GAMES.items():
        slots[game] = []
        for i in range(7):
            day = start + timedelta(days=i)
            bet_at = datetime(day.year, day.month, day.day, 19, tzinfo=PH)
            if day.weekday() in weekdays and bet_at > now:
                slots[game].append((bet_at, bet_at + timedelta(hours=2)))
        rng.shuffle(slots[game])
    # Equal allocation rounds; secure random order removes a preferred category for leftover slots.
    chosen = []
    for depth in range(3):
        order = list(GAMES); rng.shuffle(order)
        for game in order:
            if len(chosen) >= capacity: break
            if len(slots[game]) > depth: chosen.append((game, *slots[game][depth]))
    chosen.sort(key=lambda x: (x[1], x[0]))
    lines = []
    for index, (game, bet_at, draw_at) in enumerate(chosen):
        numbers = sorted(rng.sample(range(1, GAMES[game][0] + 1), 6))
        lines.append({'id': f'{start.isoformat()}-{game}-{draw_at.date().isoformat()}',
                      'game': game, 'numbers': numbers, 'cost': cost,
                      'betAt': bet_at.isoformat(), 'drawAt': draw_at.isoformat(),
                      'remindAt': (bet_at - timedelta(minutes=30)).isoformat()})
    return {'version': 1, 'weekStart': start.isoformat(),
            'weekEnd': (start + timedelta(days=6)).isoformat(),
            'generatedAt': now.astimezone(PH).isoformat(), 'budget': budget, 'unitCost': cost,
            'method': 'OS-backed uniform sampling without replacement; no history or personal weighting',
            'totalCost': round(sum(x['cost'] for x in lines), 2), 'lines': lines}

def ensure_plan(root, now):
    path = root / 'weekly-plan.json'; week = week_start(now).isoformat()
    if path.exists():
        current = json.loads(path.read_text())
        if current['weekStart'] == week: return current, False
    archive = root / 'plans' / f'{week}.json'
    if archive.exists(): plan = json.loads(archive.read_text())
    else:
        settings = json.loads((root / 'sets.json').read_text())
        plan = create_plan(now, cost=settings['costPerPlay'])
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_text(json.dumps(plan, indent=2) + '\n')
    temp = path.with_suffix('.tmp');temp.write_text(json.dumps(plan, indent=2) + '\n');temp.replace(path)
    return plan, True

if __name__ == '__main__':
    ap = argparse.ArgumentParser();ap.add_argument('--root', type=Path, default=Path('.'));args=ap.parse_args()
    plan, changed = ensure_plan(args.root, datetime.now(PH))
    print(f"Weekly plan {plan['weekStart']}: {len(plan['lines'])} lines, PHP {plan['totalCost']} / {plan['budget']}; changed={changed}")
