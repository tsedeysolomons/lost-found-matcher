-- Lost and Found Database Setup Script
-- Run this with: psql -U postgres -f setup_database.sql

-- Create database (if not exists)
SELECT 'CREATE DATABASE lost_found_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'lost_found_db')\gexec

-- Connect to the database
\c lost_found_db

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension
\dx

-- Show success message
\echo 'Database setup complete!'
\echo 'Extension pgvector installed: YES'
\echo ''
\echo 'Next steps:'
\echo '1. Update backend/.env with:'
\echo '   DATABASE_URL=postgresql://postgres:2124newpassword@localhost:5432/lost_found_db'
\echo '2. Run: python backend/init_db.py'
