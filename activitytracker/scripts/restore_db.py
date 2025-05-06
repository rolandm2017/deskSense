import subprocess
import os

def restore_database(
    db_name,
    backup_file,
    host="localhost",
    port="5432",
    username="postgres"
):
    try:
        # Drop the existing database (optional, but ensures clean restore)
        subprocess.run([
            'dropdb',
            '-h', host,
            '-p', port,
            '-U', username,
            db_name
        ], check=True)
        
        print(f"Dropped existing database: {db_name}")
        
        # Create a fresh database
        subprocess.run([
            'createdb',
            '-h', host,
            '-p', port,
            '-U', username,
            db_name
        ], check=True)
        
        print(f"Created fresh database: {db_name}")
        
        # Restore from backup
        subprocess.run([
            'pg_restore',
            '-h', host,
            '-p', port,
            '-U', username,
            '-d', db_name,
            '-v',
            backup_file
        ], check=True)
        
        print(f"Database restored successfully from: {backup_file}")
        
    except subprocess.CalledProcessError as e:
        print(f"Restore failed: {e}")
        raise

# Using the exact path with .sql extension as you confirmed
backup_file = os.path.join(".", "backup_deskSense_20250503_001944.sql")

# For debugging, let's add a print statement to show the full path
print(f"Looking for backup file at: {os.path.abspath(backup_file)}")

# Make sure the backup file exists
if not os.path.exists(backup_file):
    print(f"Error: Backup file not found at {backup_file}")
else:
    # First parameter is database name, second is backup file path
    restore_database("deskSense", backup_file)