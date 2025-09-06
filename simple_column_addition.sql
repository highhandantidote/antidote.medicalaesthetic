-- Ultra-Simple Column Addition (run these ONE AT A TIME)
-- If the full migration times out, try these individual commands

-- Command 1: Add age column
ALTER TABLE users ADD COLUMN IF NOT EXISTS age INTEGER;

-- Command 2: Add gender column  
ALTER TABLE users ADD COLUMN IF NOT EXISTS gender TEXT;

-- Command 3: Add city column
ALTER TABLE users ADD COLUMN IF NOT EXISTS city TEXT;

-- Command 4: Add interests column
ALTER TABLE users ADD COLUMN IF NOT EXISTS interests TEXT[];

-- Command 5: Add profile_completed column
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_completed BOOLEAN DEFAULT FALSE;

-- Command 6: Update existing users with auto-generated names
UPDATE users SET profile_completed = FALSE WHERE name LIKE 'User %' OR name IS NULL;