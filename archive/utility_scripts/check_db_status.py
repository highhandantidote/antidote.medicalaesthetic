#!/usr/bin/env python3
"""
Check database status and verify seeding progress for the Antidote platform.

This script provides detailed reporting on:
1. Current procedure counts by body part
2. Thread count and keyword distribution
3. Database health (locks, active queries, connection pool)
"""
import os
import sys
import psycopg2
import logging
from datetime import datetime

# Configure logging
LOG_FILE = f"db_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def connect_to_db():
    """Connect to the PostgreSQL database."""
    logger.info("Connecting to database...")
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = True  # Read-only operations
        logger.info("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to the database: {str(e)}")
        raise

def check_procedure_counts(conn):
    """Check procedure counts by body part."""
    logger.info("Checking procedure counts...")
    
    try:
        with conn.cursor() as cur:
            # Total procedure count
            cur.execute("SELECT COUNT(*) FROM procedures")
            total_count = cur.fetchone()[0]
            logger.info(f"Total procedures: {total_count}/117")
            
            # Procedure counts by body part
            cur.execute("SELECT body_part, COUNT(*) FROM procedures GROUP BY body_part ORDER BY COUNT(*) DESC")
            body_part_counts = cur.fetchall()
            
            if body_part_counts:
                logger.info("Procedure distribution by body part:")
                for body_part, count in body_part_counts:
                    logger.info(f"  - {body_part}: {count}")
            else:
                logger.warning("No procedures found")
            
            # Check specific procedure IDs (1, 13, 50)
            target_ids = [1, 13, 50]
            for proc_id in target_ids:
                cur.execute("SELECT id, procedure_name, body_part FROM procedures WHERE id = %s", (proc_id,))
                result = cur.fetchone()
                if result:
                    logger.info(f"  - Procedure ID {proc_id}: {result[1]} (Body part: {result[2]})")
                else:
                    logger.info(f"  - Procedure ID {proc_id}: Not found")
            
            return total_count, body_part_counts
    except Exception as e:
        logger.error(f"Error checking procedure counts: {str(e)}")
        raise

