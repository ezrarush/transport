# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "matplotlib",
#     "openpyxl",
# ]
# ///

import os
import sys
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

DB_PATH = "transportation_accidents.db"
OUTPUT_IMAGE = "transportation_safety_dashboard.png"
OUTPUT_EXCEL = "transportation_safety_report.xlsx"

VOLUME_INDEX_MAP = {
    '25 mph': 12000, '35 mph': 25000, '45 mph': 40000,
    '55 mph': 65000, '65 mph': 95000, '70 mph': 110000,
}

def check_database_exists(path):
    if not os.path.exists(path):
        print(f"[FATAL ERROR]: Missing critical data source file at '{path}'.", file=sys.stderr)
        sys.exit(1)

def main():
    check_database_exists(DB_PATH)
    
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
        df_raw['speed_zone'] = df_raw['speed_limit'].astype(str) + " mph"

        # TASK A: Cross-tabulating Weather Conditions with Speed Limit Zones
        print("\n--- 2. Executing Weather vs Speed Zone Cross-Tabulation ---")
        df_crosstab = pd.crosstab(
            index=df_raw['weather_condition'],
            columns=df_raw['speed_zone'],
            values=df_raw['crash_count'],
            aggfunc='sum'
        ).fillna(0).astype(int)

        # TASK B: Calculating Exposure-Adjusted Accident Rates
        print("\n--- 3. Computing Exposure-Adjusted Rates ---")
        df_rates = df_raw.groupby('speed_zone')['crash_count'].sum().reset_index()
        df_rates['daily_volume'] = df_rates['speed_zone'].map(VOLUME_INDEX_MAP).fillna(50000)
        df_rates['crash_rate_per_10k'] = (df_rates['crash_count'] / df_rates['daily_volume']) * 10000
        df_rates = df_rates.sort_values(by='crash_rate_per_10k', ascending=False)

        # TASK C: Auto-Export to Styled Excel Spreadsheets
        print(f"\n--- 4. Exporting Structured Spreadsheet -> '{OUTPUT_EXCEL}' ---")
        
        # Open an Excel writer engine using pandas and openpyxl
        with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
            # Send DataFrames to distinct workbook tabs
            df_crosstab.to_excel(writer, sheet_name='Environmental Crosstab', index=True)
            df_rates.to_excel(writer, sheet_name='Exposure Analysis', index=False)
            
            # Pull workbook reference to apply advanced typography and grids
            workbook = writer.book
            
            # Define stylistic properties
            header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
            header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
            thin_border = Border(
                left=Side(style='thin', color='D9D9D9'),
                right=Side(style='thin', color='D9D9D9'),
                top=Side(style='thin', color='D9D9D9'),
                bottom=Side(style='thin', color='D9D9D9')
            )
            
            # Iterate through each tab to auto-format column widths and alignments
            for sheet_name in workbook.sheetnames:
                ws = workbook[sheet_name]
                ws.views.sheetView[0].showGridLines = True  # Enforce visible grid lines
                
                # Format headers and apply thin border matrix borders across cells
                for row in ws.iter_rows(min_row=1, max_row=1):
                    for cell in row:
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                
                for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
                    for cell in row:
                        cell.border = thin_border
                        if type(cell.value) in [int, float]:
                            cell.alignment = Alignment(horizontal="right")
                        else:
                            cell.alignment = Alignment(horizontal="left")
                
                # Dynamically fit column widths to cell text content lengths
                for col in ws.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    col_letter = get_column_letter(col[0].column)
                    ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        print("Spreadsheet successfully compiled and saved to disk.")

    except Exception as error:
        print(f"[RUNTIME PIPELINE ERROR]: Operation halted. Details: {error}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
