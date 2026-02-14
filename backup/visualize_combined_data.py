
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# 한글 폰트 설정 (Mac 환경용)
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

def create_visualizations():
    file_path = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/seoul_combined_data.csv'
    df = pd.read_csv(file_path)
    
    output_dir = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/output/visualizations'
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 대분류별 시설 수 (Bar Chart)
    plt.figure(figsize=(12, 6))
    sns.countplot(data=df, y='category_large', order=df['category_large'].value_counts().index, palette='viridis')
    plt.title('서울시 편의시설 대분류별 데이터 현황')
    plt.xlabel('시설 수')
    plt.ylabel('대분류')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '01_category_distribution.png'))
    plt.close()

    # 2. 결측치 히트맵 (Missing Value Heatmap)
    plt.figure(figsize=(10, 6))
    sns.heatmap(df.isnull(), cbar=False, cmap='magma')
    plt.title('데이터 결측치 분포 현황 (노란색이 결측)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '02_missing_values_heatmap.png'))
    plt.close()

    # 3. 데이터 출처별 비중 (Pie Chart)
    plt.figure(figsize=(10, 8))
    source_counts = df['source_file'].value_counts()
    plt.pie(source_counts, labels=source_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
    plt.title('데이터 출처(파일)별 비중')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '03_data_source_pie.png'))
    plt.close()

    # 4. 지리적 분포 - 산점도 (Geographic Scatter Map)
    # 극단적 이상치를 제외한 서울 인근 플로팅 (좌표 오류 시각화 포함)
    plt.figure(figsize=(10, 10))
    # 결합 데이터 중 유효 범위 내부 데이터만 필터링하여 시각화 (이상치 존재 확인용)
    plt.scatter(df['longitude'], df['latitude'], alpha=0.1, s=1, c='blue')
    plt.title('서울시 편의시설 지리적 분포 (전체 데이터)')
    plt.xlabel('경도 (Longitude)')
    plt.ylabel('위도 (Latitude)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '04_geographic_distribution.png'))
    plt.close()

    # 5. 상위 15개 소분류 현황 (Top 15 Small Categories Bar Chart)
    plt.figure(figsize=(12, 8))
    top_small_cats = df['category_small'].value_counts().head(15)
    sns.barplot(x=top_small_cats.values, y=top_small_cats.index, palette='coolwarm')
    plt.title('편의시설 소분류 상위 15개 현황')
    plt.xlabel('시설 수')
    plt.ylabel('소분류')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '05_top_15_small_categories.png'))
    plt.close()

    print(f"시각화 결과가 저장되었습니다: {output_dir}")

if __name__ == "__main__":
    create_visualizations()
