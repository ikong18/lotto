"""Validated public fallbacks. Publish only rows agreed by two independent sites."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import re
import time

PH = timezone(timedelta(hours=8))
DAYS = {'ultra': {1,4,6}, 'grand': {0,2,5}, 'super': {1,3,6}, 'mega': {0,2,4}, 'lotto': {1,3,5}}
MONTHS = ('january february march april may june july august september october november december').split()

def fetch_text(url, attempts=2):
    for attempt in range(attempts):
        try:
            with urlopen(Request(url, headers={'User-Agent':'LottoTracker/1.1 (+https://github.com/ikong18/lotto)', 'Accept':'text/html'}), timeout=15) as response:
                body=response.read(2_000_001)
                if len(body)>2_000_000:raise ValueError('Response too large')
                return body.decode('utf-8-sig')
        except HTTPError as error:
            # A forbidden response is not a transient fault. Use another public source.
            if error.code not in (429,500,502,503,504) or attempt+1 == attempts: raise
        except (URLError, TimeoutError):
            if attempt+1 == attempts: raise
        time.sleep(attempt+1)
    raise RuntimeError('Fetch failed')

def urls_for(day):
    slug=f'{MONTHS[day.month-1]}-{day.day}-{day.year}'
    return (f'https://lottotayo.ph/results/{slug}',
            f'https://www.thesummitexpress.com/{day:%Y/%m}/pcso-lotto-result-today-{slug}.html')

def parse_fallback(html, day, provider, url):
    from update_results import Rows, parse_row
    parser=Rows();parser.feed(html); found={}
    def accept(cells):
        try: row=parse_row(cells,day)
        except (ValueError,IndexError):return
        if row is None or row['date'] != day.isoformat() or day.weekday() not in DAYS[row['game']]:return
        row['source']=url
        key=(row['date'],row['game'])
        if key in found and found[key] != row: found[key]=None
        elif key not in found: found[key]=row
    if provider==0:
        # The page date must match; numbers can be nested spans, never infer a date from the URL alone.
        heading=re.search(r'<h1\b[^>]*>(.*?)</h1>',html,re.I|re.S)
        if not heading:return []
        text=' '.join(re.sub(r'<[^>]*>',' ',heading[1]).split())
        if not re.search(rf'\b{MONTHS[day.month-1]}\s+0?{day.day},?\s+{day.year}\b',text,re.I):return []
        for cells in parser.rows:
            if len(cells)!=4:continue
            digits=re.findall(r'\d+',cells[1])
            if len(digits)==1 and len(digits[0])==12:digits=[digits[0][i:i+2] for i in range(0,12,2)]
            winner=re.match(r'^\s*(\d[\d,]*)\b',cells[3])
            if len(digits)!=6 or not winner:continue
            accept([cells[0],'-'.join(digits),day.strftime('%m/%d/%Y'),cells[2],winner[1]])
    else:
        group=None; values={}
        def finish():
            if group and all(k in values for k in ('numbers','jackpot','winners')):
                accept([group,'-'.join(re.findall(r'\d+',values['numbers'])),day.strftime('%m/%d/%Y'),values['jackpot'],values['winners']])
        for cells in parser.rows:
            if len(cells)!=2:continue
            if re.search(r'6/(58|55|49|45|42)\b',cells[0]):
                finish();group=None;values={}
                try:header_date=datetime.strptime(cells[1],'%B %d, %Y').date()
                except ValueError:continue
                if header_date==day:group=cells[0]
            elif group:
                labels={'winning numbers':'numbers','winning combination':'numbers','jackpot prize':'jackpot','jackpot winner(s)':'winners'}
                k=labels.get(cells[0].lower())
                if k:values[k]=cells[1]
        finish()
    return [row for row in found.values() if row]

def same_result(a,b):
    return (sorted(a['numbers'])==sorted(b['numbers']) and a.get('winners')==b.get('winners') and
            abs(Decimal(str(a.get('jackpot',0)))-Decimal(str(b.get('jackpot',0))))<=Decimal('0.005'))

def corroborate(first,second):
    a={(r['date'],r['game']):r for r in first};b={(r['date'],r['game']):r for r in second};verified=[];conflicts=[]
    for key in sorted(a.keys() & b.keys()):
        if not same_result(a[key],b[key]):conflicts.append('|'.join(key));continue
        verified.append({**a[key], 'verifiedSources':[a[key]['source'],b[key]['source']], 'verification':'two-source agreement'})
    return verified,conflicts

def expected_draws(now,days=7):
    local=now.astimezone(PH)
    # Give publishers time after 9 PM. Do not call a 9:20 PM run stale while publication is pending.
    end=local.date() if (local.hour,local.minute)>=(21,45) else local.date()-timedelta(days=1)
    return {(str(day),g) for i in range(days) for day in [end-timedelta(days=i)] for g,weekdays in DAYS.items() if day.weekday() in weekdays}

def fallback_results(dates,fetch=fetch_text):
    jobs=[(day,i,url) for day in sorted(dates) for i,url in enumerate(urls_for(day))]
    def read(job):
        day,i,url=job
        try:return day,i,parse_fallback(fetch(url),day,i,url),None
        except Exception as error:return day,i,[],f'{url}: {type(error).__name__}'
    pages={};errors=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for day,i,rows,error in pool.map(read,jobs):
            pages[day,i]=rows
            if error:errors.append(error)
    verified=[];conflicts=[]
    for day in sorted(dates):
        rows,bad=corroborate(pages.get((day,0),[]),pages.get((day,1),[]));verified+=rows;conflicts+=bad
    return verified,conflicts,errors
