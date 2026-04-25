-- ===========================================================================
-- Domus Aperta - Initial Schema fuer Supabase
-- ---------------------------------------------------------------------------
-- Ausfuehren im Supabase SQL Editor:
--   https://supabase.com/dashboard/project/uimsswjellvsvyrtphyx/sql/new
-- Einmalig ausfuehren. Kann durch erneute Ausfuehrung gefahrlos wiederholt werden
-- (alle Statements sind idempotent).
-- ===========================================================================

-- Gastgeber -----------------------------------------------------------------
create table if not exists public.gastgeber (
    id bigint generated always as identity primary key,
    name text not null unique,
    beschreibung text,
    erstellt timestamptz not null default now()
);

comment on table public.gastgeber is 'Gastgeber des Domus Aperta Bundes';

-- Checks --------------------------------------------------------------------
create table if not exists public.checks (
    id bigint generated always as identity primary key,
    gastgeber_id bigint not null references public.gastgeber(id) on delete cascade,
    datum date not null,
    bewerter text not null,
    empfang integer not null check (empfang between 1 and 10),
    essen integer not null check (essen between 1 and 10),
    aufmerksamkeit integer not null check (aufmerksamkeit between 1 and 10),
    wow integer not null check (wow between 1 and 10),
    bonus integer not null default 0 check (bonus between -5 and 5),
    kommentar text,
    erstellt timestamptz not null default now()
);

comment on table public.checks is 'Hospitality-Check-Bewertungen';

create index if not exists checks_gastgeber_id_idx on public.checks(gastgeber_id);
create index if not exists checks_datum_idx on public.checks(datum desc);

-- Row Level Security --------------------------------------------------------
alter table public.gastgeber enable row level security;
alter table public.checks enable row level security;

-- Policies: Anon-Key (wird von der App benutzt) darf lesen und schreiben.
-- Die eigentliche Zugangskontrolle laeuft ueber das Passwort-Gate in der App.
-- Der Anon-Key liegt nur in den Streamlit-Secrets und ist nicht oeffentlich.

drop policy if exists "gastgeber_read" on public.gastgeber;
create policy "gastgeber_read" on public.gastgeber
    for select to anon, authenticated using (true);

drop policy if exists "gastgeber_insert" on public.gastgeber;
create policy "gastgeber_insert" on public.gastgeber
    for insert to anon, authenticated with check (true);

drop policy if exists "gastgeber_update" on public.gastgeber;
create policy "gastgeber_update" on public.gastgeber
    for update to anon, authenticated using (true) with check (true);

drop policy if exists "checks_read" on public.checks;
create policy "checks_read" on public.checks
    for select to anon, authenticated using (true);

drop policy if exists "checks_insert" on public.checks;
create policy "checks_insert" on public.checks
    for insert to anon, authenticated with check (true);

drop policy if exists "checks_update" on public.checks;
create policy "checks_update" on public.checks
    for update to anon, authenticated using (true) with check (true);

drop policy if exists "gastgeber_delete" on public.gastgeber;
create policy "gastgeber_delete" on public.gastgeber
    for delete to anon, authenticated using (true);

drop policy if exists "checks_delete" on public.checks;
create policy "checks_delete" on public.checks
    for delete to anon, authenticated using (true);
