import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("KAKAO_REST_API_KEY")
url = "https://dapi.kakao.com/v2/local/search/address.json"
headers = {"Authorization": f"KakaoAK {api_key}"}
params = {"query": "서울시청"}

response = requests.get(url, headers=headers, params=params)
print(f"Status Code: {response.status_code}")
print(f"Response Body: {response.text}")
