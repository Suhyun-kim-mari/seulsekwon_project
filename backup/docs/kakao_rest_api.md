# 📍 카카오 로컬 API 활용: 주소 및 위경도 검색 가이드

본 가이드는 카카오 로컬 API를 사용하여 **주소를 좌표로 변환**하거나, **키워드(명칭)로 장소를 검색**하여 주소와 위경도를 추출하는 방법을 설명합니다.

---

### 1. 사전 준비사항
1. [카카오 개발자 센터](https://developers.kakao.com/)에서 앱 생성 후 **REST API 키**를 발급받습니다.
2. **플랫폼 설정**: `Web` 플랫폼에 도메인을 등록합니다 (로컬 테스트 시 `http://localhost` 등).
3. **보안 설정**: 특정 IP에서만 호출할 것이 아니라면 [보안 > IP 허용 리스트] 기능을 **OFF**로 설정합니다.

---

### 2. 통합 파이썬 스크립트
안티그라비티의 파이썬 노드에서 아래 코드를 활용하여 검색 기능을 구현할 수 있습니다.

```python
import requests

class KakaoLocalHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"Authorization": f"KakaoAK {api_key}"}

    def search_by_address(self, address):
        """주소를 입력하면 해당 위치의 상세 정보와 위경도를 반환합니다."""
        url = "https://dapi.kakao.com/v2/local/search/address.json"
        params = {"query": address}
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data['documents']:
                doc = data['documents'][0]
                return {
                    "status": "success",
                    "address_name": doc['address_name'],
                    "lat": doc['y'],
                    "lng": doc['x'],
                    "type": "address"
                }
            return {"status": "fail", "message": "결과 없음"}
        return {"status": "error", "message": response.text}

    def search_by_keyword(self, keyword):
        """키워드(예: '강남역 맛집')를 입력하면 가장 유사한 장소의 주소와 위경도를 반환합니다."""
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        params = {"query": keyword}
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data['documents']:
                doc = data['documents'][0] # 가장 정확도 높은 첫 번째 결과
                return {
                    "status": "success",
                    "place_name": doc['place_name'],
                    "address_name": doc['address_name'],
                    "road_address_name": doc['road_address_name'],
                    "lat": doc['y'],
                    "lng": doc['x'],
                    "type": "keyword"
                }
            return {"status": "fail", "message": "결과 없음"}
        return {"status": "error", "message": response.text}

# --- 사용 예시 ---
API_KEY = "YOUR_REST_API_KEY_HERE"
kakao = KakaoLocalHandler(API_KEY)

# 1. 주소로 찾기
res_addr = kakao.search_by_address("서울특별시 강남구 테헤란로 501")
print(f"[주소 검색 결과]: {res_addr}")

# 2. 키워드로 찾기
res_key = kakao.search_by_keyword("카카오 판교오피스")
print(f"[키워드 검색 결과]: {res_key}")
```

---

### 3. 주요 API 엔드포인트 상세

| 기능 | 엔드포인트 URL | 주요 파라미터 | 설명 |
| :--- | :--- | :--- | :--- |
| **주소 검색** | `/v2/local/search/address.json` | `query` (주소) | 지번/도로명 주소를 좌표로 변환 |
| **키워드 검색** | `/v2/local/search/keyword.json` | `query` (키워드) | 특정 명칭이나 장소를 좌표로 변환 |
| **좌표→주소** | `/v2/local/geo/coord2address.json` | `x`(경도), `y`(위도) | 좌표를 해당 위치의 주소로 변환 |

---

### 4. 결과 데이터 구조 (JSON)
성공 시 API는 아래와 같은 핵심 필드를 포함한 데이터를 응답합니다.

*   **address_name**: 전체 지번 주소 또는 도로명 주소
*   **x**: 경도 (Longitude)
*   **y**: 위도 (Latitude)
*   **place_name**: (키워드 검색 시) 장소 명칭

---

### 5. 트러블슈팅 및 주의사항

1.  **401 Unauthorized**: API 키가 잘못되었거나 헤더에 `KakaoAK ` 접두사가 누락된 경우입니다.
2.  **403 Forbidden**: 카카오 개발자 콘솔에서 **[IP 허용 리스트]**에 호출 서버의 IP가 등록되지 않은 경우입니다. (테스트 시에는 해당 기능을 끄는 것을 권장합니다.)
3.  **Localhost 오류**: REST API 호출 시 `localhost` 도메인 등록은 JavaScript SDK용입니다. 파이썬 `requests` 호출 시에는 IP 보안 설정을 확인하세요.
4.  **좌표 체계**: 기본적으로 **WGS84** 좌표계(위경도)를 사용합니다.

---
*Created for Antigravity Environment - Python Data Automation*