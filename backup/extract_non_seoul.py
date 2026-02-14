
import pandas as pd
import os

def extract_non_seoul_data():
    file_path = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/seoul_combined_data.csv'
    output_path = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/non_seoul_data.csv'
    
    # 데이터 로드
    df = pd.read_csv(file_path)
    
    # 서울 위경도 유효 범위 설정
    # 위도(Latitude): 37.4 ~ 37.7
    # 경도(Longitude): 126.7 ~ 127.2
    lat_min, lat_max = 37.4, 37.7
    lon_min, lon_max = 126.7, 127.2
    
    # 서울 범위를 벗어나는 데이터 필터링
    # 1. 위경도가 결측치인 경우 포함
    # 2. 범위를 벗어나는 경우 포함
    non_seoul_mask = (
        (df['latitude'].isnull()) | 
        (df['longitude'].isnull()) |
        (df['latitude'] < lat_min) | 
        (df['latitude'] > lat_max) |
        (df['longitude'] < lon_min) | 
        (df['longitude'] > lon_max)
    )
    
    non_seoul_df = df[non_seoul_mask]
    
    # 별도 CSV 파일로 저장
    non_seoul_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"--- 추출 결과 ---")
    print(f"전체 데이터 수: {len(df)}")
    print(f"서울 외 데이터 수 (결측 포함): {len(non_seoul_df)}")
    print(f"저장 경로: {output_path}")
    
    if len(non_seoul_df) > 0:
        print("\n--- 출처별 통계 ---")
        print(non_seoul_df['source_file'].value_counts())
        
        print("\n--- 상위 5개 샘플 ---")
        print(non_seoul_df[['name', 'latitude', 'longitude', 'source_file']].head())

if __name__ == "__main__":
    extract_non_seoul_data()
