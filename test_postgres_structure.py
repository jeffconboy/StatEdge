#!/usr/bin/env python3
"""
Test script to get PostgreSQL table structure via MCP
"""

import subprocess
import sys

def run_postgres_query(query):
    """Run a PostgreSQL query using claude MCP"""
    try:
        # Use the MCP postgres query through claude command
        cmd = ["claude", "mcp", "postgres", "query", query]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout, result.stderr
    except Exception as e:
        return None, str(e)

def main():
    tables = ['mlb_players', 'fangraphs_batting', 'fangraphs_pitching', 'statcast']
    
    for table in tables:
        print(f"\n{'='*60}")
        print(f"TABLE: {table}")
        print(f"{'='*60}")
        
        # Get column information
        query = f"""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = '{table}' 
        ORDER BY ordinal_position;
        """
        
        stdout, stderr = run_postgres_query(query)
        
        if stderr:
            print(f"Error querying {table}: {stderr}")
        elif stdout:
            print(stdout)
        else:
            print(f"No results for table {table}")
            
        # Also try to get a sample row
        sample_query = f"SELECT * FROM {table} LIMIT 1;"
        stdout, stderr = run_postgres_query(sample_query)
        
        if stdout and not stderr:
            print(f"\nSample row from {table}:")
            print(stdout[:500] + "..." if len(stdout) > 500 else stdout)

if __name__ == "__main__":
    main()