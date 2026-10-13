-- نفّذ هذا الملف من SQL Editor في Supabase. النشر باسم زائر لا يثبت الهوية.
create table if not exists public.comments (id bigint generated always as identity primary key, novel text not null check(novel in ('zat','kader')), chapter integer not null check(chapter between 1 and 99), name text not null check(char_length(trim(name)) between 2 and 50), body text not null check(char_length(trim(body)) between 3 and 1500), created_at timestamptz not null default now());
create table if not exists public.ratings (id bigint generated always as identity primary key, novel text not null check(novel in ('zat','kader')), chapter integer not null check(chapter between 1 and 99), name text not null check(char_length(trim(name)) between 2 and 50), stars integer not null check(stars between 1 and 5), created_at timestamptz not null default now());
alter table public.comments enable row level security;
alter table public.ratings enable row level security;
create policy "Public read comments" on public.comments for select to anon using (true);
create policy "Public submit comments" on public.comments for insert to anon with check (true);
create policy "Public read ratings" on public.ratings for select to anon using (true);
create policy "Public submit ratings" on public.ratings for insert to anon with check (true);
grant select,insert on public.comments,public.ratings to anon;
grant usage,select on all sequences in schema public to anon;
-- مهم: بدون CAPTCHA / Rate limiting أو moderation، يمكن إساءة استخدام النشر وتكرار التقييمات.
