# Database Migration to Supabase

## Overview

This package provides tools to migrate your existing database to Supabase while ensuring data integrity.

## Files Included

- **SUPABASE_MIGRATION_GUIDE.md** - Comprehensive step-by-step guide
- **check_pre_migration.py** - Pre-migration database analysis
- **backup_database.py** - Database backup tool
- **migrate_to_supabase.py** - Core data migration script
- **update_db_references.py** - Application reference updater
- **verify_post_migration.py** - Post-migration verification
- **run_supabase_migration.py** - Master migration coordinator

## Quick Start

1. **Create a Supabase Project**:
   - Go to [Supabase.com](https://supabase.com/) and create a new project
   - Get your database connection string from Project Settings > Database

2. **Set Environment Variables**:
   ```bash
   # Save current connection string
   export SOURCE_DATABASE_URL=$DATABASE_URL
   
   # Set new Supabase connection string
   export DATABASE_URL="your-supabase-connection-string"
   ```

3. **Run Migration**:
   ```bash
   # Pre-migration check
   python check_pre_migration.py
   
   # Full migration process
   python run_supabase_migration.py
   
   # Verify migration
   python verify_post_migration.py
   ```

## Safety Features

- **Automatic backups** before any migration steps
- **Data verification** comparing source and target databases
- **Rollback capability** if issues are encountered
- **Detailed logs** for troubleshooting

## Notes

- The migration process may take several minutes depending on the size of your database
- Internet connectivity is required throughout the migration
- Application restart may be required after migration

## Support

If you encounter any issues or have questions, please refer to the SUPABASE_MIGRATION_GUIDE.md file for detailed troubleshooting steps.

---

Copyright © 2025 | Visit [Supabase Documentation](https://supabase.com/docs) for more information.