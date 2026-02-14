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

# ==========================================
# 2026 Premium Seulsekwon Analytics
# ==========================================

load_dotenv()

# Page Setup
st.set_page_config(
    page_title="서울 실시간 슬세권 리포트",
    page_icon="🏠",
    layout="wide"
)

# Custom Design System (Glassmorphism & Vibrant)
PRIM_COLOR = "#FF385C"  # Airbnb-like Red
BACK_COLOR = "#F7F7F7"
CARD_ACCENT = "rgba(255, 255, 255, 0.9)"

def apply_aesthetic_styles():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap');
    
    .stApp {{
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
    }}
    
    /* Premium Glass Cards */
    .metric-card {{
        background: {CARD_ACCENT};
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 24px;
        border-radius: 24px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        text-align: center;
        margin-bottom: 20px;
    }}
    
    .score-large {{
        font-size: 72px;
        font-weight: 800;
        color: {PRIM_COLOR};
        line-height: 1;
        margin: 10px 0;
    }}
    
    .stMetric {{
        background: white;
        padding: 15px;
        border-radius: 18px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }}
    
    /* Modern Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: white !important;
    }}
    
    /* Inputs */
    .stTextInput input {{
        border-radius: 12px !important;
        border: 1px solid #e0e0e0 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# Core Engine (Self-Contained)
# ==========================================

def get_kakao_client():
    key = os.getenv("KAKAO_REST_API_KEY")
    if not key:
        try: key = st.secrets["KAKAO_REST_API_KEY"]
        except: pass
    return key

def search_locations(query):
    key = get_kakao_client()
    if not key: return []
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {key}"}
    try:
        res = requests.get(url, headers=headers, params={"query": query}, timeout=5)
        if res.status_code == 200:
            docs = res.json().get('documents', [])
            return [{"display_name": d['address_name'] or d['place_name'], "lat": float(d['y']), "lon": float(d['x'])} for d in docs]
    except: pass
    return []

@st.cache_data
def load_data():
    path = "/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/cleaned"
    if not os.path.exists(path): return None
    
    data_files = {
        '스타벅스': 'starbucks_seoul_cleaned.csv',
        '버스정류장': 'bus_station_seoul_cleaned.csv',
        '지하철역': 'metro_station_seoul_cleaned.csv',
        '병원': 'hospital_seoul_cleaned.csv',
        '의원/약국': 'hospital_seoul_cleaned.csv', # Simplified
        '도서관': 'library_seoul_cleaned.csv',
        '학교': 'school_seoul_cleaned.csv',
        '공원': 'park_seoul_cleaned.csv',
        '은행/금융': 'finance_seoul_cleaned.csv'
    }
    
    all_chunks = []
    for cat, fname in data_files.items():
        fpath = os.path.join(path, fname)
        if os.path.exists(fpath):
            try: df = pd.read_csv(fpath, encoding='utf-8-sig')
            except: df = pd.read_csv(fpath, encoding='cp949')
            
            df = df.rename(columns={'위도': 'lat', '경도': 'lon', 'X좌표': 'lon', 'Y좌표': 'lat'})
            if 'lat' in df.columns and 'lon' in df.columns:
                df = df[['lat', 'lon']].dropna()
                df['category'] = cat
                all_chunks.append(df)
    return pd.concat(all_chunks, ignore_index=True) if all_chunks else None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

def calculate_analytics(lat, lon, df, weights, radius_m):
    radius_km = radius_m / 1000.0
    # Pre-filter
    margin = radius_km / 111.0
    df_near = df[(df['lat'].between(lat-margin, lat+margin)) & (df['lon'].between(lon-margin, lon+margin))].copy()
    
    if df_near.empty: return 0, {}, []
    
    df_near['dist_m'] = df_near.apply(lambda r: haversine(lat, lon, r['lat'], r['lon']) * 1000, axis=1)
    df_final = df_near[df_near['dist_m'] <= radius_m].copy()
    
    counts = df_final['category'].value_counts().to_dict()
    # Scoring Logic (Norm to 100)
    scores = {}
    total_score = 0
    
    categories = list(weights.keys())
    for cat in categories:
        cnt = counts.get(cat, 0)
        # Dynamic normalization (cap at reasonable urban density)
        norm = min(cnt / 5.0, 1.0) * 100
        scores[cat] = norm
        total_score += norm * weights[cat]
    
    final_score = total_score / (sum(weights.values()) or 1)
    return final_score, scores, df_final.to_dict('records')

# ==========================================
# Main Application Logic
# ==========================================

def main():
    apply_aesthetic_styles()
    
    data = load_data()
    if data is None:
        st.error("데이터셋을 찾을 수 없습니다. 경로를 확인하세요.")
        st.stop()

    # Sidebar UI
    st.sidebar.title("📍 분석 설정")
    search_q = st.sidebar.text_input("분석 위치 검색", value="서울숲")
    
    if 'search_results' not in st.session_state: st.session_state.search_results = []
    
    if st.sidebar.button("검색", use_container_width=True):
        results = search_locations(search_q)
        st.session_state.search_results = results
        if not results: st.sidebar.warning("검색 결과가 없습니다.")

    selected_loc = None
    if st.session_state.search_results:
        loc_names = [r['display_name'] for r in st.session_state.search_results]
        choice = st.sidebar.selectbox("검색된 주소 선택", loc_names)
        selected_loc = next(r for r in st.session_state.search_results if r['display_name'] == choice)

    radius = st.sidebar.slider("분석 반경 (m)", 300, 1500, 700, 100)
    
    st.sidebar.subheader("⚖️ 가중치")
    cats = ['스타벅스', '버스정류장', '지하철역', '병원', '학교', '공원', '은행/금융']
    weights = {c: st.sidebar.slider(c, 0.0, 2.0, 1.0, 0.1) for c in cats}

    # State for location
    if 'pos' not in st.session_state:
        st.session_state.pos = (37.5446, 127.0440) # Default Seoul Forest
        st.session_state.addr = "서울특별시 성동구 서울숲"

    if st.sidebar.button("실시간 분석 실행", type="primary", use_container_width=True):
        if selected_loc:
            st.session_state.pos = (selected_loc['lat'], selected_loc['lon'])
            st.session_state.addr = selected_loc['display_name']
            st.rerun()

    # Calculation
    f_score, c_scores, facilities = calculate_analytics(st.session_state.pos[0], st.session_state.pos[1], data, weights, radius)

    # Layout
    col_l, col_r = st.columns([1, 2])
    
    with col_l:
        st.markdown(f"""
        <div class="metric-card">
            <h3>종합 슬세권 점수</h3>
            <div class="score-large">{f_score:.1f}</div>
            <p><strong>{st.session_state.addr}</strong> 기준</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Radar
        fig = go.Figure(data=go.Scatterpolar(
            r=list(c_scores.values()),
            theta=list(c_scores.keys()),
            fill='toself',
            line_color=PRIM_COLOR
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, 
                          paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=30, b=30, l=30, r=30))
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("🗺️ 지역 인프라 맵")
        m = folium.Map(location=st.session_state.pos, zoom_start=15, tiles="cartodbpositron")
        folium.Circle(st.session_state.pos, radius=radius, color=PRIM_COLOR, fill=True, fill_opacity=0.08).add_to(m)
        folium.Marker(st.session_state.pos, icon=folium.Icon(color='red', icon='home', prefix='fa')).add_to(m)
        
        for f in facilities[:200]:
            folium.CircleMarker([f['lat'], f['lon']], radius=4, color=PRIM_COLOR, fill=True, 
                                popup=f"{f['category']}").add_to(m)
        
        map_out = st_folium(m, width="100%", height=550)
        if map_out and map_out.get("last_clicked"):
            new_p = (map_out['last_clicked']['lat'], map_out['last_clicked']['lng'])
            if round(new_p[0], 5) != round(st.session_state.pos[0], 5):
                st.session_state.pos = new_p
                st.session_state.addr = f"지정 위치 ({new_p[0]:.4f}, {new_p[1]:.4f})"
                st.rerun()

    st.divider()
    st.subheader("📋 카테고리별 상세 점수")
    m_cols = st.columns(len(c_scores))
    for i, (cat, score) in enumerate(c_scores.items()):
        m_cols[i].metric(cat, f"{score:.1f}")

if __name__ == "__main__":
    main()
