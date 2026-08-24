-- ============================================
-- Lost and Found Matcher Database Schema
-- ============================================
-- This script creates all necessary tables for the Lost and Found matching system
-- Run with: psql -U postgres -d lost_found_db -f create_tables.sql

-- Connect to database
\c lost_found_db

-- Enable pgvector extension (must be installed first)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- Drop existing tables (if any) - CAREFUL!
-- ============================================
-- Uncomment these lines if you want to reset the database
-- DROP TABLE IF EXISTS reports CASCADE;
-- DROP TYPE IF EXISTS report_type CASCADE;
-- DROP TYPE IF EXISTS report_status CASCADE;

-- ============================================
-- Create ENUM types
-- ============================================

-- Report type: Lost or Found
CREATE TYPE report_type AS ENUM ('Lost', 'Found');

-- Report status: Searching, Unclaimed, or Resolved
CREATE TYPE report_status AS ENUM ('Searching', 'Unclaimed', 'Resolved');

-- ============================================
-- Create Reports Table
-- ============================================

CREATE TABLE reports (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Report Type
    type report_type NOT NULL,
    
    -- Item Details
    item VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    color VARCHAR(100) NOT NULL,
    location VARCHAR(500) NOT NULL,
    date DATE NOT NULL,
    details TEXT,
    
    -- Status
    status report_status NOT NULL DEFAULT 'Searching',
    
    -- AI/ML Features
    embedding vector(384),  -- Sentence Transformers embedding (384 dimensions)
    keywords TEXT[],        -- Extracted keywords for matching
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Create Indexes for Performance
-- ============================================

-- Index on type for filtering Lost/Found
CREATE INDEX idx_reports_type ON reports(type);

-- Index on category for filtering by category
CREATE INDEX idx_reports_category ON reports(category);

-- Index on date for date range queries
CREATE INDEX idx_reports_date ON reports(date DESC);

-- Index on status for filtering active reports
CREATE INDEX idx_reports_status ON reports(status);

-- Composite index for common query patterns
CREATE INDEX idx_reports_type_category_status ON reports(type, category, status);

-- Index on created_at for sorting recent reports
CREATE INDEX idx_reports_created_at ON reports(created_at DESC);

-- ============================================
-- Create Function to Update updated_at Timestamp
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Create Trigger to Auto-Update updated_at
-- ============================================

CREATE TRIGGER update_reports_updated_at
    BEFORE UPDATE ON reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Insert Sample Data (Optional - for testing)
-- ============================================

-- Sample Lost Reports
INSERT INTO reports (type, item, category, color, location, date, status, details) VALUES
('Lost', 'AirPods Pro (2nd gen)', 'Electronics', 'White', 'Student Union, 2nd floor', '2024-04-18', 'Searching', 'White case with a small blue sticker on the lid.'),
('Lost', 'Navy blue hoodie', 'Clothing', 'Navy blue', 'Recreation Center', '2024-04-15', 'Searching', 'Size M, university crest embroidered on front.'),
('Lost', 'Black water bottle', 'Personal items', 'Black', 'Science Library', '2024-04-20', 'Searching', 'Matte black bottle with a silver cap.');

-- Sample Found Reports
INSERT INTO reports (type, item, category, color, location, date, status, details) VALUES
('Found', 'Apple AirPods case', 'Electronics', 'White', 'Student Union', '2024-04-19', 'Unclaimed', 'Found near the second-floor study tables.'),
('Found', 'Blue university hoodie', 'Clothing', 'Navy blue', 'Recreation Center locker room', '2024-04-16', 'Unclaimed', 'Medium hoodie folded on a bench.');

-- ============================================
-- Verify Table Structure
-- ============================================

-- Show table structure
\d reports

-- Show indexes
\di

-- Count records
SELECT 
    type,
    COUNT(*) as count
FROM reports
GROUP BY type;

-- ============================================
-- Useful Queries for Testing
-- ============================================

-- View all reports
-- SELECT * FROM reports ORDER BY created_at DESC;

-- View Lost reports only
-- SELECT * FROM reports WHERE type = 'Lost' ORDER BY date DESC;

-- View Found reports only
-- SELECT * FROM reports WHERE type = 'Found' ORDER BY date DESC;

-- View by category
-- SELECT * FROM reports WHERE category = 'Electronics';

-- View active reports (not resolved)
-- SELECT * FROM reports WHERE status != 'Resolved';

-- ============================================
-- Grant Permissions (if needed)
-- ============================================

-- Grant all privileges to postgres user
GRANT ALL PRIVILEGES ON TABLE reports TO postgres;
GRANT USAGE, SELECT ON SEQUENCE reports_id_seq TO postgres;

-- ============================================
-- Display Success Message
-- ============================================

\echo ''
\echo '=========================================='
\echo '✓ Database schema created successfully!'
\echo '=========================================='
\echo ''
\echo 'Tables created:'
\echo '  - reports (with pgvector support)'
\echo ''
\echo 'Indexes created:'
\echo '  - idx_reports_type'
\echo '  - idx_reports_category'
\echo '  - idx_reports_date'
\echo '  - idx_reports_status'
\echo '  - idx_reports_type_category_status'
\echo '  - idx_reports_created_at'
\echo ''
\echo 'Sample data:'
\echo '  - 3 Lost reports'
\echo '  - 2 Found reports'
\echo ''
\echo 'Next steps:'
\echo '  1. Verify with: SELECT * FROM reports;'
\echo '  2. Start backend: cd backend && python run.py'
\echo '  3. Backend will use SQLAlchemy ORM'
\echo ''
\echo '=========================================='
