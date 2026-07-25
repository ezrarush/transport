import sqlite3
import pandas as pd

# 1. Establish a connection to the SQLite database file
# Ensure the file 'transportation_accidents.db' is in your working directory
db_path = "transportation_accidents.db"
conn = sqlite3.connect(db_path)

try:
    print("--- 1. Crashes Table ---")
    # Read the entire crashes table
    df_crashes = pd.read_sql_query("SELECT * FROM crashes;", conn)
    print(df_crashes.head())
    
    print("\n--- 2. Vehicles Table ---")
    # Read the entire vehicles table
    df_vehicles = pd.read_sql_query("SELECT * FROM vehicles;", conn)
    print(df_vehicles.head())
    
    print("\n--- 3. Relational Join Example ---")
    # Execute a JOIN query to find the worst injuries by vehicle type
    join_query = """
        SELECT 
            v.vehicle_type,
            p.injury_severity_kabco,
            COUNT(p.person_id) as total_people
        FROM people p
        JOIN vehicles v ON p.vehicle_id = v.vehicle_id
        GROUP BY v.vehicle_type, p.injury_severity_kabco
        ORDER BY total_people DESC;
    """
    df_analysis = pd.read_sql_query(join_query, conn)
    print(df_analysis)

finally:
    # 2. Always close the database connection when finished
    conn.close()
    print("\nDatabase connection closed successfully.")
