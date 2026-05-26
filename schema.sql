-- ─────────────────────────────────────────────────────────────────────────
-- Supabase schema for Gym Agent
-- Run this in the Supabase SQL editor (Dashboard → SQL Editor → New Query)
-- ─────────────────────────────────────────────────────────────────────────

-- Enable UUID extension (already enabled on Supabase by default)
-- create extension if not exists "uuid-ossp";

-- ── Users ──────────────────────────────────────────────────────────────────
create table if not exists users (
  id            bigserial primary key,
  telegram_id   bigint unique not null,
  name          text not null,
  level         int not null default 1,
  xp            int not null default 0,
  streak        int not null default 0,
  difficulty    text not null default 'beginner'
                  check (difficulty in ('beginner', 'intermediate', 'advanced')),
  created_at    timestamptz not null default now()
);

create index if not exists users_telegram_id_idx on users (telegram_id);

-- ── Workout Logs ───────────────────────────────────────────────────────────
create table if not exists workout_logs (
  id            bigserial primary key,
  user_id       bigint not null references users(id) on delete cascade,
  log_date      date not null default current_date,
  exercise_name text not null,
  completed     boolean not null default false,
  xp_earned     int not null default 0,
  created_at    timestamptz not null default now(),
  unique (user_id, log_date, exercise_name)
);

create index if not exists workout_logs_user_date_idx on workout_logs (user_id, log_date);

-- ── User State ─────────────────────────────────────────────────────────────
create table if not exists user_state (
  id                        bigserial primary key,
  user_id                   bigint unique not null references users(id) on delete cascade,
  conversation_history      jsonb not null default '[]',
  workout_sent_today        boolean not null default false,
  reminder_sent_today       boolean not null default false,
  last_workout_message_id   bigint,
  updated_at                timestamptz not null default now()
);

-- Auto-update updated_at
create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger user_state_updated_at
  before update on user_state
  for each row execute procedure update_updated_at();

-- ── Weekly Stats ───────────────────────────────────────────────────────────
create table if not exists weekly_stats (
  id                bigserial primary key,
  user_id           bigint not null references users(id) on delete cascade,
  week_start        date not null,
  workouts_done     int not null default 0,
  total_calories    int not null default 0,
  personal_records  jsonb not null default '{}',
  total_xp_earned   int not null default 0,
  created_at        timestamptz not null default now(),
  unique (user_id, week_start)
);

create index if not exists weekly_stats_user_week_idx on weekly_stats (user_id, week_start);

-- ── User Preferences ──────────────────────────────────────────────────────
create table if not exists user_preferences (
  id              bigserial primary key,
  user_id         bigint unique not null references users(id) on delete cascade,
  equipment       jsonb not null default '["treadmill","jump_rope","resistance_band","bodyweight"]',
  goals           jsonb not null default '["weight_loss","muscle","endurance"]',
  target_muscles  jsonb not null default '[]',
  exclusions      jsonb not null default '[]',
  session_minutes int not null default 35,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create trigger user_preferences_updated_at
  before update on user_preferences
  for each row execute procedure update_updated_at();

-- ── Daily Workouts (AI-generated plan cache) ───────────────────────────────
-- One row per generated plan. Not unique on (user_id, plan_date) because
-- quick workouts and regenerate each add a new row.
-- Consider a cleanup job to delete rows older than 30 days.
create table if not exists daily_workouts (
  id          bigserial primary key,
  user_id     bigint not null references users(id) on delete cascade,
  plan_date   date not null default current_date,
  category    text not null,
  source      text not null default 'ai' check (source in ('ai', 'fallback', 'quick')),
  plan        jsonb not null,
  created_at  timestamptz not null default now()
);

create index if not exists daily_workouts_user_date_idx on daily_workouts (user_id, plan_date);

-- ── Row Level Security (RLS) ───────────────────────────────────────────────
-- The app connects with the service role key (bypasses RLS),
-- but enable RLS to prevent accidental public reads.

alter table users enable row level security;
alter table workout_logs enable row level security;
alter table user_state enable row level security;
alter table weekly_stats enable row level security;
alter table user_preferences enable row level security;
alter table daily_workouts enable row level security;

-- Service role already bypasses RLS — no policies needed for the backend.
-- Add anon-read policies only if you expose a public dashboard later.
