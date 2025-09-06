# Supabase Migration Guide

This guide provides detailed instructions for migrating the Antidote platform database from your current PostgreSQL database to Supabase.

## Migration Overview

The migration process involves these key steps:
1. Backing up your current database data
2. Generating SQL scripts for import into Supabase
3. Creating tables and importing data in Supabase
4. Updating your application configuration
5. Verifying the migration

## Step 1: Prepare for Migration

### Create a Supabase Project

1. Go to the [Supabase dashboard](https://supabase.com/dashboard/projects)
2. Click "New Project"
3. Enter a name for your project (e.g., "Antidote-Production")
4. Set a secure database password (this will be needed for your connection string)
5. Choose a region closest to your users
6. Click "Create new project"

### Get Connection Details

From your Supabase project dashboard:
1. Click on "Settings" in the left sidebar
2. Click on "Database"
3. Under "Connection string", copy the "URI" value
4. Note that you'll need to replace the `[YOUR-PASSWORD]` placeholder with your actual password

## Step 2: Run Backup Scripts

We've created scripts to back up your current database and prepare it for migration:

```bash
# Create a JSON backup of your database
python database_backup.py

# Generate SQL import files from the backup
python generate_sql_from_backup.py
```

These scripts will create:
- JSON backup files in `database_backup/[timestamp]/`
- SQL import files in `sql_import/[timestamp]/`

## Step 3: Import Data into Supabase

### Option 1: All-in-One Import Script

1. In the Supabase dashboard, navigate to the "SQL Editor"
2. Click "New query"
3. Open the `sql_import/[timestamp]/import_to_supabase.sql` file in your local editor
4. Copy the entire contents and paste it into the Supabase SQL editor
5. Click "Run" to execute the script
6. Wait for the import to complete (this may take several minutes)

### Option 2: Import Tables Individually

If you prefer to import tables one by one (useful for troubleshooting):

1. In the Supabase SQL Editor, click "New query"
2. Start with the foundational tables:
   - `body_parts.sql`
   - `categories.sql`
   - `procedures.sql`
   - `doctors.sql`
3. Then continue with the remaining tables
4. Execute each SQL file in the order listed in the README

## Step 4: Update Application Configuration

After successfully importing your data, update your application to use the Supabase database:

1. Open your `.env` file
2. Update the `DATABASE_URL` environment variable with your Supabase connection string:

```
DATABASE_URL=postgresql://postgres:Ar8897365503@#@db.asgwdfirkanaaswobuj.supabase.co:5432/postgres
```

**Important Notes:**
- Replace the example values with your actual Supabase connection details
- If your password contains special characters like `@` or `#`, you may need to URL-encode them
- The format is `postgresql://[user]:[password]@[host]:[port]/[database]`

## Step 5: Verify Migration

### Check Database Connection

1. After updating your `.env` file, restart your application
2. Monitor the logs for any database connection errors
3. If you see connection errors, verify your connection string and network settings

### Verify Data Integrity

1. Check that all tables were created correctly
2. Verify row counts match your original database
3. Test key application features to ensure they work with the new database

## Troubleshooting

### Connection Issues

- **Problem**: Unable to connect to Supabase
- **Solution**: 
  - Ensure your password is correctly formatted in the connection string
  - Try URL-encoding special characters in your password
  - Check if your network allows outbound connections to Supabase

### Import Errors

- **Problem**: Foreign key constraint violations during import
- **Solution**: 
  - Import tables in the correct order (dependencies first)
  - Temporarily disable foreign key checks if needed

### Data Type Mismatches

- **Problem**: Column type mismatches between databases
- **Solution**:
  - Modify the SQL schema to match Supabase requirements
  - Consider converting problematic columns to more compatible types

## Support Resources

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Supabase Migration Guide](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [URL Encoding Tool](https://www.urlencoder.org/)

## Post-Migration Steps

After successfully migrating to Supabase:

1. Set up automated backups in Supabase
2. Update any database credentials in your CI/CD pipelines
3. Monitor database performance and make adjustments as needed
4. Consider implementing connection pooling for production workloads