
import pandas as pd
import requests
import time
import os
from dotenv import load_dotenv

def search_kakao_coords(query, api_key, search_type='address'):
    """
    search_type: 'address' or 'keyword'
    """
    if not query or pd.isna(query):
        return None, None
        
    url = f"https://dapi.kakao.com/v2/local/search/{search_type}.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": query}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['documents']:
                # Get the first result
                doc = data['documents'][0]
                return float(doc['y']), float(doc['x']) # lat, lon
        return None, None
    except Exception as e:
        print(f"Error searching {query}: {e}")
        return None, None

def update_coords_via_kakao():
    # Load environment variables
    load_dotenv('/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/.env')
    api_key = os.getenv('KAKAO_REST_API_KEY')
    
    if not api_key:
        print("API Key not found in .env file.")
        return

    file_path = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/non_seoul_data.csv'
    df = pd.read_csv(file_path)
    
    updated_count = 0
    total = len(df)
    
    print(f"Starting Kakao API search for {total} items...")
    
    for idx, row in df.iterrows():
        name = row['name']
        address = row['address']
        
        lat, lon = None, None
        
        # 1. Try Address Search if address exists
        if pd.notnull(address) and address.strip():
            # Clean address: remove part after comma or parenthesis if it looks like extra info?
            # Actually, Kakao API is quite good with full strings, but let's try raw first.
            lat, lon = search_kakao_coords(address, api_key, 'address')
        
        # 2. Try Keyword Search if address failed or doesn't exist
        if lat is None:
            # Add "서울 " if it's likely a Seoul establishment to narrow down
            query = name if "서울" in name else f"서울 {name}"
            lat, lon = search_kakao_coords(query, api_key, 'keyword')
            
        if lat is not None:
            df.at[idx, 'latitude'] = lat
            df.at[idx, 'longitude'] = lon
            updated_count += 1
            
        # Rate limiting (Kakao has limits, so a tiny sleep is safe)
        if (idx + 1) % 10 == 0:
            print(f"Progress: {idx + 1}/{total}...")
            time.sleep(0.1)

    output_path = '/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/non_seoul_data_kakao_updated.csv'
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"Finished. Updated {updated_count} out of {total} rows.")
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    update_coords_via_kakao()
