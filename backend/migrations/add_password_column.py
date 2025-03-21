import os
import sys
import psycopg2
import configparser

# Add the parent directory to path to import app configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config

def add_password_column():
    """Add the password column to the users table if it doesn't exist."""
    try:
        # Get database configuration from the same config used by the Flask app
        config = get_config('development')
        db_uri = config.SQLALCHEMY_DATABASE_URI
        
        # Parse the SQLAlchemy URI to extract connection parameters
        # Format is typically: postgresql://username:password@host:port/database
        print(f"Using database URI: {db_uri}")
        
        if db_uri.startswith('postgresql://'):
            # Remove the postgresql:// prefix
            db_uri = db_uri[len('postgresql://'):]
            
            # Split credentials from host/database
            if '@' in db_uri:
                credentials, host_db = db_uri.split('@', 1)
            else:
                credentials, host_db = '', db_uri
            
            # Parse credentials
            if ':' in credentials:
                user, password = credentials.split(':', 1)
            else:
                user, password = credentials, ''
            
            # Parse host/database
            if '/' in host_db:
                host_port, database = host_db.split('/', 1)
            else:
                host_port, database = host_db, ''
            
            # Parse host/port
            if ':' in host_port:
                host, port = host_port.split(':', 1)
                port = int(port)
            else:
                host, port = host_port, 5432
            
            # Connect to the database
            print(f"Connecting to PostgreSQL on {host}:{port} as {user}...")
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            )
            
            cur = conn.cursor()
            
            # Check if the column exists
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='password'")
            column_exists = cur.fetchone() is not None
            
            if not column_exists:
                print("Adding 'password' column to users table...")
                cur.execute("ALTER TABLE users ADD COLUMN password VARCHAR(255)")
                conn.commit()
                print("Added 'password' column successfully")
            else:
                print("Password column already exists in users table")
                
            # Close the database connection
            cur.close()
            conn.close()
            print("Database connection closed.")
        else:
            print(f"Unsupported database URI format: {db_uri}")
            sys.exit(1)
        
    except Exception as e:
        print(f"Error: {e}")
        print("Hint: Make sure your database credentials are correct in config.py")
        sys.exit(1)

if __name__ == "__main__":
    add_password_column()
