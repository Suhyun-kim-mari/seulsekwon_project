import streamlit as st
import pandas as pd
import folium
import plotly.express as px
import plotly.graph_objects as go
from geopy.distance import geodesic
import os
import requests
from dotenv import load_dotenv
from streamlit_folium import st_folium
import re
import base64
from io import BytesIO
import datetime

# ==========================================
# 1. Configuration & Constants
# ==========================================

# .env 파일 로드 (부모 디렉토리의 .env 탐색)
import os
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))

possible_paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), '.env'), # seulsekwon_project/.env
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), '.env') # pj/.env
]

env_path = None
for path in possible_paths:
    if os.path.exists(path):
        env_path = path
        break

if env_path:
    load_dotenv(env_path)
    print(f".env loaded from: {env_path}")
else:
    print("Warning: .env file not found.")

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) 

st.set_page_config(
    page_title="서울 슬세권 분석 시스템 v2.5",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Design System
THEME = {
    "primary": "#3b82f6",
    "secondary": "#1e293b",
    "accent": "#6366f1",
    "background": "#f8fafc",
    "card_bg": "#ffffff",
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "text_main": "#1e293b",
    "text_muted": "#64748b"
}

EMOJI_MAP = {
    "스타벅스": "☕", "카페": "☕", "편의점": "🏪", "세탁소": "🏪", "마트": "🏪", "대형마트": "🏬",
    "백화점": "🏬", "버스": "🚌", "bus": "🚌", "정류장": "🚌", "정류소": "🚌",
    "지하철": "🚇", "metro": "🚇", "역": "🚇", "병원": "🏥", "의원": "💊",
    "약국": "💊", "경찰": "🚓", "파출소": "🚓", "도서관": "📚", "서점": "📚",
    "학교": "🏫", "공원": "🌳", "park": "🌳", "체육": "🏋️", "운동": "🏋️", "은행": "🏦", "금융": "🏦"
}

CATEGORY_GROUPS = {
    "생활/편의🏪": ["스타벅스", "편의점", "세탁소", "마트", "대형마트", "백화점", "카페"],
    "교통🚌": ["버스", "지하철", "정류장", "정류소", "역", "bus", "metro"],
    "의료💊": ["병원", "의원", "약국", "치과", "한의원"],
    "안전/치안🚨": ["경찰", "파출소", "치안", "소방", "119"],
    "교육/문화📚": ["도서관", "서점", "학교", "유치원", "학원"],
    "자연/여가🌳": ["공원", "체육", "운동", "산책", "park"],
    "금융🏦": ["은행", "금융", "ATM"]
}

DEFAULT_WEIGHTS = {
    "생활/편의🏪": 30, 
    "교통🚌": 20, 
    "의료💊": 15, 
    "안전/치안🚨": 10, 
    "교육/문화📚": 5, 
    "자연/여가🌳": 15, 
    "금융🏦": 5
}

# ==========================================
# 2. Styling (CSS)
# ==========================================

def inject_custom_css():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700&display=swap');
        
        .stApp {{
            font-family: 'Pretendard', sans-serif;
            background-color: {THEME['background']};
        }}
        
        .dashboard-card {{
            background: {THEME['card_bg']};
            padding: 1.5rem;
            border-radius: 1.2rem;
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(226, 232, 240, 0.8);
            margin-bottom: 1.2rem;
            transition: all 0.3s ease;
        }}
        
        .dashboard-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 28px -5px rgba(0, 0, 0, 0.08);
        }}
        
        .metric-value {{
            font-size: 4rem;
            font-weight: 800;
            background: linear-gradient(135deg, {THEME['primary']}, {THEME['accent']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0.5rem 0;
            text-align: center;
        }}
        
        .grade-badge {{
            display: inline-block;
            padding: 0.6rem 2rem;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 1.4rem;
            color: white;
            text-align: center;
            width: 100%;
        }}
        
        .grade-s {{ background-color: #f59e0b; }}
        .grade-a {{ background-color: #10b981; }}
        .grade-b {{ background-color: #3b82f6; }}
        .grade-c {{ background-color: #64748b; }}
        
        section[data-testid="stSidebar"] {{
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0;
        }}
        
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        .custom-footer {{
            margin-top: 5rem;
            padding: 3rem 1rem;
            background-color: #ffffff;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            color: #64748b;
            font-size: 0.9rem;
            line-height: 1.6;
        }}
        
        .report-btn {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: linear-gradient(135deg, #f43f5e, #e11d48);
            color: white !important;
            padding: 0.8rem 1.5rem;
            border-radius: 2rem;
            box-shadow: 0 4px 15px rgba(225, 29, 72, 0.4);
            cursor: pointer;
            z-index: 999;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            border: none;
            transition: all 0.3s ease;
        }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. Core Engine Functions
# ==========================================

def get_kakao_api_key():
    try:
        if "KAKAO_REST_API_KEY" in st.secrets:
            return st.secrets["KAKAO_REST_API_KEY"]
    except:
        pass
    return os.getenv("KAKAO_REST_API_KEY")

@st.cache_data(ttl=3600)
def get_coords_from_address(query: str):
    api_key = get_kakao_api_key()
    if not api_key:
        st.error("카카오 API 키가 설정되지 않았습니다.")
        return None
        
    headers = {"Authorization": f"KakaoAK {api_key}"}
    url_kw = "https://dapi.kakao.com/v2/local/search/keyword.json"
    try:
        res_kw = requests.get(url_kw, headers=headers, params={"query": query, "size": 1}, timeout=5)
        if res_kw.status_code == 200:
            data = res_kw.json()
            if data['documents']:
                info = data['documents'][0]
                return {"address_name": info.get('place_name', info.get('address_name', query)), "lat": float(info['y']), "lng": float(info['x'])}
    except:
        pass

    url_addr = "https://dapi.kakao.com/v2/local/search/address.json"
    try:
        res_addr = requests.get(url_addr, headers=headers, params={"query": query, "size": 1}, timeout=5)
        if res_addr.status_code == 200:
            data = res_addr.json()
            if data['documents']:
                info = data['documents'][0]
                return {"address_name": info['address_name'], "lat": float(info['y']), "lng": float(info['x'])}
    except:
        pass
    return None

@st.cache_data
def load_infrastructure_data():
    file_path = "share/data/seoul_combined_data_final_v3.csv"
    if not os.path.exists(file_path):
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, "..", "data", "seoul_combined_data_final_v3.csv")
    
    try:
        df = pd.read_csv(file_path)
        df_slim = pd.DataFrame()
        df_slim['name'] = df['name']
        df_slim['lat'] = df['latitude']
        df_slim['lon'] = df['longitude']
        df_slim['sub_category'] = df['category_small']
        return df_slim.dropna(subset=['lat', 'lon'])
    except:
        return pd.DataFrame()

def calculate_seulsekwon_index(center_lat, center_lon, data, weights, radius_m):
    if data.empty: return 0.0, {}, {}, [], {}
    radius_km = radius_m / 1000.0
    MAX_CAPS = {"생활/편의🏪": 15, "교통🚌": 8, "의료💊": 5, "안전/치안🚨": 1, "교육/문화📚": 2, "자연/여가🌳": 2, "금융🏦": 3}
    
    lat_margin, lon_margin = radius_km / 111.0, radius_km / 88.0
    mask = (data['lat'].between(center_lat - lat_margin, center_lat + lat_margin)) & (data['lon'].between(center_lon - lon_margin, center_lon + lon_margin))
    candidates = data[mask].copy()

    scores, counts, nearby, raw_progress = {}, {}, [], {}
    for g_name, sub_cats in CATEGORY_GROUPS.items():
        pattern = '|'.join([re.escape(str(sc).lower()) for sc in sub_cats])
        g_data = candidates[candidates['sub_category'].str.lower().str.contains(pattern, na=False)]
        
        unique_group = []
        for _, row in g_data.iterrows():
            dist = geodesic((center_lat, center_lon), (row['lat'], row['lon'])).meters
            if dist <= radius_m:
                d = row.to_dict()
                d['distance'] = dist
                d['group'] = g_name
                d['emoji'] = next((emoji for key, emoji in EMOJI_MAP.items() if key in str(row['sub_category'])), "📍")
                unique_group.append(d)
        
        unique_group = sorted(unique_group, key=lambda x: x['distance'])
        final_group = []
        for item in unique_group:
            if not any(item['name'] == f['name'] and abs(item['distance'] - f['distance']) < 5 for f in final_group):
                final_group.append(item)
        
        counts[g_name] = len(final_group)
        nearby.extend(final_group)
        cap = MAX_CAPS.get(g_name, 5)
        progress = min(counts[g_name], cap) / cap
        raw_progress[g_name] = progress
        scores[g_name] = round(progress * weights.get(g_name, 0), 2)
    
    return round(sum(scores.values()), 1), scores, counts, sorted(nearby, key=lambda x: x['distance']), raw_progress

# ==========================================
# 4. Visualizations & Reports
# ==========================================

def create_viz_objects(total_score, scores, counts, facilities, raw_progress):
    layout_base = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="Pretendard", color=THEME['secondary']))
    
    fig_radar = go.Figure(go.Scatterpolar(r=[v * 100 for v in raw_progress.values()] + [list(raw_progress.values())[0] * 100], theta=list(raw_progress.keys()) + [list(raw_progress.keys())[0]], fill='toself', line=dict(color=THEME['accent'])))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, **layout_base)
    
    fig_gauge = go.Indicator(mode="gauge+number", value=total_score, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': THEME['accent']}})
    
    return {'radar': fig_radar, 'gauge': fig_gauge}

@st.cache_data
def load_real_estate_data():
    file_path = "share/data/seoul_real_estate_combined_2023_2026_geo.csv"
    try:
        df = pd.read_csv(file_path, usecols=['RCPT_YR', 'BLDG_NM', 'THING_AMT', 'ARCH_AREA', 'latitude', 'longitude'])
        df['price_억'] = df['THING_AMT'] / 10000.0
        return df.dropna(subset=['latitude', 'longitude'])
    except:
        return pd.DataFrame()

def render_dashboard():
    st.title("🏙️ 서울 슬세권 분석 대시보드")
    # ... Dashboard UI logic ...
    pass

def main():
    inject_custom_css()
    if 'page' not in st.session_state: st.session_state.page = 'home'
    if 'config' not in st.session_state: st.session_state.config = {'coords': (37.5665, 126.9780), 'address': '서울시청', 'radius': 500}
    
    if st.session_state.page == 'home':
        render_home_page()
    else:
        render_dashboard()

def render_home_page():
    st.markdown("<h1 style='text-align: center;'>SEOUL SEULSEKWON</h1>", unsafe_allow_html=True)
    query = st.text_input("📍 분석할 위치 부근을 검색하세요", placeholder="예: 성수동, 강남역 등")
    if st.button("분석 시작") and query:
        res = get_coords_from_address(query)
        if res:
            st.session_state.config.update({'coords': (res['lat'], res['lng']), 'address': res['address_name']})
            st.session_state.page = 'dashboard'
            st.rerun()

if __name__ == "__main__":
    main()
