-- ============================================
-- Drop All Tables - Use with CAUTION!
-- ============================================
-- This will delete all data and tables
-- Run with: psql -U postgres -d lost_found_db -f drop_tables.sql

\c lost_found_db

-- Drop tables
DROP TABLE IF EXISTS reports CASCADE;

-- Drop types
DROP TYPE IF EXISTS report_type CASCADE;
DROP TYPE IF EXISTS report_status CASCADE;

-- Drop function
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

\echo '✓ All tables and types dropped!'
\echo 'Run create_tables.sql to recreate the schema.'
