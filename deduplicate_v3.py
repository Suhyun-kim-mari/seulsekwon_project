import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from scipy.spatial import KDTree

def string_similarity(a, b):
    return SequenceMatcher(None, str(a).strip(), str(b).strip()).ratio()

def lon_lat_to_cartesian(lon, lat):
    # Convert degrees to radians
    lon_rad = np.deg2rad(lon)
    lat_rad = np.deg2rad(lat)
    # Earth radius in meters
    R = 6371000
    x = R * np.cos(lat_rad) * np.cos(lon_rad)
    y = R * np.cos(lat_rad) * np.sin(lon_rad)
    z = R * np.sin(lat_rad)
    return np.column_stack((x, y, z))

def solve_duplicates():
    file_path = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/seoul_combined_data_final.csv'
    df = pd.read_csv(file_path)
    
    print(f"Original shape: {df.shape}")
    
    # 1. Separate transport and others
    transport_sources = ['metro_station_seoul_cleaned.csv', 'bus_station_seoul_cleaned.csv']
    sosang_source = 'sosang_seoul_cleaned.csv'
    
    df_transport = df[df['source_file'].isin(transport_sources)].copy()
    df_others = df[~df['source_file'].isin(transport_sources)].copy()
    
    # Reset index for df_others to handle mapping correctly
    df_others = df_others.reset_index(drop=True)
    
    # 2. Prepare for proximity search using KDTree
    # Convert points to 3D Cartesian coordinates
    coords_3d = lon_lat_to_cartesian(df_others['longitude'].values, df_others['latitude'].values)
    tree = KDTree(coords_3d)
    
    # Identify indices to drop
    to_drop = set()
    processed = [False] * len(df_others)
    
    # Radius in meters
    radius_m = 50 
    
    print("Identifying duplicates...")
    for i in range(len(df_others)):
        if i % 10000 == 0:
            print(f"Processing... {i}/{len(df_others)}")
            
        if processed[i]:
            continue
            
        # Find neighbors within radius
        idx_neighbors = tree.query_ball_point(coords_3d[i], r=radius_m)
        
        if len(idx_neighbors) <= 1:
            continue
            
        current_name = df_others.iloc[i]['name']
        current_source = df_others.iloc[i]['source_file']
        
        for neighbor_idx in idx_neighbors:
            if neighbor_idx == i or processed[neighbor_idx]:
                continue
                
            neighbor_name = df_others.iloc[neighbor_idx]['name']
            neighbor_source = df_others.iloc[neighbor_idx]['source_file']
            
            # Check name similarity
            sim = string_similarity(current_name, neighbor_name)
            
            if sim >= 0.8:
                # Rule: If one is sosang and other is not, drop sosang
                if current_source == sosang_source and neighbor_source != sosang_source:
                    to_drop.add(i)
                    processed[i] = True
                    break # Current is dropped, no need to check other neighbors for it
                elif neighbor_source == sosang_source and current_source != sosang_source:
                    to_drop.add(neighbor_idx)
                    processed[neighbor_idx] = True
                elif current_source == sosang_source and neighbor_source == sosang_source:
                    # Both are sosang, drop the neighbor
                    to_drop.add(neighbor_idx)
                    processed[neighbor_idx] = True
                else:
                    # Neither is sosang, but they are similar and close
                    to_drop.add(neighbor_idx)
                    processed[neighbor_idx] = True

    # 3. Create cleaned dataframe
    df_others_cleaned = df_others.drop(index=list(to_drop))
    print(f"Dropped {len(to_drop)} duplicates from non-transport data.")
    
    # 4. Combine and save
    df_final = pd.concat([df_others_cleaned, df_transport], ignore_index=True)
    print(f"Final shape: {df_final.shape}")
    
    output_path = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/seoul_combined_data_final_v3.csv'
    df_final.to_csv(output_path, index=False)
    print(f"Saved cleaned data to {output_path}")

if __name__ == "__main__":
    solve_duplicates()
