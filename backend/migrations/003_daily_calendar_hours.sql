-- Apply the salon-approved daily operating window to untouched closed defaults only.
-- Existing customized calendar hours are preserved.
BEGIN;
SELECT pg_advisory_xact_lock(69020261020);

UPDATE lb_calendar_settings
SET value = '{"enabled":true,"week":[[540,1020],[540,1020],[540,1020],[540,1020],[540,1020],[540,1020],[540,1020]]}'::json
WHERE id = 'salon'
  AND value::jsonb ->> 'enabled' = 'false'
  AND value::jsonb -> 'week' = '[null,null,null,null,null,null,null]'::jsonb;

INSERT INTO lb_schema (version) VALUES (3) ON CONFLICT DO NOTHING;
COMMIT;
