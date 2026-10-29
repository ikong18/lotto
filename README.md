# Lotto Tracker

A static, personal tracker for five PCSO major games: 6/58, 6/55, 6/49, 6/45 and 6/42.

- Results and history use `results.json`, updated from the official PCSO results table by GitHub Actions. Open tabs check the committed feed every five minutes.
- Upcoming Picks shows repeatable combinations, the next scheduled draw in Philippine time, and clearly labeled prize estimates.
- Settings edits all five games. Fill the blank six-number row to add a set; clear all numbers in a row to remove it. Changes save in this browser.
- Overview backtests your current sets against recorded history; it does not represent actual bets.
- Budget compares mathematical odds and estimated returns. No number selection method predicts an independent draw.

## Run locally

Run `python -m http.server 8000` in this directory and open http://localhost:8000. Run regression checks with `node tests.cjs` and `python -m unittest discover -s scripts -p 'test_*.py'`. No build or package installation is required.

## GitHub Pages

In repository Settings > Pages, deploy the `main` branch root. The **Update lotto results** Action checks PCSO daily at 9:20, 10:20 and 11:20 PM, plus 7:20 AM Philippine time. Scheduled Actions may run late. Use Actions > Update lotto results > Run workflow for an immediate retry. It imports the recent rows PCSO exposes, preserves history, and fails without changing data if the source is unavailable or malformed. It does not backfill older missing dates beyond the source table. No API key is required. The workflow needs Contents write permission. Branch protection may require an exception for the updater.

On GitHub Pages, the app reads the committed `main/results.json` feed directly, so bot commits do not depend on another Pages deployment. Cloud records are merged with the repository feed, with repository records taking precedence on matching dates. A network failure during a background refresh leaves the last successful results visible.

Manual update from the page: the Results tab has **Refresh now** (reloads `results.json` and the weekly plan immediately) and **Run updater**. Without a token, Run updater opens the Actions page so you can press Run workflow. If you save a fine-grained GitHub token under Settings (this repository only, Actions: read and write only, short expiry), the button starts the workflow itself, follows the run, and reloads the results when it finishes. The token stays in this browser's storage and is only sent to api.github.com. The browser cannot read PCSO directly (no CORS), so the Action does the fetching.

You can also update `results.json` manually with verified results. Each draw requires `date` (YYYY-MM-DD), `game` (ultra, grand, super, mega or lotto), and six unique in-range `numbers`. Optional fields are `jackpot`, `winners`, and `prizes` (for example, `"5": [winnerCount, payoutPerWinner]`).

## Optional cloud and email integrations

`config.js` accepts only the public HTTPS Supabase project URL and a public anon/publishable key. Never put a database password or service key in browser files. The previously committed database password must be rotated in Supabase; removing it from the latest file does not remove it from Git history.

Cloud tables: `supabase/schema.sql` is a reference schema for `draws`, `app_state` and `bets` with row-level security (public read of draws, owner-only writes). Replace `OWNER_EMAIL_HERE`, compare it with any existing tables, then run it in the Supabase SQL editor. Local tracking remains available if cloud configuration is missing or invalid.

Automatic draw sync: after each update the workflow runs `scripts/sync_supabase.py`, which upserts every draw in `results.json` into `draws` (idempotent, keyed on `date,game`). Add two repository secrets (Settings > Secrets and variables > Actions): `SUPABASE_URL` (the project URL) and `SUPABASE_SERVICE_ROLE_KEY` (Project Settings > API > service_role). The service-role key bypasses RLS, so it belongs only in GitHub Secrets, never in `config.js`. Without the secrets the step is skipped. Sets, budget and the bet log still sync from the browser, which requires signing in under Settings > Cloud.

Failure handling: a malformed PCSO row is skipped and logged instead of aborting the import, and a failure in the tests, weekly plan, PCSO fetch or Supabase sync no longer blocks the other steps; the run still ends red so GitHub notifies you. If `results.json` has not changed for 48 hours the Results tab shows a warning banner.

Email preference controls are retained for integration compatibility. The results updater does not send email; these preferences do not send email by themselves.

## My Numbers and Engine v2

My Numbers is a planning workspace. Each line shows its game, next scheduled draw in Philippine time, and ordinary-line cost. Add individual saved sets or engine options to **My Bet Slip**, review the total, and copy the game/date/numbers together. The slip persists in this browser only. Expired draw selections are excluded; they never become bets for another draw. Selection does not purchase a ticket or create a bet-log entry. The budget comparison covers the slip only, not all actual spending. Clear slip removes both upcoming and expired selections.

Engine v2 generates five unique candidate lines from deterministic uniform samples, then favors personal-number preferences, balanced shapes and fewer repeated numbers across the five options. It excludes exact saved-set duplicates and limits pairwise overlap between suggestions to two numbers. These are convenience preferences, not prediction probabilities, a guaranteed wheel, or an advantage on any individual line. There is no winning-confidence percentage. Picks remain stable for the same history, personal numbers and saved sets; correcting historical combinations invalidates cached suggestions. Changes to prize estimates alone do not change the picks.

