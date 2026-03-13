create table if not exists public.market_snapshots (
  fund_code text not null,
  trade_date date not null,
  latest_nav numeric not null,
  latest_nav_date date not null,
  source text not null,
  created_at timestamptz not null default now(),
  primary key (fund_code, trade_date)
);

alter table public.market_snapshots disable row level security;
