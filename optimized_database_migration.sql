-- Optimized Database Migration for 2-Step Authentication
-- Following Supabase assistant's timeout debugging approach

-- Step 1: Check current table structure and size
SELECT 
    schemaname, 
    tablename, 
    attname as column_name, 
    typename as data_type,
    n_distinct,
    most_common_vals
FROM pg_stats 
WHERE tablename = 'users' 
ORDER BY attname;

-- Step 2: Check table size to understand why operations might timeout
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    most_common_vals,
    (n_distinct * avg_width) as estimated_size
FROM pg_stats 
WHERE tablename = 'users';

-- Step 3: Check for existing locks that might cause timeouts
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query,
    query_start
FROM pg_stat_activity 
WHERE datname = current_database() 
AND state != 'idle';

-- Step 4: Add columns one by one with shorter timeouts (safer approach)
-- Run these individually, not all at once

-- Column 1: Age
ALTER TABLE users ADD COLUMN IF NOT EXISTS age INTEGER;

-- Column 2: Gender  
ALTER TABLE users ADD COLUMN IF NOT EXISTS gender TEXT;

-- Column 3: City
ALTER TABLE users ADD COLUMN IF NOT EXISTS city TEXT;

-- Column 4: Interests (this might be the problematic one due to array type)
ALTER TABLE users ADD COLUMN IF NOT EXISTS interests TEXT[];

-- Column 5: Profile completed
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_completed BOOLEAN DEFAULT FALSE;

-- Step 5: Verify columns were added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('age', 'gender', 'city', 'interests', 'profile_completed')
ORDER BY column_name;

-- Step 6: Update existing users (do this AFTER adding columns successfully)
-- Use LIMIT to process in smaller batches if needed
UPDATE users 
SET profile_completed = FALSE 
WHERE (name LIKE 'User %' OR name IS NULL)
AND profile_completed IS NULL
LIMIT 100;

-- Step 7: Verify the specific user we're working with
SELECT id, name, phone_number, profile_completed, created_at
FROM users 
WHERE phone_number = '+918074491308';