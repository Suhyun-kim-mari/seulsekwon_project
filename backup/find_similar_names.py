
import pandas as pd
import re
from difflib import SequenceMatcher
import os

def ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()

def clean_name(name):
    if not isinstance(name, str): return ""
    # Remove spaces, special chars, common Corp suffixes
    name = re.sub(r'\([^)]*\)', '', name) # Remove anything in parenthesis
    name = re.sub(r'[^가-힣a-zA-Z0-9]', '', name)
    return name

def find_similar_names():
    file_path = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/seoul_combined_data_final_v2.csv'
    output_path = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/potential_duplicates.xlsx'
    
    print("Loading data...")
    df = pd.read_csv(file_path)
    
    # 1. Normalize for grouping
    df['name_clean'] = df['name'].apply(clean_name)
    # Use rounded coords to define "neighborhoods" (approx 500m-1km)
    # 0.005 degrees is roughly 500m
    df['lat_grid'] = (df['latitude'] / 0.005).astype(int)
    df['lon_grid'] = (df['longitude'] / 0.005).astype(int)
    
    potential_dupes = []
    
    print("Searching for similar names in neighborhoods...")
    # Group by grid to limit the search space (O(n^2) within small groups)
    groups = df.groupby(['lat_grid', 'lon_grid'])
    
    total_groups = len(groups)
    processed = 0
    
    for _, group in groups:
        processed += 1
        if len(group) < 2: continue
        
        # Convert group to list for faster iteration
        records = group.to_dict('records')
        n = len(records)
        for i in range(n):
            for j in range(i + 1, n):
                r1 = records[i]
                r2 = records[j]
                
                # If cleaned names are exact match OR fuzzy match > 0.8
                # but they were not caught by the previous exact name/lat/lon drop
                match_val = 0
                if r1['name_clean'] == r2['name_clean']:
                    match_val = 1.0
                else:
                    # Fuzzy match on raw names
                    match_val = ratio(r1['name'], r2['name'])
                
                if match_val >= 0.8:
                    # Only add if they are quite close (already in the same 500m grid, but let's be sure)
                    # We add them to a list for inspection
                    # To avoid duplicates in output, we use a set of IDs or just collect and dedupe at the end
                    potential_dupes.append(r1)
                    potential_dupes.append(r2)
        
        if processed % 100 == 0:
            print(f"Progress: {processed}/{total_groups} groups checked...")

    if not potential_dupes:
        print("No similar names found in proximity.")
        return

    # Create a DataFrame and remove exact duplicates from this result set
    result_df = pd.DataFrame(potential_dupes).drop_duplicates()
    
    # Sort by cleaned name and coordinates to cluster them for the user
    result_df = result_df.sort_values(['name_clean', 'latitude'])
    
    # Select columns for export
    export_cols = ['name', 'address', 'latitude', 'longitude', 'category_large', 'category_small', 'source_file']
    result_df[export_cols].to_excel(output_path, index=False)
    
    print(f"\nPotential duplicates found: {len(result_df)} rows")
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    find_similar_names()
