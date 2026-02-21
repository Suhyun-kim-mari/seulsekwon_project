import pandas as pd
import os
import glob
import time

def combine_real_estate_data():
    data_dir = "/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/share/data"
    # '_all.csv'로 끝나는 실거래가 데이터 파일들을 찾습니다.
    file_pattern = os.path.join(data_dir, "seoul_real_estate_*_all.csv")
    files = glob.glob(file_pattern)
    
    if not files:
        print("🔍 통합할 실거래가 데이터 파일을 찾을 수 없습니다.")
        return

    print(f"📂 발견된 파일 목록: {[os.path.basename(f) for f in files]}")
    
    dfs = []
    for file in sorted(files):
        print(f"📖 읽는 중: {os.path.basename(file)}")
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            print(f"⚠️ {file} 로드 중 오류 발생: {e}")

    if dfs:
        print("🔗 데이터 통합 중...")
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # 중복 제거 (필요시)
        initial_count = len(combined_df)
        combined_df = combined_df.drop_duplicates()
        final_count = len(combined_df)
        
        if initial_count > final_count:
            print(f"✨ 중복 데이터 {initial_count - final_count:,}건을 제거했습니다.")

        # 최종 저장
        output_path = os.path.join(data_dir, "seoul_real_estate_combined_2023_2026.csv")
        combined_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ 통합 완료!")
        print(f"📊 총 레코드 수: {len(combined_df):,}건")
        print(f"💾 저장 경로: {output_path}")
    else:
        print("❌ 통합할 데이터가 없습니다.")

if __name__ == "__main__":
    combine_real_estate_data()
