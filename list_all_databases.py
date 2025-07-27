#!/usr/bin/env python3
"""
List all PostgreSQL databases on this machine
"""
import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_databases():
    """List all databases and their connection details"""
    
    # Known database connections from the project
    connections = [
        {
            "name": "sports_data",
            "url": "postgresql://sports_user:sports_secure_2025@localhost:5432/sports_data",
            "description": "Main sports database (Baseball analytics data)"
        },
        {
            "name": "statedge", 
            "url": "postgresql://statedge_user:statedge_pass@localhost:15432/statedge",
            "description": "StatEdge MCP database (Read-only access)"
        },
        {
            "name": "users_data",
            "url": "postgresql://user_admin:user_secure_2025@localhost:5433/users_data", 
            "description": "User management database"
        }
    ]
    
    print("🗄️  PostgreSQL Databases on this machine:")
    print("=" * 60)
    
    for conn_info in connections:
        print(f"\n📊 {conn_info['name'].upper()} DATABASE")
        print(f"   Description: {conn_info['description']}")
        print(f"   Connection: {conn_info['url']}")
        
        try:
            conn = psycopg2.connect(conn_info['url'])
            cursor = conn.cursor()
            
            # Get database name
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()[0]
            
            # Get all tables
            cursor.execute("""
                SELECT table_name, 
                       (SELECT COUNT(*) FROM information_schema.columns 
                        WHERE table_name = t.table_name) as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            print(f"   Status: ✅ Connected")
            print(f"   Tables ({len(tables)}):")
            
            for table_name, col_count in tables:
                # Get row count for each table
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    row_count = cursor.fetchone()[0]
                    print(f"     - {table_name} ({col_count} cols, {row_count:,} rows)")
                except Exception as e:
                    print(f"     - {table_name} ({col_count} cols, error counting rows)")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"   Status: ❌ Connection failed - {e}")
    
    print("\n" + "=" * 60)
    print("💡 MLB tables were created in both:")
    print("   • statedge database (port 15432) - FIRST ATTEMPT")  
    print("   • sports_data database (port 5432) - CORRECT LOCATION")

if __name__ == "__main__":
    list_databases()