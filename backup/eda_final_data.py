
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 한글 폰트 설정 (Mac 환경용)
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

def run_final_eda():
    file_path = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/seoul_combined_data_final.csv'
    output_dir = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/output/final_eda'
    os.makedirs(output_dir, exist_ok=True)
    
    df = pd.read_csv(file_path)
    
    print("--- [최종 데이터셋 EDA 보고서] ---")
    print(f"1. 전체 데이터 규모: {len(df):,} 행")
    print(f"2. 컬럼 구성: {df.columns.tolist()}")
    
    print("\n3. 결측치 현황:")
    print(df.isnull().sum())
    
    print("\n4. 대분류별(category_large) 분포:")
    cat_counts = df['category_large'].value_counts()
    print(cat_counts)
    
    # 지리적 범위 확인
    print("\n5. 지리적 데이터 범위 (서울 핵심 권역):")
    print(f"위도(Latitude): {df['latitude'].min():.4f} ~ {df['latitude'].max():.4f}")
    print(f"경도(Longitude): {df['longitude'].min():.4f} ~ {df['longitude'].max():.4f}")

    # 시각화 1: 대분류별 시설 수
    plt.figure(figsize=(12, 7))
    sns.countplot(data=df, y='category_large', order=cat_counts.index, palette='crest')
    plt.title('최종 통합 데이터 카테고리별 분포')
    plt.xlabel('시설 수')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'final_category_dist.png'))
    plt.close()

    # 시각화 2: 지리적 산점도 (데이터 정제 후의 서울 지도 형태 확인)
    plt.figure(figsize=(10, 10))
    plt.scatter(df['longitude'], df['latitude'], alpha=0.05, s=0.5, c='darkblue')
    plt.title('최종 데이터 지리적 분포 (정제 완료)')
    plt.xlabel('경도')
    plt.ylabel('위도')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'final_geo_scatter.png'))
    plt.close()

    print(f"\nEDA 결과 및 시각화 파일들이 {output_dir} 에 저장되었습니다.")

if __name__ == "__main__":
    run_final_eda()
