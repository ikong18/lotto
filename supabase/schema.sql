-- Reference schema for the cloud features in index.html. Compare with your existing
-- tables before running (Supabase > SQL editor); every statement is safe to re-run.
--
-- BEFORE RUNNING: replace OWNER_EMAIL_HERE below with the email you sign in with.
-- Only that signed-in user can write; everyone (the public site) can read draws.
-- The GitHub Action writes with the service-role key, which bypasses RLS.

create table if not exists public.draws (
  date      date    not null,
  game      text    not null check (game in ('ultra','grand','super','mega','lotto')),
  numbers   integer[] not null check (cardinality(numbers) = 6),
  jackpot   numeric,
  winners   integer,
  prizes    jsonb,
  notified  boolean not null default false,
  primary key (date, game)
);

create table if not exists public.app_state (
  key        text primary key,
  value      jsonb not null,
  updated_at timestamptz not null default now()
);

create table if not exists public.bets (
  id         bigint generated always as identity primary key,
  played_on  date    not null,
  game       text    not null,
  numbers    integer[],
  amount     numeric not null check (amount > 0),
  created_at timestamptz not null default now()
);

alter table public.draws     enable row level security;
alter table public.app_state enable row level security;
alter table public.bets      enable row level security;

-- Results are public information: anyone may read them.
drop policy if exists "draws are public" on public.draws;
create policy "draws are public" on public.draws for select to anon, authenticated using (true);

-- Writes to draws from the browser (the Settings > Upload button): owner only.
drop policy if exists "owner writes draws" on public.draws;
create policy "owner writes draws" on public.draws for all to authenticated
  using ((auth.jwt() ->> 'email') = 'OWNER_EMAIL_HERE')
  with check ((auth.jwt() ->> 'email') = 'OWNER_EMAIL_HERE');

-- Personal state (sets, budget, bet log): owner only, no public access at all.
drop policy if exists "owner app_state" on public.app_state;
create policy "owner app_state" on public.app_state for all to authenticated
  using ((auth.jwt() ->> 'email') = 'OWNER_EMAIL_HERE')
  with check ((auth.jwt() ->> 'email') = 'OWNER_EMAIL_HERE');

drop policy if exists "owner bets" on public.bets;
create policy "owner bets" on public.bets for all to authenticated
  using ((auth.jwt() ->> 'email') = 'OWNER_EMAIL_HERE')
  with check ((auth.jwt() ->> 'email') = 'OWNER_EMAIL_HERE');
