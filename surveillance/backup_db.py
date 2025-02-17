import subprocess
from datetime import datetime


def backup_database(
    db_name,
    backup_path,
    host="localhost",
    port="5432",
    username="postgres"
):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{backup_path}/backup_{db_name}_{timestamp}.sql"

    try:
        # Create backup
        subprocess.run([
            'pg_dump',
            '-h', host,
            '-p', port,
            '-U', username,
            '-F', 'c',  # Custom format (compressed)
            '-b',  # Include large objects
            '-v',  # Verbose
            '-f', backup_file,
            db_name
        ], check=True)
        print(f"Backup completed successfully: {backup_file}")
        return backup_file
    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e}")
        raise


backup_database("deskSense", ".")