Analysis excludes invalid and duplicate dated records. The archive report counts scheduled dates absent between the first and last record, without verifying holidays or cancellations. With at least 20 valid draws, the randomness audit compares observed frequency dispersion with 199 simulated archives that draw six balls without replacement. Its empirical p-value has resolution 0.005 and sampling uncertainty; it is exploratory and does not establish a usable bias. Sparse archives do not receive an audit p-value.

Walk-forward comparisons use a 20-draw warmup and three predefined rules: lifetime frequency, last-ten frequency, and lifetime least-frequency. Each test line is generated before seeing the held-out draw. These are historical rule comparisons, **not performance claims for the generated five-line portfolio**. Missing dates are not reconstructed and the best historical rule is not automatically promoted into the generator. Exact single-line prize odds use the hypergeometric distribution.

### Reference projects

Design research (independent implementation; no source code copied):

- [jhadev/lotto](https://github.com/jhadev/lotto): clear per-game number generation.
- [jpdevpersonal/lotto-predictor](https://github.com/jpdevpersonal/lotto-predictor): chronological evaluation, explicit analysis status and comparison with a fair-draw baseline.
- [yaotzin1/lotto-agent](https://github.com/yaotzin1/lotto-agent): reducing repetition across multiple lines and reporting portfolio structure. Historical pair-affinity claims were not adopted as evidence of predictive power.

## Autonomous PHP 300 Weekly Auto Plan

The **₱300 Auto Plan** tab is an independent, automatically selected plan for the five supported major games. At the repository's PHP 25 ordinary-line price, a full week selects 12 lines. Allocation proceeds in equal rounds across the games with randomly assigned extra slots, giving two or three lines per game in a full week. There is at most one line per game per scheduled draw. A partial week can spend less: only draw slots with a future suggested betting time are considered. Unused or skipped money is not rolled over, replaced or used to chase missed draws. The cap applies to this auto plan; manual bets must also fit within the user's real weekly budget and are not automatically deducted from it.

`scripts/weekly_plan.py` uses Python's OS-backed `secrets.SystemRandom` to sample six distinct numbers uniformly. It does not read personal numbers, frequencies, birthdays, engine scores or previous winning combinations. It does not constrain parity, sums, consecutive numbers or portfolio overlap. Every valid combination is eligible. Randomly generated lines do not predict winning results.

The existing scheduled Action creates the plan once each Philippine Monday–Sunday week (normally at the 7:20 AM check), saving `weekly-plan.json` and an immutable dated copy under `plans/`. Reruns reuse the week's saved plan, even if results or settings have changed. Deleting the current pointer recovers the archived plan instead of rerolling. The initial partial-week plan is included in this change. The Action saves a newly created plan even if the PCSO results source is temporarily unavailable, then reports the source failure. GitHub schedules can be delayed; running **Update lotto results** manually also prepares the week's plan.

The UI shows selected cost, locally marked placed cost, pending reserve and unallocated/released funds. **Mark placed** and **Skip** are reversible local bookkeeping, not ticket purchases or cloud bet-log writes. Marks do not sync across devices; the selected numbers do. Results are compared automatically when a matching dated result exists, with plan-only comparisons clearly distinguished from tickets marked placed. Stored plans are never retargeted into another week or draw.

### Betting dates and reminders

Each line shows a suggested 7:00 PM betting time and scheduled 9:00 PM draw in **Asia/Manila**. These are planning times, not an official sales cut-off; verify the outlet's actual closing time and PCSO's schedule, especially holidays and cancellations.

- **Copy today's bets / pending week** includes game, draw, numbers and cost.
- **Download calendar reminders** exports the currently pending dates with 6:30 PM alarms. Import the ICS file into a calendar app and enable notifications there for closed-app reminders. Import each new week's file; imports do not automatically sync after skipping a line or a new plan generation. Remove obsolete calendar entries if plans/statuses change.
- **Enable open-tab reminders** requests browser permission on click. The app checks once per minute, groups due lines by date, and suppresses repeat notices and lines marked placed/skipped. The same button pauses reminders. The page must remain open; browser throttling, platform support and notification settings can delay or prevent alerts. No background web-push or email delivery is configured.
- **Reload saved plan** fetches the same server-selected numbers; it never regenerates them.

The calendar uses UTC timestamps (converted from Philippine time), stable weekly/day event IDs and standard display alarms. No reminders or calendar entries are created in external accounts automatically.

### Receipt-style print preview

On Auto Plan, choose **Print receipt preview**. The 80 mm-style preview groups lines by game/category and includes suggested betting dates, draw dates, saved numbers, line costs, category subtotals and a grand total. It defaults to pending upcoming bets, excluding lines marked placed/skipped and expired draws. Choose today's pending bets, the full week (with each status clearly printed), or a particular game. The preview initially follows the page's selected game filter.

**Print / Save PDF** opens the browser's print dialog. Only the receipt prints; app navigation and preview controls are hidden. Select the actual paper size in the printer dialog or save to PDF on ordinary paper. The receipt is a personal checklist, not an official lottery ticket. Printing does not regenerate numbers, purchase tickets or change placed/skip marks.
