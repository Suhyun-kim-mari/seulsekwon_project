
import pandas as pd

def finalize_dataset():
    main_file = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/seoul_combined_data.csv'
    updated_file = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/non_seoul_data_kakao_updated.csv'
    final_output = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/seoul_combined_data_final.csv'
    
    df_main = pd.read_csv(main_file)
    df_updated = pd.read_csv(updated_file)
    
    # Define Seoul bounds
    lat_min, lat_max = 37.4, 37.7
    lon_min, lon_max = 126.7, 127.2
    
    # 1. First, remove the problematic rows from the main dataframe
    # Problematic rows are those that were extracted to non_seoul_data.csv
    # We can identify them by checking which rows were in the outlier set (Lat < 37.4 etc.)
    outlier_mask = (
        (df_main['latitude'].isnull()) | 
        (df_main['longitude'].isnull()) |
        (df_main['latitude'] < lat_min) | 
        (df_main['latitude'] > lat_max) |
        (df_main['longitude'] < lon_min) | 
        (df_main['longitude'] > lon_max)
    )
    
    df_filtered_main = df_main[~outlier_mask].copy()
    
    # 2. Add the successfully updated rows back
    # Only those that are now within Seoul bounds
    within_seoul_updated = df_updated[
        (df_updated['latitude'] >= lat_min) & 
        (df_updated['latitude'] <= lat_max) & 
        (df_updated['longitude'] >= lon_min) & 
        (df_updated['longitude'] <= lon_max)
    ]
    
    df_final = pd.concat([df_filtered_main, within_seoul_updated], ignore_index=True)
    
    # 3. Final cleaning: remove any duplicates if they exist (based on name, lat, lon)
    df_final = df_final.drop_duplicates(subset=['name', 'latitude', 'longitude'])
    
    # 4. Save the final dataset
    df_final.to_csv(final_output, index=False, encoding='utf-8-sig')
    
    print(f"--- 최종 정제 결과 ---")
    print(f"원본 데이터 수: {len(df_main)}")
    print(f"이상치/결측치 중 복구된 데이터: {len(within_seoul_updated)}")
    print(f"최종 통합 데이터 수: {len(df_final)}")
    print(f"삭제된 영구 이상치 수: {len(df_updated) - len(within_seoul_updated)}")
    print(f"최종 파일 저장 위치: {final_output}")

if __name__ == "__main__":
    finalize_dataset()
