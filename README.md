# Lotto Tracker (GitHub Pages)
Tracks all five PCSO majors (6/58, 6/55, 6/49, 6/45, 6/42). The Budget tab ranks games for your weekly budget by expected return, prize frequency or jackpot odds; set sets for the new games by adding them to `sets.json`.
1. Upload these files to your repo (e.g. `hallmarks`). Settings > Pages > Deploy from branch > `main` / root. Site: `https://<user>.github.io/<repo>/`.
2. Settings > Actions > General > Workflow permissions: **Read and write**.
3. Settings > Secrets and variables > Actions, add: `RESEND_API_KEY`, `EMAIL_TO` (your email), optional `EMAIL_FROM`.
   Without a verified domain in Resend, the default sender `onboarding@resend.dev` can only email the address on your Resend account.
4. Actions tab > "Update lotto results" > Run workflow once to test (mode `draw`, or `weekly` for the weekly email).
- Schedule: after each draw (Tue/Thu/Fri/Sun ~9:30PM PH) it scrapes thesummitexpress.com, updates `results.json`, emails WIN/LOSE + results. Monday 9AM PH: weekly summary.
- Edit your numbers in `sets.json`. If scraping breaks, add a draw by hand in `results.json` (`{"date","game":"ultra|super","numbers":[...],"notified":false}`) or use Run workflow with a date (`from` + `date` backfills a whole range, including real jackpot, winner counts and 5/4/3-match payouts). Optional per-draw fields: `jackpot`, `winners`, `prizes` (`{"5":[winners,php],...}`); the app uses real payouts when present.
- Check the source site's terms before relying on the scraper.
