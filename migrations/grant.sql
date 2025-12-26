CREATE ROLE authenticated NOLOGIN;
GRANT authenticated TO neondb_owner;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT SELECT ON public.sources_types TO authenticated; 
GRANT SELECT, INSERT, UPDATE, DELETE ON public.sources TO authenticated;
GRANT SELECT, INSERT ON public.sources_collect_jobs TO authenticated;
GRANT USAGE ON SEQUENCE sources_collect_jobs_id_seq TO authenticated;
GRANT SELECT ON public.extensions TO authenticated;
GRANT SELECT ON public.logs TO authenticated;