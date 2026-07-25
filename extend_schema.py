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
    # If database already exists, remove it to build a clean relational structure
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    print(f"--- 1. Creating Database & Schema Structure at '{DB_PATH}' ---")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Enable explicit runtime foreign key constraints validation in SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Create Table: Core Crashes Element
    cursor.execute("""
        CREATE TABLE crashes (
            crash_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            weather_condition TEXT NOT NULL,
            speed_limit INTEGER NOT NULL,
            roadway_type TEXT
        );
    """)
    
    # Create Table: Autonomous Level Dimensions Catalog (SAE Standards J3016)
    cursor.execute("""
        CREATE TABLE dim_autonomy_levels (
            autonomy_level INTEGER PRIMARY KEY CHECK(autonomy_level BETWEEN 0 AND 5),
            sae_name TEXT NOT NULL,
            description TEXT
        );
    """)
    
    # Create Table: Standard Mechanical Failure Classification Category Catalog
    cursor.execute("""
        CREATE TABLE dim_mechanical_failures (
            failure_code TEXT PRIMARY KEY,
            failure_category TEXT NOT NULL,
            description TEXT
        );
    """)

    # Create Table: Extended Vehicles Track Layer
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
    
    # Create Junction Table: Many-to-Many Bridge tracking multiple vehicle failures per sequence
    cursor.execute("""
        CREATE TABLE vehicle_failures_bridge (
            vehicle_id TEXT NOT NULL,
            failure_code TEXT NOT NULL,
            PRIMARY KEY (vehicle_id, failure_code),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
            FOREIGN KEY (failure_code) REFERENCES dim_mechanical_failures(failure_code)
        );
    """)

    # =====================================================================
    # SEED DATA INJECTION
    # =====================================================================
    print("--- 2. Seeding Lookup Dimension Tables ---")
    
    # Seed Autonomy Categories
    autonomy_data = [
        (0, "No Driving Automation", "Manual driver controls all steering, braking, and throttle work."),
        (1, "Driver Assistance", "Vehicle features single automated system (e.g., adaptive cruise controls)."),
        (2, "Partial Driving Automation", "Vehicle controls steering and speed simultaneously (e.g., lane centering)."),
        (3, "Conditional Driving Automation", "System monitors driving environment, pilot must intervene on demand."),
        (4, "High Driving Automation", "Vehicle drives completely unaided within geofenced parameters."),
        (5, "Full Driving Automation", "Complete automation across all environment layers, steering wheel optional.")
    ]
    cursor.executemany("INSERT INTO dim_autonomy_levels VALUES (?, ?, ?);", autonomy_data)
    
    # Seed Mechanical Failures Category Records
    failure_data = [
        ("BRK_FAIL", "Braking System", "Complete hydraulic pressure loss or brake pad lockup."),
        ("TYR_BLOW", "Suspension & Tires", "Sudden catastrophic tire sidewall blowout event."),
        ("STR_LOSS", "Steering System", "Mechanical linkage failure or power steering fluid leak drop."),
        ("SEN_BLND", "AV Sensors", "Autonomous camera obstruction or LiDAR feedback error freeze."),
        ("SFT_CRSH", "AV Software", "System compute lockup forcing automated fallback procedure failure.")
    ]
    cursor.executemany("INSERT INTO dim_mechanical_failures VALUES (?, ?, ?);", failure_data)
    
    print("--- 3. Injecting Sample Accident & Autonomous Vehicle Crash Rows ---")
    
    # Seed crashes (Crash records that align with our speed map indexes)
    crashes = [
        ("CRASH_001", "2026-03-12 08:32:00", "Rain", 65, "Interstate"),
        ("CRASH_002", "2026-05-19 14:15:00", "Clear", 35, "Urban Arterial"),
        ("CRASH_003", "2026-07-04 22:45:00", "Snow", 45, "Rural Highway")
    ]
    cursor.executemany("INSERT INTO crashes VALUES (?, ?, ?, ?, ?);", crashes)
    
    # Seed vehicles (Mixing baseline Level 0 cars with Level 2 and Level 4 Autonomous Trucks)
    vehicles = [
        ("VEH_101", "CRASH_001", "Commercial Truck", 4), # Level 4 Autonomy freight unit
        ("VEH_102", "CRASH_001", "Passenger Car", 0),    # Baseline vehicle hit by truck
        ("VEH_201", "CRASH_002", "Transit Bus", 2),       # Level 2 highway commuter transport 
        ("VEH_301", "CRASH_003", "Passenger Car", 1)     # Level 1 sedan
    ]
    cursor.executemany("INSERT INTO vehicles VALUES (?, ?, ?, ?);", vehicles)
    
    # Seed complex failures mapped to our vehicles bridge
    failures_bridge = [
        ("VEH_101", "SEN_BLND"), # Level 4 Truck suffered sensor blindness in rain...
        ("VEH_101", "BRK_FAIL"), # ...which triggered an automated hard-braking pad lockup (Multi-failure)
        ("VEH_201", "STR_LOSS"), # Bus suffered structural steering link separation
        ("VEH_301", "TYR_BLOW")  # Car had a high-speed tire tread burst
    ]
    cursor.executemany("INSERT INTO vehicle_failures_bridge VALUES (?, ?);", failures_bridge)
    
    conn.commit()
    conn.close()
    print("Success! Database schema extended and seeded securely.")

if __name__ == "__main__":
    build_extended_schema()
