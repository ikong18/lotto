# Lotto Tracker

A static, personal tracker for five PCSO major games: 6/58, 6/55, 6/49, 6/45 and 6/42.

- Results and history use `results.json`; they are not a live PCSO feed.
- Upcoming Picks shows repeatable combinations, the next scheduled draw in Philippine time, and clearly labeled prize estimates.
- Settings edits all five games. Fill the blank six-number row to add a set; clear all numbers in a row to remove it. Changes save in this browser.
- Overview backtests your current sets against recorded history; it does not represent actual bets.
- Budget compares mathematical odds and estimated returns. No number selection method predicts an independent draw.

## Run locally

Run `python -m http.server 8000` in this directory and open http://localhost:8000. Run regression checks with `node tests.cjs`. No build or package installation is required.

## GitHub Pages

In repository Settings > Pages, deploy the `main` branch root. Update `results.json` manually with verified results. Each draw requires `date` (YYYY-MM-DD), `game` (ultra, grand, super, mega or lotto), and six unique in-range `numbers`. Optional fields are `jackpot`, `winners`, and `prizes` (for example, `"5": [winnerCount, payoutPerWinner]`).

## Optional cloud and email integrations

`config.js` accepts only the public HTTPS Supabase project URL and a public anon/publishable key. Never put a database password or service key in browser files. The previously committed database password must be rotated in Supabase; removing it from the latest file does not remove it from Git history.

Cloud sync expects existing `draws`, `app_state`, and `bets` tables with appropriate access policies. This repository does not include their schema, so cloud sync needs separate setup and verification. Local tracking remains available if cloud configuration is missing or invalid.

Email preference controls are retained for integration compatibility. This repository currently contains no updater, scraper or email workflow; these preferences do not send email by themselves.
