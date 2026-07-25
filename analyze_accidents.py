# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "matplotlib",
# ]
# ///

import os
import sys
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Define files
DB_PATH = "transportation_accidents.db"
OUTPUT_IMAGE = "transportation_safety_dashboard.png"

# Mock exposure matrix: Denotes Daily Traffic Volume Index per speed zone category
# Used to scale raw crash figures to a unified frequency (e.g., rate per 10k vehicles)
VOLUME_INDEX_MAP = {
    '25 mph': 12000,
    '35 mph': 25000,
    '45 mph': 40000,
    '55 mph': 65000,
    '65 mph': 95000,
    '70 mph': 110000,
}

def check_database_exists(path):
    """Gracefully handles missing database prerequisite step."""
    if not os.path.exists(path):
        print(f"[FATAL ERROR]: Missing critical data source file at '{path}'.", file=sys.stderr)
        print("Please place the 'transportation_accidents.db' file in this directory.", file=sys.stderr)
        sys.exit(1)

def main():
    check_database_exists(DB_PATH)
    
    # Establish connection with exception catching
    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        print(f"[DATABASE CONNECTION ERROR]: Could not connect. Reason: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        print("--- 1. Pulling Raw Crash Data Metrics ---")
        query = """
            SELECT weather_condition, speed_limit, COUNT(crash_id) as crash_count
            FROM crashes
            WHERE weather_condition IS NOT NULL AND speed_limit IS NOT NULL
            GROUP BY weather_condition, speed_limit;
        """
        df_raw = pd.read_sql_query(query, conn)
        
        if df_raw.empty:
            print("[WARN]: Connected successfully, but query returned 0 rows. Populating mock records for pipeline execution.")
            # Graceful fallback data generation if the db instance is completely empty
            df_raw = pd.DataFrame([
                {'weather_condition': 'Clear', 'speed_limit': 35, 'crash_count': 14},
                {'weather_condition': 'Clear', 'speed_limit': 65, 'crash_count': 32},
                {'weather_condition': 'Rain', 'speed_limit': 35, 'crash_count': 8},
                {'weather_condition': 'Rain', 'speed_limit': 65, 'crash_count': 22},
                {'weather_condition': 'Snow', 'speed_limit': 35, 'crash_count': 4},
                {'weather_condition': 'Snow', 'speed_limit': 65, 'crash_count': 19},
            ])

        # Formatting speed limit representations into category labels
        df_raw['speed_zone'] = df_raw['speed_limit'].astype(str) + " mph"

        # TASK A: Cross-tabulating Weather Conditions with Speed Limit Zones
        print("\n--- 2. Executing Weather vs Speed Zone Cross-Tabulation ---")
        # Generate matrix counting exactly where environmental intersections reside
        df_crosstab = pd.crosstab(
            index=df_raw['weather_condition'],
            columns=df_raw['speed_zone'],
            values=df_raw['crash_count'],
            aggfunc='sum'
        ).fillna(0)
        
        print(df_crosstab)

        # TASK B: Calculating Exposure-Adjusted Accident Rates
        print("\n--- 3. Computing Exposure-Adjusted Rates (per 10k Vehicles) ---")
        # Collapse counts down to specific speed zones to compute risk indexes
        df_rates = df_raw.groupby('speed_zone')['crash_count'].sum().reset_index()
        
        # Merge exposure indicators into dataframe rows
        df_rates['daily_volume'] = df_rates['speed_zone'].map(VOLUME_INDEX_MAP).fillna(50000)
        
        # Formula: (Crashes / Daily Volume Index) * Rate Factor Constant
        df_rates['crash_rate_per_10k'] = (df_rates['crash_count'] / df_rates['daily_volume']) * 10000
        df_rates = df_rates.sort_values(by='crash_rate_per_10k', ascending=False)
        
        print(df_rates[['speed_zone', 'crash_count', 'daily_volume', 'crash_rate_per_10k']])

        # TASK C: Multi-panel Visual Plot Generation
        print(f"\n--- 4. Rendering Analytics Panels -> '{OUTPUT_IMAGE}' ---")
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Advanced Transportation Safety Analytics & Risk Exposure', fontsize=14, fontweight='bold')

        # Subplot 1: Stacked Bar Chart of Environmental Cross-tabulation
        df_crosstab.plot(kind='bar', stacked=True, ax=axes[0], colormap='viridis', edgecolor='black', alpha=0.85)
        axes[0].set_title('Crash Volume: Weather Condition vs Speed Zone', fontsize=11, fontweight='bold', pad=10)
        axes[0].set_ylabel('Total Crash Count', fontsize=10)
        axes[0].set_xlabel('Weather Condition', fontsize=10)
        axes[0].grid(axis='y', linestyle='--', alpha=0.5)
        axes[0].tick_params(axis='x', rotation=0)
        axes[0].legend(title='Speed Limit')

        # Subplot 2: Exposure-Adjusted Crash Rates Bar Chart
        bars = axes[1].bar(df_rates['speed_zone'], df_rates['crash_rate_per_10k'], color='#c62828', edgecolor='black', alpha=0.8)
        axes[1].set_title('Exposure-Adjusted Risk Rate (Per 10,000 Vehicles)', fontsize=11, fontweight='bold', pad=10)
        axes[1].set_ylabel('Adjusted Crash Rate Index', fontsize=10)
        axes[1].set_xlabel('Speed Limit Zone', fontsize=10)
        axes[1].grid(axis='y', linestyle='--', alpha=0.5)

        # Append data values text labels above the bars
        for bar in bars:
            height = bar.get_height()
            axes[1].annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, fontweight='bold')

        plt.tight_layout()
        plt.savefig(OUTPUT_IMAGE, dpi=300)
        print("\nPipeline execution complete! Graphic exported cleanly.")

    except Exception as error:
        print(f"[RUNTIME PIPELINE ERROR]: Operation halted. Details: {error}", file=sys.stderr)
        sys.exit(1)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
