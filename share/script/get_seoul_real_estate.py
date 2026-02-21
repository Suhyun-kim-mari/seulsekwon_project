import requests
import pandas as pd
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv
import time

# .env 파일 로드 (부모 디렉토리의 .env 탐색)
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)

def fetch_seoul_real_estate(api_key, start_index=1, end_index=1000, year="", sgg_cd="", sgg_nm="", bjdong_cd="", land_gb="", land_gb_nm="", bonbeon="", bubeon="", bldg_nm="", contract_date="", bldg_usg=""):
    """
    서울시 부동산 실거래가 정보를 가져오는 함수
    파라미터 순서: {인증키}/xml/tbLnOpendataRtmsV/{시작}/{종료}/{접수연도}/{시군구코드}/{시군구명}/{법정동코드}/{지번구분}/{지번구분명}/{본번}/{부번}/{건물명}/{계약일}/{건물용도}
    """
    # 기본 URL
    base_url = f"http://openapi.seoul.go.kr:8088/{api_key}/xml/tbLnOpendataRtmsV/{start_index}/{end_index}"
    
    # 상세 파라미터 구성 (사용자가 제공한 샘플 URL 구조 준수)
    params = [year, sgg_cd, sgg_nm, bjdong_cd, land_gb, land_gb_nm, bonbeon, bubeon, bldg_nm, contract_date, bldg_usg]
    
    # 뒤쪽부터 빈 문자열 제거하여 URL 생성
    while params and not params[-1]:
        params.pop()
        
    extra_params = "/".join([str(p) for p in params])
    url = f"{base_url}/{extra_params}".rstrip("/")
    
    print(f"📡 {year}년 데이터 요청 중: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # XML 파싱
        root = ET.fromstring(response.content)
        
        # 결과 코드 확인
        result_node = root.find(".//RESULT")
        if result_node is not None:
            code = result_node.find("CODE").text
            message = result_node.find("MESSAGE").text
            if code != "INFO-000":
                if code == "INFO-200": # 데이터 없음
                    return pd.DataFrame(), 0
                print(f"❌ API 응답 오류: {code} ({message})")
                return pd.DataFrame(), 0

        # 전체 개수 확인
        total_count_node = root.find("list_total_count")
        total_count = int(total_count_node.text) if total_count_node is not None else 0

        # 데이터 추출
        rows = []
        for row in root.findall(".//row"):
            item = {child.tag: child.text for child in row}
            rows.append(item)
            
        return pd.DataFrame(rows), total_count
        
    except Exception as e:
        print(f"⚠️ {year}년 요청 중 오류 발생: {e}")
        return pd.DataFrame(), 0

def main():
    # 1. API 키 설정
    API_KEY = os.getenv("SEOUL_API_KEY", "sample")
    
    print(f"🔑 사용 중인 인증키: {API_KEY}")
    if API_KEY == "sample":
        print("⚠️ 주의: 'sample' 키는 페이지네이션이 제한될 수 있습니다 (최대 5건).")
        batch_size = 5
    else:
        batch_size = 1000 # 일반 키는 최대 1000건

    target_years = range(2023, 2027)
    output_dir = "/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/share/data"
    os.makedirs(output_dir, exist_ok=True)

    for year in target_years:
        print(f"\n🚀 {year}년 전체 데이터 수집 프로세스 시작")
        year_data = []
        start_idx = 1
        
        # 첫 번째 호출로 전체 개수 파악
        temp_df, total_count = fetch_seoul_real_estate(API_KEY, 1, batch_size, year=str(year))
        
        if total_count == 0:
            print(f"🔍 {year}년 성과 데이터가 없습니다. 건너뜁니다.")
            continue
            
        print(f"📊 {year}년 총 데이터 건수: {total_count:,}건")
        
        # 페이지네이션 루프
        while start_idx <= total_count:
            end_idx = min(start_idx + batch_size - 1, total_count)
            print(f"📦 데이터 수집 중... ({start_idx:,} ~ {end_idx:,} / {total_count:,})", end="\r")
            
            df, _ = fetch_seoul_real_estate(API_KEY, start_idx, end_idx, year=str(year))
            
            if not df.empty:
                year_data.append(df)
            else:
                print(f"\n⚠️ {start_idx} 지점에서 빈 데이터를 응답받았습니다. 중단합니다.")
                break
                
            start_idx += batch_size
            
            # API 서버 부하 방지를 위한 아주 짧은 휴식 (필요 시)
            # time.sleep(0.1)

        if year_data:
            final_df = pd.concat(year_data, ignore_index=True)
            print(f"\n✅ {year}년 수집 완료: 총 {len(final_df):,}건")
            
            # 데이터 정제 (숫자형 변환)
            numeric_cols = ['THING_AMT', 'ARCH_AREA', 'LAND_AREA', 'FLR', 'ARCH_YR']
            for col in numeric_cols:
                if col in final_df.columns:
                    final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
            
            # 파일 저장
            filename = f"seoul_real_estate_{year}_all.csv"
            save_path = os.path.join(output_dir, filename)
            final_df.to_csv(save_path, index=False, encoding='utf-8-sig')
            print(f"💾 파일 저장 완료: {save_path}")
        else:
            print(f"\n❌ {year}년 수집된 데이터가 없습니다.")

if __name__ == "__main__":
    main()
