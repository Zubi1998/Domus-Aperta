-- Domus Aperta - Nachtrag: DELETE-Policies fuer Supabase
-- Diese SQL-Datei einmalig im Supabase SQL Editor ausfuehren,
-- damit die App Eintraege loeschen kann.
--
-- Hintergrund: Die urspruengliche Migration hat nur SELECT/INSERT/UPDATE
-- Policies erstellt. Ohne DELETE-Policy blockiert Supabase Row Level Security
-- saemtliche DELETE-Operationen stillschweigend.

drop policy if exists "gastgeber_delete" on public.gastgeber;
create policy "gastgeber_delete" on public.gastgeber
    for delete to anon, authenticated using (true);

drop policy if exists "checks_delete" on public.checks;
create policy "checks_delete" on public.checks
    for delete to anon, authenticated using (true);
