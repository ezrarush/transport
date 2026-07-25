# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "matplotlib",
# ]
# ///

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Connect to the SQLite database file
db_path = "transportation_accidents.db"
conn = sqlite3.connect(db_path)

try:
    print("--- 1. Querying Dashboard Data Components ---")
    
    # Query A: KABCO Injury Severity Distribution
    query_kabco = """
        SELECT injury_severity_kabco as severity, COUNT(person_id) as total_count 
        FROM people WHERE injury_severity_kabco IS NOT NULL
        GROUP BY injury_severity_kabco
        ORDER BY CASE injury_severity_kabco
            WHEN 'K' THEN 1 WHEN 'A' THEN 2 WHEN 'B' THEN 3 WHEN 'C' THEN 4 WHEN 'O' THEN 5 ELSE 6
        END;
    """
    df_kabco = pd.read_sql_query(query_kabco, conn)
    kabco_labels = {'K': 'K-Fatal', 'A': 'A-Serious', 'B': 'B-Minor', 'C': 'C-Possible', 'O': 'O-No Injury'}
    df_kabco['label'] = df_kabco['severity'].map(kabco_labels)

    # Query B: Accident Distribution by Weather Condition
    query_weather = """
        SELECT weather_condition as weather, COUNT(crash_id) as total_count 
        FROM crashes WHERE weather_condition IS NOT NULL
        GROUP BY weather_condition
        ORDER BY total_count DESC;
    """
    df_weather = pd.read_sql_query(query_weather, conn)

    # Query C: Autonomous Driving Levels vs Accident Frequency (Count of Vehicles involved)
    query_autonomy = """
        SELECT 
            'Level ' || autonomous_level as av_level, 
            COUNT(vehicle_id) as total_count 
        FROM vehicles WHERE autonomous_level IS NOT NULL
        GROUP BY autonomous_level
        ORDER BY autonomous_level ASC;
    """
    df_autonomy = pd.read_sql_query(query_autonomy, conn)

    # 2. Generating the 3-Panel Dashboard Plot Layout
    print("\n--- 2. Generating Multi-Panel Visualization Canvas ---")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    fig.suptitle('Transportation System Accident Analytics Dashboard', fontsize=16, fontweight='bold', y=0.98)

    # Panel 1: Bar Chart of KABCO Injury Severities
    colors_kabco = ['#d32f2f', '#f57c00', '#fbc02d', '#388e3c', '#1976d2']
    bars1 = axes[0].bar(df_kabco['label'], df_kabco['total_count'], color=colors_kabco[:len(df_kabco)], edgecolor='black', alpha=0.8)
    axes[0].set_title('Injury Severities (KABCO Scale)', fontsize=12, fontweight='bold', pad=10)
    axes[0].set_ylabel('Count of People', fontsize=10)
    axes[0].grid(axis='y', linestyle='--', alpha=0.5)
    axes[0].tick_params(axis='x', rotation=15)

    # Panel 2: Horizontal Bar Chart of Crashes by Weather Condition
    bars2 = axes[1].barh(df_weather['weather'], df_weather['total_count'], color='#4a148c', edgecolor='black', alpha=0.75)
    axes[1].set_title('Accident Breakdown by Weather', fontsize=12, fontweight='bold', pad=10)
    axes[1].set_xlabel('Count of Crashes', fontsize=10)
    axes[1].grid(axis='x', linestyle='--', alpha=0.5)
    axes[1].invert_yaxis()  # Puts highest count at top

    # Panel 3: Bar Chart of Autonomy Levels vs Crash Counts
    bars3 = axes[2].bar(df_autonomy['av_level'], df_autonomy['total_count'], color='#006064', edgecolor='black', alpha=0.8)
    axes[2].set_title('Autonomy Levels vs Crash Frequency', fontsize=12, fontweight='bold', pad=10)
    axes[2].set_ylabel('Count of Vehicles Involved', fontsize=10)
    axes[2].grid(axis='y', linestyle='--', alpha=0.5)

    # Inject Value Annotation Labels on Bars Helper Function
    def add_labels(ax, bars, is_horizontal=False):
        for bar in bars:
            if is_horizontal:
                width = bar.get_width()
                ax.annotate(f'{int(width)}', xy=(width, bar.get_y() + bar.get_height() / 2),
                            xytext=(5, 0), textcoords="offset points", ha='left', va='center', fontweight='bold', fontsize=9)
            else:
                height = bar.get_height()
                ax.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold', fontsize=9)

    add_labels(axes[0], bars1)
    add_labels(axes[1], bars2, is_horizontal=True)
    add_labels(axes[2], bars3)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    
    # Save the output file directly into your system directory
    output_filename = "transportation_safety_dashboard.png"
    plt.savefig(output_filename, dpi=300)
    print(f"Success! Dashboard snapshot exported to disk as: '{output_filename}'")

finally:
    conn.close()
    print("Database connection closed cleanly.")
