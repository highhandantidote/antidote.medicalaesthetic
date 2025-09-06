"""
Create personalization tables for anonymous user tracking.
This script creates the necessary database tables to support personalized recommendations.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def create_personalization_tables():
    """Create tables for personalization system."""
    try:
        # Connect to database
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cur = conn.cursor()
        
        print("Creating personalization tables...")
        
        # Create anonymous_users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS anonymous_users (
                id SERIAL PRIMARY KEY,
                browser_fingerprint VARCHAR(64) UNIQUE NOT NULL,
                session_id VARCHAR(64),
                preferred_categories JSONB DEFAULT '{}',
                interest_keywords JSONB DEFAULT '{}',
                location_data JSONB DEFAULT '{}',
                visit_count INTEGER DEFAULT 1,
                total_time_spent INTEGER DEFAULT 0,
                last_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                first_visit TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create user_interactions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_interactions (
                id SERIAL PRIMARY KEY,
                anonymous_user_id INTEGER REFERENCES anonymous_users(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                interaction_type VARCHAR(50) NOT NULL,
                content_type VARCHAR(50) NOT NULL,
                content_id INTEGER NOT NULL,
                content_name TEXT,
                page_url TEXT,
                referrer TEXT,
                session_id VARCHAR(64),
                time_spent INTEGER DEFAULT 0,
                interaction_data JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create search_history table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id SERIAL PRIMARY KEY,
                anonymous_user_id INTEGER REFERENCES anonymous_users(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                query TEXT NOT NULL,
                search_type VARCHAR(50),
                results_count INTEGER DEFAULT 0,
                clicked_result_id INTEGER,
                clicked_result_type VARCHAR(50),
                session_id VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create personalization_insights table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS personalization_insights (
                id SERIAL PRIMARY KEY,
                anonymous_user_id INTEGER REFERENCES anonymous_users(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                insight_type VARCHAR(50) NOT NULL,
                insight_data JSONB NOT NULL,
                confidence_score REAL DEFAULT 0.0,
                computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            );
        """)
        
        # Create content_recommendations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS content_recommendations (
                id SERIAL PRIMARY KEY,
                anonymous_user_id INTEGER REFERENCES anonymous_users(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                content_type VARCHAR(50) NOT NULL,
                content_id INTEGER NOT NULL,
                recommendation_score REAL NOT NULL,
                reasoning TEXT,
                recommendation_context VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                shown_count INTEGER DEFAULT 0,
                clicked BOOLEAN DEFAULT FALSE
            );
        """)
        
        # Create indexes for better performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_anonymous_users_fingerprint ON anonymous_users(browser_fingerprint);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_interactions_anonymous_user ON user_interactions(anonymous_user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_interactions_content ON user_interactions(content_type, content_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_search_history_anonymous_user ON search_history(anonymous_user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_personalization_insights_anonymous_user ON personalization_insights(anonymous_user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_content_recommendations_anonymous_user ON content_recommendations(anonymous_user_id);")
        
        # Commit changes
        conn.commit()
        print("Personalization tables created successfully!")
        
        # Check table creation
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('anonymous_users', 'user_interactions', 'search_history', 'personalization_insights', 'content_recommendations')
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        print(f"Created {len(tables)} personalization tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error creating personalization tables: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = create_personalization_tables()
    if success:
        print("\nPersonalization system database setup complete!")
    else:
        print("\nFailed to set up personalization database tables.")