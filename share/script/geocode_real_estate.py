import pandas as pd
import requests
import os
import time
import json
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load API Key
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)
KAKAO_KEY = os.getenv("KAKAO_REST_API_KEY")

if not KAKAO_KEY:
    print("❌ Error: KAKAO_REST_API_KEY not found in .env")
    exit(1)

INPUT_FILE = "/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/share/data/seoul_real_estate_combined_2023_2026.csv"
OUTPUT_FILE = "/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/share/data/seoul_real_estate_combined_2023_2026_geo.csv"
CACHE_FILE = "/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/share/data/geo_cache.json"

def get_coords(query):
    """Kakao API를 사용해 위경도 좌표를 가져옵니다."""
    headers = {"Authorization": f"KakaoAK {KAKAO_KEY}"}
    
    # 1. 주소 검색 시도
    addr_url = "https://dapi.kakao.com/v2/local/search/address.json"
    try:
        res = requests.get(addr_url, headers=headers, params={"query": query}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data['documents']:
                doc = data['documents'][0]
                return query, float(doc['y']), float(doc['x'])
    except:
        pass

    # 2. 키워드 검색 시도 (주소로 안 나올 경우)
    kw_url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    try:
        res = requests.get(kw_url, headers=headers, params={"query": query}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data['documents']:
                doc = data['documents'][0]
                return query, float(doc['y']), float(doc['x'])
    except:
        pass

    return query, None, None

def main():
    print("📖 Loading data...")
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    
    # 지번 처리를 위한 정제
    def format_mno_sno(row):
        mno = str(row['MNO']).replace('.0', '') if pd.notnull(row['MNO']) and str(row['MNO']) != 'nan' else ''
        sno = str(row['SNO']).replace('.0', '') if pd.notnull(row['SNO']) and str(row['SNO']) != 'nan' else ''
        return f"{mno}-{sno}".strip('-')

    df['jibun'] = df.apply(format_mno_sno, axis=1)
    df['search_addr'] = (df['CGG_NM'].fillna('').astype(str) + ' ' + \
                        df['STDG_NM'].fillna('').astype(str) + ' ' + \
                        df['jibun'].fillna('').astype(str) + ' ' + \
                        df['BLDG_NM'].fillna('').astype(str)).str.strip().str.replace('  ', ' ')
    
    unique_addrs = df['search_addr'].unique()
    total_unique = len(unique_addrs)
    print(f"📍 Unique Addresses to geocode: {total_unique:,}")

    # 캐시 로드
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        print(f"💾 Loaded cache with {len(cache):,} items.")

    # 작업 대기열 생성
    todo = [addr for addr in unique_addrs if addr and addr not in cache]
    print(f"🚀 Tasks to process: {len(todo):,}")

    if not todo:
        print("✅ No new addresses to geocode.")
    else:
        # 병렬 실행 (max_workers=10 정도로 제한하여 API 속도 제한 준수)
        processed = 0
        new_results = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_addr = {executor.submit(get_coords, addr): addr for addr in todo}
            
            for future in as_completed(future_to_addr):
                addr, lat, lng = future.result()
                cache[addr] = {"lat": lat, "lng": lng}
                processed += 1
                if lat: new_results += 1
                
                # 진행률 출력 및 중간 저장
                if processed % 500 == 0 or processed == len(todo):
                    print(f"📦 Progress: {processed}/{len(todo)} ({processed/len(todo)*100:.1f}%) | Found: {new_results}")
                    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(cache, f, ensure_ascii=False)

    print(f"\n✨ Geocoding finished. Total cached: {len(cache):,}")

    # 데이터프레임에 매핑
    print("🔗 Mapping coordinates back to DataFrame...")
    df['latitude'] = df['search_addr'].map(lambda x: cache.get(x, {}).get('lat'))
    df['longitude'] = df['search_addr'].map(lambda x: cache.get(x, {}).get('lng'))

    # 임시 컬럼 제거 및 저장
    df = df.drop(columns=['jibun', 'search_addr'])
    print(f"💾 Saving to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print("✅ Done!")

if __name__ == "__main__":
    main()
