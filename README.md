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

You can also update `results.json` manually with verified results. Each draw requires `date` (YYYY-MM-DD), `game` (ultra, grand, super, mega or lotto), and six unique in-range `numbers`. Optional fields are `jackpot`, `winners`, and `prizes` (for example, `"5": [winnerCount, payoutPerWinner]`).

## Optional cloud and email integrations

`config.js` accepts only the public HTTPS Supabase project URL and a public anon/publishable key. Never put a database password or service key in browser files. The previously committed database password must be rotated in Supabase; removing it from the latest file does not remove it from Git history.

Cloud sync expects existing `draws`, `app_state`, and `bets` tables with appropriate access policies. This repository does not include their schema, so cloud sync needs separate setup and verification. Local tracking remains available if cloud configuration is missing or invalid.

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