def check_thread_counts(conn):
    """Check thread counts and keyword distribution."""
    logger.info("Checking thread counts...")
    
    try:
        with conn.cursor() as cur:
            # Total thread count
            cur.execute("SELECT COUNT(*) FROM threads")
            total_count = cur.fetchone()[0]
            logger.info(f"Total threads: {total_count}/6")
            
            if total_count > 0:
                # Thread info
                cur.execute("""
                    SELECT id, title, procedure_id, keywords 
                    FROM threads 
                    LIMIT 6
                """)
                thread_info = cur.fetchall()
                
                logger.info("Thread information:")
                for thread in thread_info:
                    thread_id, title, procedure_id, keywords = thread
                    logger.info(f"  - Thread ID {thread_id}: {title}")
                    logger.info(f"    Keywords: {keywords}")
                    
                    # Get procedure info for this thread
                    if procedure_id:
                        cur.execute("""
                            SELECT procedure_name, body_part 
                            FROM procedures 
                            WHERE id = %s
                        """, (procedure_id,))
                        proc_info = cur.fetchone()
                        if proc_info:
                            logger.info(f"    Procedure: {proc_info[0]} (Body part: {proc_info[1]})")
                
                # Thread distribution by body part
                cur.execute("""
                    SELECT p.body_part, COUNT(*) 
                    FROM threads t
                    JOIN procedures p ON t.procedure_id = p.id
                    GROUP BY p.body_part
                    ORDER BY COUNT(*) DESC
                """)
                body_part_counts = cur.fetchall()
                
                if body_part_counts:
                    logger.info("Thread distribution by body part:")
                    for body_part, count in body_part_counts:
                        logger.info(f"  - {body_part}: {count}")
                
                # Check for 'cost' keyword
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM threads 
                    WHERE keywords::text LIKE '%cost%'
                """)
                cost_count = cur.fetchone()[0]
                logger.info(f"Threads with 'cost' keyword: {cost_count}/2")
            
            return total_count
    except Exception as e:
        logger.error(f"Error checking thread counts: {str(e)}")
        raise

def check_database_health(conn):
    """Check database health (locks, active queries, connection pool)."""
    logger.info("Checking database health...")
    
    try:
        with conn.cursor() as cur:
            # Check version
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            logger.info(f"PostgreSQL version: {version}")
            
            # Check active connections
            cur.execute("SELECT COUNT(*) FROM pg_stat_activity")
            connection_count = cur.fetchone()[0]
            logger.info(f"Active connections: {connection_count}")
            
            # Check for locks
            cur.execute("""
                SELECT COUNT(*) 
                FROM pg_locks l
                JOIN pg_stat_activity a ON l.pid = a.pid
                WHERE l.granted = false
            """)
            lock_count = cur.fetchone()[0]
            if lock_count > 0:
                logger.warning(f"Found {lock_count} waiting locks")
                
                # Show details of locked queries
                cur.execute("""
                    SELECT a.pid, a.usename, a.query, a.query_start, a.state
                    FROM pg_locks l
                    JOIN pg_stat_activity a ON l.pid = a.pid
                    WHERE l.granted = false
                """)
                lock_details = cur.fetchall()
                for lock in lock_details:
                    logger.warning(f"  - PID {lock[0]} ({lock[1]}): {lock[4]} since {lock[3]}")
                    logger.warning(f"    Query: {lock[2]}")
            else:
                logger.info("No waiting locks found")
            
            # Check long-running queries (over 30 seconds)
            cur.execute("""
                SELECT pid, usename, query, query_start, state, now() - query_start as duration
                FROM pg_stat_activity
                WHERE state = 'active'
                  AND now() - query_start > interval '30 seconds'
                  AND query NOT LIKE '%pg_stat_activity%'
                ORDER BY duration DESC
            """)
            long_queries = cur.fetchall()
            if long_queries:
                logger.warning(f"Found {len(long_queries)} long-running queries")
                for query in long_queries:
                    logger.warning(f"  - PID {query[0]} ({query[1]}): running for {query[5]}")
                    logger.warning(f"    Query: {query[2]}")
            else:
                logger.info("No long-running queries found")
            
            # Check table sizes
            cur.execute("""
                SELECT relname as table_name,
                       pg_size_pretty(pg_total_relation_size(relid)) as total_size,
                       pg_size_pretty(pg_relation_size(relid)) as table_size,
                       pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as index_size
                FROM pg_catalog.pg_statio_user_tables
                ORDER BY pg_total_relation_size(relid) DESC
                LIMIT 5
            """)
            table_sizes = cur.fetchall()
            logger.info("Top 5 table sizes:")
            for table in table_sizes:
                logger.info(f"  - {table[0]}: {table[1]} (Table: {table[2]}, Indexes: {table[3]})")
    except Exception as e:
        logger.error(f"Error checking database health: {str(e)}")
        raise

def generate_summary(proc_count, thread_count):
    """Generate a summary report in Markdown format."""
    logger.info("Generating summary report...")
    
    summary_file = "db_status_summary.md"
    try:
        with open(summary_file, "w") as f:
            f.write("# Antidote Platform Database Status\n\n")
            f.write(f"**Report generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Seeding Status\n\n")
            f.write(f"- Procedures: {proc_count}/117 ({proc_count/117*100:.1f}%)\n")
            f.write(f"- Community Threads: {thread_count}/6 ({thread_count/6*100:.1f}%)\n\n")
            
            if proc_count >= 117 and thread_count >= 6:
                status = "✅ Complete"
            elif proc_count > 0 and thread_count > 0:
                status = "🟨 Partial"
            else:
                status = "❌ Incomplete"
            
            f.write(f"**Overall Status:** {status}\n\n")
            
            f.write("## Next Steps\n\n")
            if proc_count < 117:
                f.write("1. Complete procedure seeding\n")
            if thread_count < 6:
                f.write(f"{'2' if proc_count < 117 else '1'}. Complete community thread seeding\n")
            
            if proc_count >= 117 and thread_count >= 6:
                f.write("1. Verify community analytics dashboard functionality\n")
                f.write("2. Test real-time updates via `/api/community/trends`\n")
                f.write("3. Run performance tests\n")
            
            f.write(f"\n\n*For detailed information, see the full log at: {LOG_FILE}*\n")
        
        logger.info(f"Summary report generated: {summary_file}")
    except Exception as e:
        logger.error(f"Error generating summary report: {str(e)}")

def main():
    """Run the database status check."""
    logger.info("Starting database status check...")
    
    try:
        conn = connect_to_db()
        
        proc_count, _ = check_procedure_counts(conn)
        thread_count = check_thread_counts(conn)
        check_database_health(conn)
        
        conn.close()
        
        generate_summary(proc_count, thread_count)
        
        logger.info("Database status check completed")
        logger.info(f"Full log available at: {LOG_FILE}")
        
        return 0
    except Exception as e:
        logger.error(f"Error checking database status: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())