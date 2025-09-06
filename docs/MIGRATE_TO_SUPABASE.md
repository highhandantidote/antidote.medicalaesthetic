# Migrating to Supabase

This document provides step-by-step instructions for migrating the Antidote database from PostgreSQL to Supabase.

## Prerequisites

1. A Supabase account and project
2. Access to the Supabase PostgreSQL connection string
3. Backup of your current database

## Step 1: Get Your Supabase Connection String

1. Log in to the [Supabase dashboard](https://supabase.com/dashboard/projects)
2. Create a new project if you haven't already
3. Once in the project page, click the "Connect" button on the top toolbar
4. Copy the URI value under "Connection string" -> "Transaction pooler"
5. Replace `[YOUR-PASSWORD]` with the database password you set for the project

Example connection string:
```
postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijklm.supabase.co:6543/postgres?pgbouncer=true
```

## Step 2: Update Environment Variables

Update your `.env` file to use the Supabase connection string:

```
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijklm.supabase.co:6543/postgres?pgbouncer=true
SUPABASE_DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijklm.supabase.co:6543/postgres?pgbouncer=true
```

## Step 3: Export Your Current Database

We've already prepared several scripts to help with the migration:

1. **Database Backup**: Run `python database_backup.py` to create a full backup of your database in JSON format
2. **SQL Generation**: Run `python generate_sql_from_backup.py` to create SQL scripts from your backup files

These steps have already been completed and the results are stored in the `database_backup` and `sql_import` directories.

## Step 4: Import Data to Supabase

### Option 1: Direct Import (Recommended)

If your Supabase project allows direct connections from your environment:

1. Run the migration script:

```bash
python migrate_to_supabase.py
```

This script will:
- Connect to your Supabase PostgreSQL database
- Create all necessary tables
- Import all data from your backup files

### Option 2: Manual Import

If you encounter connection issues with Option 1:

1. Use the Supabase SQL Editor to run the scripts in the `sql_import` directory
2. Run the scripts in this order:
   - schema.sql (creates tables)
   - data_[table_name].sql (imports data for each table)

## Step 5: Verify Migration

After migration, verify that all your data has been successfully transferred:

1. Run `python verify_supabase_connection.py` to check the connection
2. Check that all tables have been created correctly
3. Verify record counts match between your original database and Supabase

```sql
-- Run this query in both databases and compare results
SELECT 
  (SELECT COUNT(*) FROM users) AS user_count,
  (SELECT COUNT(*) FROM procedures) AS procedure_count,
  (SELECT COUNT(*) FROM community) AS community_count,
  (SELECT COUNT(*) FROM community_replies) AS reply_count;
```

## Step 6: Update Application Configuration

After verifying the migration was successful:

1. Update your application code to use the Supabase connection string
2. Test all database-related functionality

## Troubleshooting

### Connection Issues

If you encounter connection issues with Supabase:

1. Check that your IP is allowed in the Supabase project settings
2. Verify that your password does not contain special characters that need URL encoding
3. Try connecting with psql to isolate application-specific issues:

```bash
psql postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijklm.supabase.co:6543/postgres?pgbouncer=true
```

### Data Import Issues

If you encounter issues with data import:

1. Check for unique constraint violations
2. Ensure foreign key dependencies are satisfied
3. Import tables in the correct order (referenced tables first)

## Contact Support

If you continue to experience issues, contact Supabase support or refer to their documentation:

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase GitHub](https://github.com/supabase/supabase)
- [Supabase Discord](https://discord.supabase.com)