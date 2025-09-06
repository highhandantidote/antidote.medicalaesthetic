#!/usr/bin/env python3
"""
Fix database schema for 2-step authentication
This adds the missing columns that the previous agent's implementation requires
"""
import psycopg2
import os
import sys

def add_missing_columns():
    try:
        # Connect to database
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        conn.autocommit = True  # Autocommit each statement
        cur = conn.cursor()
        
        print("🔧 Adding missing columns for 2-step authentication...")
        
        # Add columns one by one with autocommit
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS age INTEGER;")
            print("✅ Added age column")
        except Exception as e:
            print(f"⚠️ Age column: {e}")
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS gender TEXT;")
            print("✅ Added gender column")
        except Exception as e:
            print(f"⚠️ Gender column: {e}")
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS city TEXT;")
            print("✅ Added city column")
        except Exception as e:
            print(f"⚠️ City column: {e}")
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS interests TEXT[];")
            print("✅ Added interests column")
        except Exception as e:
            print(f"⚠️ Interests column: {e}")
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_completed BOOLEAN DEFAULT FALSE;")
            print("✅ Added profile_completed column")
        except Exception as e:
            print(f"⚠️ Profile_completed column: {e}")
        
        # Update existing users with auto-generated names
        try:
            cur.execute("UPDATE users SET profile_completed = FALSE WHERE name LIKE 'User %';")
            print("✅ Updated existing users to incomplete profile status")
        except Exception as e:
            print(f"⚠️ Update users: {e}")
        
        cur.close()
        conn.close()
        print("🎉 Database schema update completed!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    success = add_missing_columns()
    if not success:
        sys.exit(1)