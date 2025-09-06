-- Database Migration Commands for 2-Step Authentication
-- Run these commands in your Supabase SQL Editor

-- Add missing columns for user profile completion
ALTER TABLE users ADD COLUMN IF NOT EXISTS age INTEGER;
ALTER TABLE users ADD COLUMN IF NOT EXISTS gender TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS city TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS interests TEXT[];
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_completed BOOLEAN DEFAULT FALSE;

-- Update existing users with auto-generated names to incomplete profile status
UPDATE users SET profile_completed = FALSE WHERE name LIKE 'User %' OR name IS NULL;

-- Verify the columns were added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('age', 'gender', 'city', 'interests', 'profile_completed')
ORDER BY column_name;

-- Check current user status
SELECT id, name, phone_number, profile_completed 
FROM users 
WHERE phone_number = '+918074491308';