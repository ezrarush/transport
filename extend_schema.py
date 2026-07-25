# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "openpyxl",
# ]
# ///

import sqlite3
import os

DB_PATH = "transportation_accidents.db"

def build_extended_schema():
    # Clear the old database instance if it exists to establish fresh relations
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    print(f"--- 1. Initializing Database Structure at '{DB_PATH}' ---")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Enforce strict cascading foreign key constraints dynamically inside SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Table A: Core Crashes Element 
    cursor.execute("""
        CREATE TABLE crashes (
            crash_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            weather_condition TEXT NOT NULL,
            speed_limit INTEGER NOT NULL,
            roadway_type TEXT
        );
    """)
    
    # Table B: Autonomous driving scale lookup dictionary 
    cursor.execute("""
        CREATE TABLE dim_autonomy_levels (
            autonomy_level INTEGER PRIMARY KEY CHECK(autonomy_level BETWEEN 0 AND 5),
            sae_name TEXT NOT NULL,
            description TEXT
        );
    """)
    
    # Table C: Standard mechanical failure taxonomy definitions
    cursor.execute("""
        CREATE TABLE dim_mechanical_failures (
            failure_code TEXT PRIMARY KEY,
            failure_category TEXT NOT NULL,
            description TEXT
        );
    """)

    # Table D: System Vehicles (normalized to point to the autonomy level keys)
    cursor.execute("""
        CREATE TABLE vehicles (
            vehicle_id TEXT PRIMARY KEY,
            crash_id TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            autonomous_level INTEGER NOT NULL,
            FOREIGN KEY (crash_id) REFERENCES crashes(crash_id) ON DELETE CASCADE,
            FOREIGN KEY (autonomous_level) REFERENCES dim_autonomy_levels(autonomy_level)
        );
    """)
    
    # Table E: Junction table tracking complex multi-failure accidents
    cursor.execute("""
        CREATE TABLE vehicle_failures_bridge (
            vehicle_id TEXT NOT NULL,
            failure_code TEXT NOT NULL,
            PRIMARY KEY (vehicle_id, failure_code),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
            FOREIGN KEY (failure_code) REFERENCES dim_mechanical_failures(failure_code)
        );
    """)

    # Table F: Normalized People and Injury tracking table
    cursor.execute("""
        CREATE TABLE people (
            person_id TEXT PRIMARY KEY,
            crash_id TEXT NOT NULL,
            vehicle_id TEXT, -- Nullable to support non-motorists (e.g. pedestrians, cyclists)
            role TEXT CHECK(role IN ('Driver', 'Occupant', 'Pedestrian', 'Cyclist')),
            age INTEGER,
            gender TEXT,
            injury_severity_kabco TEXT CHECK(injury_severity_kabco IN ('K', 'A', 'B', 'C', 'O')),
            FOREIGN KEY (crash_id) REFERENCES crashes(crash_id) ON DELETE CASCADE,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE SET NULL
        );
    """)

    # =====================================================================
    # STEP 2: CREATING THE STORED DEMOGRAPHIC ANALYSIS VIEW
    # =====================================================================
    print("--- 2. Compiling Stored SQL View: view_demographic_safety_summary ---")
    cursor.execute("""
        CREATE VIEW view_demographic_safety_summary AS
        SELECT 
            p.person_id,
            p.role,
            p.age,
            CASE 
                WHEN p.age < 18 THEN 'Under 18'
                WHEN p.age BETWEEN 18 AND 64 THEN '18-64'
                WHEN p.age >= 65 THEN '65+'
                ELSE 'Unknown'
            END as age_band,
            p.gender,
            p.injury_severity_kabco as injury_severity,
            v.vehicle_type,
            COALESCE(a.sae_name, 'Non-Motorist (No Vehicle)') as vehicle_autonomy_tier,
            c.weather_condition,
            c.speed_limit
        FROM people p
        LEFT JOIN vehicles v ON p.vehicle_id = v.vehicle_id
        LEFT JOIN dim_autonomy_levels a ON v.autonomous_level = a.autonomy_level
        LEFT JOIN crashes c ON p.crash_id = c.crash_id;
    """)

    # =====================================================================
    # SEED DATA GENERATION & INSERTION
    # =====================================================================
    print("--- 3. Seeding Dimensions ---")
    
    autonomy_data = [
        (0, "No Driving Automation", "Manual driver controls all operations."),
        (1, "Driver Assistance", "Single automated system helper present."),
        (2, "Partial Driving Automation", "Automated steering and acceleration execution."),
        (3, "Conditional Driving Automation", "System drives but operator handles emergency calls."),
        (4, "High Driving Automation", "Vehicle drives unaided inside geofenced areas."),
        (5, "Full Driving Automation", "Complete vehicle independence under all constraints.")
    ]
    cursor.executemany("INSERT INTO dim_autonomy_levels VALUES (?, ?, ?);", autonomy_data)
    
    failure_data = [
        ("BRK_FAIL", "Braking System", "Complete hydraulic fluid loss or caliper seizure."),
        ("TYR_BLOW", "Suspension & Tires", "Sudden catastrophic structural tire failure."),
        ("STR_LOSS", "Steering System", "Mechanical linkage breakage or sudden power loss."),
        ("SEN_BLND", "AV Sensors", "Camera obstruction or LiDAR system disconnect."),
        ("SFT_CRSH", "AV Software", "Core operating module freeze or fatal error.")
    ]
    cursor.executemany("INSERT INTO dim_mechanical_failures VALUES (?, ?, ?);", failure_data)
    
    print("--- 4. Seeding Incidents, Fleet Units, and Failure Bridges ---")
    
    crashes = [
        ("CRASH_001", "2026-03-12 08:32:00", "Rain", 65, "Interstate"),
        ("CRASH_002", "2026-05-19 14:15:00", "Clear", 35, "Urban Arterial"),
        ("CRASH_003", "2026-07-04 22:45:00", "Snow", 45, "Rural Highway")
    ]
    cursor.executemany("INSERT INTO crashes VALUES (?, ?, ?, ?, ?);", crashes)
    
    vehicles = [
        ("VEH_101", "CRASH_001", "Commercial Truck", 4), # Level 4 Autonomous Freight Truck
        ("VEH_102", "CRASH_001", "Passenger Car", 0),    # Standard vehicle hit by truck
        ("VEH_201", "CRASH_002", "Transit Bus", 2),       # Level 2 Autonomy Bus
        ("VEH_301", "CRASH_003", "Passenger Car", 0)     # Standard vehicle
    ]
    cursor.executemany("INSERT INTO vehicles VALUES (?, ?, ?, ?);", vehicles)
    
    failures_bridge = [
        ("VEH_101", "SEN_BLND"),
        ("VEH_101", "BRK_FAIL"),
        ("VEH_201", "STR_LOSS"),
        ("VEH_301", "TYR_BLOW")
    ]
    cursor.executemany("INSERT INTO vehicle_failures_bridge VALUES (?, ?);", failures_bridge)
    
    print("--- 5. Seeding Injury Matrix Metrics ---")
    
    people_data = [
        # CRASH 001: Level 4 Autonomous Freight truck collides with standard vehicle
        ("PER_001", "CRASH_001", "VEH_101", "Driver", 42, "M", "O"),      # 18-64 Tier
        ("PER_002", "CRASH_001", "VEH_102", "Driver", 28, "F", "A"),      # 18-64 Tier
        ("PER_003", "CRASH_001", "VEH_102", "Occupant", 6, "M", "B"),    # Under 18 Tier
        
        # CRASH 002: Level 2 Transit bus sequence involving a pedestrian
        ("PER_004", "CRASH_002", "VEH_201", "Driver", 55, "M", "O"),      # 18-64 Tier
        ("PER_005", "CRASH_002", "VEH_201", "Occupant", 19, "F", "C"),    # 18-64 Tier
        ("PER_006", "CRASH_002", None, "Pedestrian", 34, "F", "K"),       # 18-64 Tier
        
        # CRASH 003: High-speed passenger car blowout
        ("PER_007", "CRASH_003", "VEH_301", "Driver", 68, "M", "B")       # 65+ Tier
    ]
    cursor.executemany("INSERT INTO people VALUES (?, ?, ?, ?, ?, ?, ?);", people_data)
    
    conn.commit()
    conn.close()
    print("Database finalized successfully! Stored view compiled and ready for querying.")

if __name__ == "__main__":
    build_extended_schema()
