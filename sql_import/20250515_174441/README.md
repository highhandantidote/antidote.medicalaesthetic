# Supabase Import SQL Files

This directory contains SQL files for importing your database into Supabase.

## Files

- `*.sql` - Individual SQL files for each table
- `import_to_supabase.sql` - A single file containing all SQL in the correct order

## Import Instructions

### Option 1: Use the all-in-one script

1. Open the Supabase dashboard and navigate to the SQL Editor
2. Open the `import_to_supabase.sql` file
3. Copy and paste the contents into the SQL Editor
4. Run the script to import all tables and data

### Option 2: Import tables individually

If you prefer to import tables one at a time:

1. Start with the core tables in this order:
   - users.sql
   - body_parts.sql
   - categories.sql
   - procedures.sql
   - doctors.sql
   - doctor_procedures.sql
2. Then import the remaining tables

## After Import

Update your `.env` file with the Supabase connection string:

```
DATABASE_URL=postgresql://postgres:{YOUR-PASSWORD}@db.XXXXXXXXXXXXXXXX.supabase.co:5432/postgres
```

Replace `{YOUR-PASSWORD}` with your Supabase password and `XXXXXXXXXXXXXXXX` with your Supabase project ID.

## Troubleshooting

If you encounter errors during import:

1. Foreign key violations: Import tables in the correct order (dependencies first)
2. Data format issues: Check and modify the SQL as needed
3. Connection problems: Make sure your Supabase project is properly configured

## Support

For further assistance, refer to the Supabase documentation or contact their support team.
