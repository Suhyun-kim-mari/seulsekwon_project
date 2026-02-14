
import requests
import os
from dotenv import load_dotenv

load_dotenv('/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/.env')
api_key = os.getenv('KAKAO_REST_API_KEY')

print(f"Using API Key: {api_key}")

def test_kakao():
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": "서울특별시 강남구 논현로175길 94"}
    
    response = requests.get(url, headers=headers, params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_kakao()
