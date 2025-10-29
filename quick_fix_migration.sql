-- Quick fix to add is_admin column if it doesn't exist
-- Run this manually if migrations fail

-- For MySQL/MariaDB:
ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT FALSE NOT NULL;

-- For PostgreSQL:
-- ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT FALSE NOT NULL;

-- For SQLite:
-- ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL;

-- Verify:
-- SELECT * FROM user LIMIT 1;

