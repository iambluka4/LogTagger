import os
import sys
import psycopg2
from tabulate import tabulate

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config

def get_db_connection():
    """Get database connection from Flask app config"""
    config = get_config('development')
    db_uri = config.SQLALCHEMY_DATABASE_URI
    
    if not db_uri.startswith('postgresql://'):
        print(f"Unsupported database URI: {db_uri}")
        sys.exit(1)
        
    # Parse connection string
    db_uri = db_uri[len('postgresql://'):]
    
    if '@' in db_uri:
        credentials, host_db = db_uri.split('@', 1)
    else:
        credentials, host_db = '', db_uri
    
    if ':' in credentials:
        user, password = credentials.split(':', 1)
    else:
        user, password = credentials, ''
    
    if '/' in host_db:
        host_port, database = host_db.split('/', 1)
    else:
        host_port, database = host_db, ''
    
    if ':' in host_port:
        host, port = host_port.split(':', 1)
        port = int(port)
    else:
        host, port = host_port, 5432
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        print(f"Successfully connected to database: {database}")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def list_tables(conn):
    """List all tables in the database"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cur.fetchall()]
        
        if not tables:
            print("No tables found in database.")
        else:
            print(f"\nFound {len(tables)} tables in database:")
            print(", ".join(tables))
        
        return tables

def inspect_table(conn, table_name):
    """Inspect a table's columns and their types"""
    with conn.cursor() as cur:
        # Get column information
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = []
        for row in cur.fetchall():
            col_name, data_type, max_length, nullable = row
            if max_length:
                data_type = f"{data_type}({max_length})"
            nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
            columns.append([col_name, data_type, nullable_str])
        
        # Get row count
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cur.fetchone()[0]
        
        print(f"\n== Table: {table_name} ({row_count} rows) ==")
        print(tabulate(columns, headers=["Column", "Type", "Nullable"]))
        
        # If it's the users table, show usernames (but not passwords)
        if table_name == 'users' and row_count > 0:
            cur.execute("SELECT id, username, role FROM users")
            users = cur.fetchall()
            print("\nUsers in database:")
            print(tabulate(users, headers=["ID", "Username", "Role"]))

def main():
    """Main function to inspect database"""
    conn = get_db_connection()
    tables = list_tables(conn)
    
    for table in tables:
        inspect_table(conn, table)
    
    conn.close()
    print("\nDatabase inspection complete!")

if __name__ == "__main__":
    main()
