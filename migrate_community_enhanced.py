"""
Migration script to add enhanced community features to the database.
This adds all the new columns needed for the world-class community platform.
"""

import os
import psycopg2
from psycopg2.extras import DictCursor

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not found")
        
        connection = psycopg2.connect(database_url)
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def migrate_community_table():
    """Add new columns to the community table for enhanced features."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Add new columns to community table
        migrations = [
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS upvotes INTEGER DEFAULT 0",
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS downvotes INTEGER DEFAULT 0", 
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS total_votes INTEGER DEFAULT 0",
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS photo_url TEXT",
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS video_url TEXT",
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE",
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE",
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE",
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS deleted_reason TEXT",
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS doctor_verified BOOLEAN DEFAULT FALSE",
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS trending_score FLOAT DEFAULT 0.0",
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS content_type TEXT DEFAULT 'text'",
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS poll_options JSONB",
            "ALTER TABLE community ADD COLUMN IF NOT EXISTS poll_votes JSONB"
        ]
        
        for migration in migrations:
            print(f"Executing: {migration}")
            cursor.execute(migration)
            
        # Add new columns to community_replies table
        reply_migrations = [
            "ALTER TABLE community_replies ADD COLUMN IF NOT EXISTS parent_reply_id INTEGER REFERENCES community_replies(id)",
            "ALTER TABLE community_replies ADD COLUMN IF NOT EXISTS is_expert_advice BOOLEAN DEFAULT FALSE",
            "ALTER TABLE community_replies ADD COLUMN IF NOT EXISTS is_ai_response BOOLEAN DEFAULT FALSE",
            "ALTER TABLE community_replies ADD COLUMN IF NOT EXISTS photo_url TEXT",
            "ALTER TABLE community_replies ADD COLUMN IF NOT EXISTS video_url TEXT"
        ]
        
        for migration in reply_migrations:
            print(f"Executing: {migration}")
            cursor.execute(migration)
        
        conn.commit()
        print("✅ Successfully migrated community table with enhanced features!")
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def create_new_tables():
    """Create new tables for enhanced community features."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create thread_votes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS thread_votes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                thread_id INTEGER NOT NULL REFERENCES community(id) ON DELETE CASCADE,
                vote_type TEXT NOT NULL CHECK (vote_type IN ('upvote', 'downvote')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, thread_id)
            )
        """)
        
        # Create reply_votes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reply_votes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                reply_id INTEGER NOT NULL REFERENCES community_replies(id) ON DELETE CASCADE,
                vote_type TEXT NOT NULL CHECK (vote_type IN ('upvote', 'downvote')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, reply_id)
            )
        """)
        
        # Create thread_saves table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS thread_saves (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                thread_id INTEGER NOT NULL REFERENCES community(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, thread_id)
            )
        """)
        
        # Create thread_follows table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS thread_follows (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                thread_id INTEGER NOT NULL REFERENCES community(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, thread_id)
            )
        """)
        
        # Create thread_reactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS thread_reactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                thread_id INTEGER NOT NULL REFERENCES community(id) ON DELETE CASCADE,
                reaction_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, thread_id, reaction_type)
            )
        """)
        
        # Create user_badges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_badges (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                badge_type TEXT NOT NULL,
                badge_name TEXT NOT NULL,
                badge_description TEXT,
                badge_icon TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_visible BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Create user_reputation table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_reputation (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                action_type TEXT NOT NULL,
                points INTEGER NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create user_profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                avatar_url TEXT,
                cover_photo_url TEXT,
                location TEXT,
                age_range TEXT,
                interests TEXT[],
                experience_level TEXT,
                total_reputation INTEGER DEFAULT 0,
                helpful_votes INTEGER DEFAULT 0,
                threads_created INTEGER DEFAULT 0,
                replies_posted INTEGER DEFAULT 0,
                show_age BOOLEAN DEFAULT FALSE,
                show_location BOOLEAN DEFAULT TRUE,
                allow_messages BOOLEAN DEFAULT TRUE,
                UNIQUE(user_id)
            )
        """)
        
        conn.commit()
        print("✅ Successfully created all new community tables!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating new tables: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Run the complete migration."""
    print("🚀 Starting enhanced community migration...")
    
    # Step 1: Migrate existing tables
    if migrate_community_table():
        print("✅ Step 1: Community table migration completed")
    else:
        print("❌ Step 1: Community table migration failed")
        return
    
    # Step 2: Create new tables
    if create_new_tables():
        print("✅ Step 2: New tables creation completed")
    else:
        print("❌ Step 2: New tables creation failed")
        return
    
    print("🎉 Enhanced community migration completed successfully!")
    print("📝 The database now supports:")
    print("   • Voting system (upvotes/downvotes)")
    print("   • Thread saves and follows") 
    print("   • Emoji reactions")
    print("   • User badges and reputation")
    print("   • Enhanced user profiles")
    print("   • Rich content (images/videos)")
    print("   • Nested replies")
    print("   • And much more!")

if __name__ == "__main__":
    main()