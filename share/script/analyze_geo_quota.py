import pandas as pd
import os

def analyze_unique_locations():
    file_path = "/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/share/data/seoul_real_estate_combined_2023_2026.csv"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print("📖 Reading file...")
    df = pd.read_csv(file_path)
    
    # Create a unique key for geographic locations
    # CGG_NM (Gu), STDG_NM (Dong), MNO (Bonbeon), SNO (Bubeon), BLDG_NM (Building)
    # Filling NaN with empty string to avoid dropna issues
    df['loc_key'] = df['CGG_NM'].fillna('').astype(str) + ' ' + \
                    df['STDG_NM'].fillna('').astype(str) + ' ' + \
                    df['MNO'].fillna('').astype(str) + '-' + df['SNO'].fillna('').astype(str) + ' ' + \
                    df['BLDG_NM'].fillna('').astype(str)
    
    unique_locs = df['loc_key'].unique()
    print(f"📊 Total Rows: {len(df):,}")
    print(f"📍 Unique Locations: {len(unique_locs):,}")
    
    # Check top locations
    print("\n--- Example Locations ---")
    print(pd.Series(unique_locs).head(10))

if __name__ == "__main__":
    analyze_unique_locations()
