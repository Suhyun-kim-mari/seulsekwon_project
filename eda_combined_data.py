
import pandas as pd
import numpy as np

def run_eda():
    file_path = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/seoul_combined_data.csv'
    df = pd.read_csv(file_path)
    
    print("--- 1. 기본 정보 ---")
    print(f"전체 행 수: {len(df)}")
    print(f"컬럼명: {df.columns.tolist()}")
    print("\n--- 2. 결측치 분석 ---")
    print(df.isnull().sum())
    
    print("\n--- 3. 대분류별 데이터 분포 (top 20) ---")
    print(df['category_large'].value_counts().head(20))
    
    print("\n--- 4. 데이터 소스별 분포 ---")
    print(df['source_file'].value_counts())
    
    print("\n--- 5. 지리적 데이터 요약 ---")
    print(f"위도(Latitude) 범위: {df['latitude'].min()} ~ {df['latitude'].max()}")
    print(f"경도(Longitude) 범위: {df['longitude'].min()} ~ {df['longitude'].max()}")
    
    # 서울 범위를 벗어나는 데이터 체크 (약 위도 37.4~37.7, 경도 126.7~127.2)
    outliers = df[(df['latitude'] < 37.0) | (df['latitude'] > 38.0) | (df['longitude'] < 126.0) | (df['longitude'] > 128.0)]
    print(f"\n이상치(서울 외곽 추정) 행 수: {len(outliers)}")
    if len(outliers) > 0:
        print("이상치 샘플:")
        print(outliers[['name', 'latitude', 'longitude', 'source_file']].head())

if __name__ == "__main__":
    run_eda()
