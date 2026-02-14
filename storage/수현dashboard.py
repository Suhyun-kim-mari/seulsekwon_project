import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import numpy as np
import os
import requests
import re
from math import radians, cos, sin, asin, sqrt
from dotenv import load_dotenv
import datetime

# ==========================================
# 1. Configuration & Initial Setup
# ==========================================

load_dotenv()

st.set_page_config(
    page_title="서울시 슬세권 지수 대시보드 v2.1",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Colors & Styles (Toss-like Clean Design)
TOSS_BLUE = "#3182f6"
TOSS_GRAY_BG = "#f9fafb"
TOSS_TEXT_MAIN = "#191f28"
TOSS_TEXT_MUTED = "#8b95a1"

# ==========================================
# 2. Custom CSS
# ==========================================

def inject_styles():
    st.markdown(f"""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {{
        font-family: 'Pretendard', -apple-system, sans-serif;
    }}
    
    .stApp {{
        background-color: {TOSS_GRAY_BG};
    }}
    
    /* Metric Cards */
    div[data-testid="stMetric"] {{
        background-color: #ffffff;
        padding: 24px;
        border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        border: 1px solid #f2f4f6;
    }}
    
    div[data-testid="stMetricValue"] {{
        color: {TOSS_BLUE} !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
    }}
    
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: #ffffff;
        border-right: 1px solid #f2f4f6;
    }}
    
    /* Buttons */
    .stButton > button {{
        background-color: {TOSS_BLUE} !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 10px 20px !important;
        border: none !important;
        font-weight: 600 !important;
    }}
    
    /* Titles */
    h1, h2, h3 {{
        color: {TOSS_TEXT_MAIN} !important;
        letter-spacing: -0.5px;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. Kakao API Handler Class
# ==========================================

class KakaoLocalService:
    def __init__(self):
        self.api_key = self._load_key()
        self.headers = {"Authorization": f"KakaoAK {self.api_key}"} if self.api_key else {}

    def _load_key(self):
        try:
            if "KAKAO_REST_API_KEY" in st.secrets:
                return st.secrets["KAKAO_REST_API_KEY"]
        except: pass
        return os.getenv("KAKAO_REST_API_KEY")

    def search_location(self, query):
        if not self.api_key:
            return {"status": "error", "message": "API Key missing."}
        
        # 1. Try Keyword Search first
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        try:
            resp = requests.get(url, headers=self.headers, params={"query": query}, timeout=5)
            if resp.status_code == 200:
                docs = resp.json().get('documents', [])
                if docs:
                    return self._format_res(docs[0], "keyword")
            
            # 2. Try Address Search if keyword fails
            url = "https://dapi.kakao.com/v2/local/search/address.json"
            resp = requests.get(url, headers=self.headers, params={"query": query}, timeout=5)
            if resp.status_code == 200:
                docs = resp.json().get('documents', [])
                if docs:
                    return self._format_res(docs[0], "address")
        except Exception as e:
            return {"status": "error", "message": str(e)}
        return {"status": "fail", "message": "No results found."}

    def _format_res(self, doc, source):
        return {
            "status": "success",
            "name": doc['address_name'] or doc.get('place_name', ""),
            "lat": float(doc['y']),
            "lon": float(doc['x']),
            "source": source
        }

# ==========================================
# 4. Utilities
# ==========================================

def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine distance in km."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * asin(sqrt(a)) * 6371

@st.cache_data
def load_all_datasets():
    data_dir = "/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/cleaned"
    if not os.path.exists(data_dir):
        return pd.DataFrame()

    files = {
        "지하철": "metro_station_seoul_cleaned.csv",
        "버스": "bus_station_seoul_cleaned.csv",
        "스타벅스": "starbucks_seoul_cleaned.csv",
        "서점": "bookstore_seoul_cleaned.csv",
        "경찰": "police_seoul_cleaned_ver2.csv",
        "병원": "hospital_seoul_cleaned.csv",
        "금융": "finance_seoul_cleaned.csv",
        "도서관": "library_seoul_cleaned.csv",
        "공원": "park_seoul_cleaned.csv",
        "학교": "school_seoul_cleaned.csv",
        "소상공인": "sosang_seoul_cleaned.csv",
        "대형마트": "large_scale_shop_seoul_cleaned.csv"
    }
    
    combined = []
    for label, fname in files.items():
        path = os.path.join(data_dir, fname)
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, encoding='utf-8-sig')
            except:
                df = pd.read_csv(path, encoding='cp949')
            
            # Column mapping
            df = df.rename(columns={'위도': 'lat', '경도': 'lon', 'X좌표': 'lon', 'Y좌표': 'lat'})
            
            # Name resolution
            name_candidates = ['시설명', '점포명', '상호명', '역명', '관서명', '학교명', '공원명', '이름', '정류소명']
            df['name'] = 'Unknown'
            for c in name_candidates:
                if c in df.columns:
                    df['name'] = df[c]
                    break
            
            if 'lat' in df.columns and 'lon' in df.columns:
                df = df[['lat', 'lon', 'name']].dropna()
                df['category'] = label
                combined.append(df)
                
    return pd.concat(combined, ignore_index=True) if combined else pd.DataFrame()

def get_seulsekwon_index(counts, weights):
    # Maximum caps for normalization
    CAPS = {
        "지하철": 2, "버스": 10, "스타벅스": 3, "소상공인": 50, 
        "병원": 5, "경찰": 1, "금융": 5, "공원": 2, "도서관": 1, "서점": 2, "학교": 3, "대형마트": 1
    }
    
    scores = {}
    for cat, cap in CAPS.items():
        cnt = counts.get(cat, 0)
        scores[cat] = min(cnt / cap, 1.0) * 100
        
    groups = {
        "교통": (scores.get("지하철", 0) * 0.7 + scores.get("버스", 0) * 0.3),
        "생활": (scores.get("스타벅스", 0) * 0.4 + scores.get("소상공인", 0) * 0.4 + scores.get("대형마트", 0) * 0.2),
        "안전": (scores.get("경찰", 0) * 0.4 + scores.get("병원", 0) * 0.4 + scores.get("금융", 0) * 0.2),
        "문화": (scores.get("공원", 0) * 0.3 + scores.get("도서관", 0) * 0.3 + scores.get("서점", 0) * 0.2 + scores.get("학교", 0) * 0.2)
    }
    
    total_w = sum(weights.values())
    if total_w == 0: return 0, groups
    
    total_idx = sum(groups[k] * weights[k] for k in groups) / total_w
    return total_idx, groups

# ==========================================
# 5. UI & Main Execution
# ==========================================

def run():
    inject_styles()
    
    # Init Data
    raw_df = load_all_datasets()
    if raw_df.empty:
        st.error("Data files not found.")
        st.stop()
    
    # Sidebar
    st.sidebar.title("🔍 슬세권 분석")
    kakao = KakaoLocalService()
    
    if not kakao.api_key:
        st.sidebar.error("KAKAO_REST_API_KEY is missing.")
    
    address_query = st.sidebar.text_input("분석 지점 입력", value="서울시청")
    btn_search = st.sidebar.button("분석 시작", use_container_width=True)
    
    st.sidebar.divider()
    st.sidebar.subheader("⚖️ 가중치 설정 (%)")
    w_traffic = st.sidebar.slider("교통", 0, 100, 30)
    w_life = st.sidebar.slider("생활", 0, 100, 25)
    w_safety = st.sidebar.slider("안전", 0, 100, 20)
    w_culture = st.sidebar.slider("문화", 0, 100, 25)
    
    # State Management
    if 'target' not in st.session_state:
        st.session_state['target'] = {"lat": 37.5665, "lon": 126.9780, "name": "서울시청"}
    
    if btn_search:
        res = kakao.search_location(address_query)
        if res['status'] == 'success':
            st.session_state['target'] = res
            st.rerun()
        else:
            st.sidebar.error(res['message'])
            
    # Calculation
    radius_km = 0.5
    target = st.session_state['target']
    
    df_near = raw_df.copy()
    # Broad filtering for performance
    deg_limit = radius_km / 111.0
    df_near = df_near[
        (df_near['lat'].between(target['lat'] - deg_limit, target['lat'] + deg_limit)) &
        (df_near['lon'].between(target['lon'] - deg_limit, target['lon'] + deg_limit))
    ]
    
    if not df_near.empty:
        df_near['dist'] = df_near.apply(lambda r: calculate_distance(target['lat'], target['lon'], r['lat'], r['lon']), axis=1)
        df_final = df_near[df_near['dist'] <= radius_km].copy()
    else:
        df_final = pd.DataFrame(columns=raw_df.columns.tolist() + ['dist'])
        
    counts = df_final['category'].value_counts().to_dict()
    weights = {"교통": w_traffic, "생활": w_life, "안전": w_safety, "문화": w_culture}
    final_idx, group_scores = get_seulsekwon_index(counts, weights)
    
    # UI Render
    st.title("🏙️ 서울시 슬세권 지수 대시보드")
    st.markdown(f"**분석 위치:** {target['name']}")
    
    # Metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("종합 지수", f"{final_idx:.1f}")
    m2.metric("교통", f"{group_scores['교통']:.1f}")
    m3.metric("생활", f"{group_scores['생활']:.1f}")
    m4.metric("안전", f"{group_scores['안전']:.1f}")
    m5.metric("문화", f"{group_scores['문화']:.1f}")
    
    st.divider()
    
    # Content Area
    col_map, col_stat = st.columns([2, 1])
    
    with col_map:
        st.subheader("🗺️ 인프라 맵")
        m = folium.Map(location=[target['lat'], target['lon']], zoom_start=15, tiles="CartoDB positron")
        folium.Circle([target['lat'], target['lon']], radius=radius_km*1000, color=TOSS_BLUE, fill=True, fill_opacity=0.05).add_to(m)
        folium.Marker([target['lat'], target['lon']], icon=folium.Icon(color='black', icon='home', prefix='fa')).add_to(m)
        
        # Display markers (capped for performance)
        for _, r in df_final.head(100).iterrows():
            folium.Marker(
                [r['lat'], r['lon']], 
                popup=r['name'], 
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
            
        st_folium(m, width="100%", height=500, returned_objects=[])

    with col_stat:
        st.subheader("📊 지표 밸런스")
        fig = go.Figure(data=go.Scatterpolar(
            r=[group_scores[k] for k in ["교통", "생활", "안전", "문화"]],
            theta=["교통", "생활", "안전", "문화"],
            fill='toself',
            line=dict(color=TOSS_BLUE),
            fillcolor='rgba(49, 130, 246, 0.2)'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            margin=dict(t=30, b=30, l=30, r=30),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
        
    # Table
    st.divider()
    st.subheader("📋 주변 시설 상세")
    if not df_final.empty:
        st.dataframe(
            df_final.sort_values('dist').iloc[:, [3, 2, 4]].rename(columns={'category': '분류', 'name': '시설명', 'dist': '거리(km)'}),
            use_container_width=True,
            height=300
        )
    else:
        st.info("No facilities found in range.")

if __name__ == "__main__":
    run()
