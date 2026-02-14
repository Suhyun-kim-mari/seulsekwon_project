
import pandas as pd
import os

def deduplicate_v2():
    file_path = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/seoul_combined_data_final.csv'
    output_path = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/seoul_combined_data_final_v2.csv'
    
    df = pd.read_csv(file_path)
    
    # 1. 좌표를 소수점 4자리까지 반올림 (약 11m 범위)
    df['lat_r4'] = df['latitude'].round(4)
    df['lon_r4'] = df['longitude'].round(4)
    
    # 2. 소상공인 데이터와 전문 데이터(병원, 은행, 스타벅스 등) 분리
    # 전문 데이터는 데이터의 질이 더 높다고 판단하여 우선순위를 줌
    df_sosang = df[df['source_file'] == 'sosang_seoul_cleaned.csv'].copy()
    df_special = df[df['source_file'] != 'sosang_seoul_cleaned.csv'].copy()
    
    # 3. 소상공인 데이터 중 이름과 유사 좌표가 전문 데이터와 겹치는 항목 식별
    # merge를 통해 겹치는 리스트 확보
    overlap_keys = df_special[['name', 'lat_r4', 'lon_r4']].drop_duplicates()
    
    # 소상공인 데이터에서 겹치는 것들 제거
    # isin 연산 대신 indicator merge 사용
    df_sosang_cleaned = df_sosang.merge(overlap_keys, on=['name', 'lat_r4', 'lon_r4'], how='left', indicator=True)
    df_sosang_final = df_sosang_cleaned[df_sosang_cleaned['_merge'] == 'left_only'].drop(columns=['_merge'])
    
    print(f"소상공인 데이터 제거 전: {len(df_sosang)}")
    print(f"소상공인 데이터 제거 후 (전문 데이터와 겹침): {len(df_sosang_final)}")
    
    # 4. 전체 통합 데이터 구성
    df_final = pd.concat([df_special, df_sosang_final], ignore_index=True)
    
    # 5. 마지막으로 전체 데이터셋에서 동일 이름 + 정확히 동일 좌표인 경우 제거 (혹시 남은 것들)
    df_final = df_final.drop_duplicates(subset=['name', 'latitude', 'longitude'])
    
    # 임시 컬럼 제거
    df_final = df_final.drop(columns=['lat_r4', 'lon_r4'])
    
    # 6. 저장
    df_final.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"\n--- 2차 데구플링 결과 ---")
    print(f"최종 데이터 수: {len(df_final):,}")
    print(f"제거된 중복 건수: {len(df) - len(df_final):,}")
    print(f"저장 경로: {output_path}")

if __name__ == "__main__":
    deduplicate_v2()
