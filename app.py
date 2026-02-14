import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.graph_objects as go
import numpy as np
import os
import requests
import re
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt

# --- Page Configuration ---
st.set_page_config(page_title="서울시 슬세권 지수 대시보드", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS for Premium Look ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="stSidebar"] {
        background-color: #161b22;
    }
    h1, h2, h3 {
        color: #ffffff;
        font-family: 'Outfit', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# --- Utility Functions ---
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def get_coords_from_address(address: str):
    api_key = None
    try:
        if "KAKAO_REST_API_KEY" in st.secrets: 
            api_key = st.secrets["KAKAO_REST_API_KEY"]
    except: 
        pass
    if not api_key: 
        api_key = os.getenv("KAKAO_REST_API_KEY")
    if not api_key: 
        return None
    
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    try:
        response = requests.get(url, headers=headers, params={"query": address})
        if response.status_code == 200:
            result = response.json()
            if result['documents']:
                info = result['documents'][0]
                return {
                    "address_name": info['address_name'], 
                    "lat": float(info['y']), 
                    "lng": float(info['x'])
                }
    except: 
        pass
    return None

def get_dong_name(address):
    if not isinstance(address, str): 
        return "알 수 없음"
    match = re.search(r'([가-힣]+동)', address)
    return match.group(1) if match else "서울시 전체"

@st.cache_data
def load_all_data(data_dir):
    data_files = {
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
    
    combined_data = []
    encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']
    
    for label, filename in data_files.items():
        path = os.path.join(data_dir, filename)
        if os.path.exists(path):
            df = None
            for enc in encodings:
                try:
                    df = pd.read_csv(path, encoding=enc)
                    break
                except (UnicodeDecodeError, pd.errors.ParserError):
                    continue
            
            if df is not None:
                rename_dict = {
                    '위도': 'lat', '경도': 'lon',
                    'lat': 'lat', 'lon': 'lon',
                    'Y좌표': 'lat', 'X좌표': 'lon'
                }
                df = df.rename(columns=rename_dict)
                
                cols = ['lat', 'lon']
                if '점포명' in df.columns: cols.append('점포명')
                elif '역명' in df.columns: cols = ['lat', 'lon', '역명']
                elif '시설명' in df.columns: cols = ['lat', 'lon', '시설명']
                elif '상호명' in df.columns: cols = ['lat', 'lon', '상호명']
                
                if 'lat' in df.columns and 'lon' in df.columns:
                    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
                    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
                    
                    # Create unified name column
                    name_col = None
                    # List of possible name columns across different datasets
                    possible_names = [
                        '점포명', '역명', '시설명', '상호명', '관서명', 
                        '기관명', '학교명', '서점명', '공원명', '도서관명', 
                        '사업장명', '명칭'
                    ]
                    for c in possible_names:
                        if c in df.columns:
                            name_col = c
                            break
                    
                    if name_col:
                        df = df.rename(columns={name_col: '시설명'})
                    else:
                        df['시설명'] = '정보 없음'
                        
                    df = df[['lat', 'lon', '시설명']].dropna(subset=['lat', 'lon'])
                    df['category'] = label
                    combined_data.append(df)
            
    if not combined_data:
        return pd.DataFrame(columns=['lat', 'lon', '시설명', 'category'])
        
    return pd.concat(combined_data, ignore_index=True)

# --- Data Loading ---
DATA_DIR = "/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/cleaned"
raw_df = load_all_data(DATA_DIR)

# --- Sidebar ---
st.sidebar.title("🏙️ 슬세권 설정")

st.sidebar.subheader("⚖️ 가중치 설정")
w_traffic = st.sidebar.slider("교통 (지하철, 버스)", 0, 100, 30)
w_life = st.sidebar.slider("생활/상권 (스타벅스, 소상공인, 대형마트)", 0, 100, 25)
w_safety = st.sidebar.slider("안전/공공 (경찰, 병원, 금융)", 0, 100, 20)
w_culture = st.sidebar.slider("문화/환경 (공원, 서점, 도서관, 학교)", 0, 100, 25)

total_w = w_traffic + w_life + w_safety + w_culture
if total_w == 0: total_w = 1

st.sidebar.subheader("📏 분석 반경")
radius_val = 0.5 # 500m 고정
st.sidebar.write(f"현재 분석 반경: {radius_val*1000:.0f}m (고정)")

st.sidebar.subheader("🔍 필터")
categories = raw_df['category'].unique().tolist()
selected_cats = st.sidebar.multiselect("표시할 인프라", categories, default=categories)

# --- Main Page ---
st.title("🚀 서울시 슬세권 지수 대시보드")
st.markdown("전문화된 생활 인프라 데이터를 기반으로 한 지역 편의도 분석")

# Layout: Map and KPI
col1, col2 = st.columns([3, 1])

with col2:
    st.subheader("📍 지점 분석")
    st.info("주소를 입력하여 해당 지점을 기준으로 슬세권 지수를 산출합니다.")
    
    search_address = st.text_input("분석할 주소 입력", value="서울특별시 중구 세종대로 110")
    
    if search_address:
        result = get_coords_from_address(search_address)
        if result:
            target_lat = result['lat']
            target_lon = result['lng']
            dong_name = get_dong_name(result['address_name'])
            st.success(f"📍 검색 결과: {result['address_name']} ({dong_name})")
        else:
            st.warning("주소를 찾을 수 없거나 API 키가 설정되지 않았습니다. 기본 위치(서울시청)로 설정합니다.")
            target_lat, target_lon = 37.5665, 126.9780
    else:
        target_lat, target_lon = 37.5665, 126.9780

    with st.expander("위경도 좌표 보기"):
        st.write(f"위도: {target_lat:.5f}, 경도: {target_lon:.5f}")

    counts = {}
    for cat in categories:
        cat_df = raw_df[raw_df['category'] == cat]
        dist_threshold = radius_val
        lat_margin = dist_threshold / 111.0
        lon_margin = dist_threshold / 88.0
        
        mask = (cat_df['lat'] > target_lat - lat_margin) & (cat_df['lat'] < target_lat + lat_margin) & \
               (cat_df['lon'] > target_lon - lon_margin) & (cat_df['lon'] < target_lon + lon_margin)
        
        filtered = cat_df[mask].copy()
        if not filtered.empty:
            filtered['dist'] = filtered.apply(lambda row: haversine(target_lon, target_lat, row['lon'], row['lat']), axis=1)
            counts[cat] = len(filtered[filtered['dist'] <= dist_threshold])
        else:
            counts[cat] = 0

    score_traffic = (counts.get("지하철", 0) * 5 + counts.get("버스", 0)) / 10 * 100
    score_life = (counts.get("스타벅스", 0) * 3 + counts.get("소상공인", 0) * 0.1 + counts.get("대형마트", 0) * 2) / 10 * 100
    score_safety = (counts.get("경찰", 0) * 2 + counts.get("병원", 0) * 1 + counts.get("금융", 0) * 0.5) / 5 * 100
    score_culture = (counts.get("공원", 0) * 3 + counts.get("서점", 0) * 1 + counts.get("도서관", 0) * 1 + counts.get("학교", 0) * 0.5) / 5 * 100

    score_traffic = min(score_traffic, 100)
    score_life = min(score_life, 100)
    score_safety = min(score_safety, 100)
    score_culture = min(score_culture, 100)
    
    final_index = (score_traffic * w_traffic + score_life * w_life + score_safety * w_safety + score_culture * w_culture) / total_w
    
    st.metric("종합 슬세권 지수", f"{final_index:.1f} / 100")
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[score_traffic, score_life, score_safety, score_culture],
        theta=['교통', '생활/상권', '안전/공공', '문화/환경'],
        fill='toself',
        name='지역 인프라 밸런스',
        line_color='#00ffcc'
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color="#ffffff"),
            bgcolor="#1e2130"
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

with col1:
    view_state = pdk.ViewState(latitude=target_lat, longitude=target_lon, zoom=14, pitch=45)
    
    map_df = raw_df[raw_df['category'].isin(selected_cats)].copy()
    
    cat_colors = {
        "지하철": [255, 0, 0],
        "버스": [255, 165, 0],
        "스타벅스": [0, 128, 0],
        "서점": [128, 0, 128],
        "경찰": [0, 0, 255],
        "병원": [255, 192, 203],
        "금융": [255, 215, 0],
        "도서관": [0, 255, 255],
        "공원": [34, 139, 34],
        "학교": [165, 42, 42],
        "소상공인": [128, 128, 128],
        "대형마트": [0, 0, 128]
    }
    
    map_df['distance'] = map_df.apply(lambda row: haversine(target_lon, target_lat, row['lon'], row['lat']), axis=1)
    map_df['is_within'] = map_df['distance'] <= radius_val
    
    # Base layers
    # 1. Radius Circle
    radius_data = pd.DataFrame([{"lat": target_lat, "lon": target_lon}])
    radius_layer = pdk.Layer(
        "ScatterplotLayer",
        radius_data,
        get_position='[lon, lat]',
        get_radius=radius_val * 1000,
        get_fill_color=[0, 255, 204, 30],
        get_line_color=[0, 255, 204, 150],
        line_width_min_pixels=2,
        stroked=True,
        filled=True,
    )
    
    # 2. Main points (smaller and faded if outside)
    map_df['color'] = map_df['category'].map(cat_colors)
    map_df['radius'] = map_df['is_within'].apply(lambda x: 40 if x else 15)
    map_df['opacity'] = map_df['is_within'].apply(lambda x: 255 if x else 60)
    
    points_layer = pdk.Layer(
        "ScatterplotLayer",
        map_df,
        get_position='[lon, lat]',
        get_color='[color[0], color[1], color[2], opacity]',
        get_radius='radius',
        pickable=True,
    )
    
    # 3. Center point marker
    center_layer = pdk.Layer(
        "ScatterplotLayer",
        radius_data,
        get_position='[lon, lat]',
        get_radius=20,
        get_fill_color=[255, 255, 255],
        get_line_color=[0, 0, 0],
        line_width_min_pixels=2,
        stroked=True,
        filled=True,
    )

    r = pdk.Deck(
        layers=[radius_layer, points_layer, center_layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v10",
        tooltip={"text": "{category}"}
    )
    
    st.pydeck_chart(r)

# --- Bottom Area ---
st.divider()
st.subheader("📋 인근 주요 시설 목록")

near_df = map_df[map_df['is_within']].sort_values('distance')

if not near_df.empty:
    tab_all, tab_cat = st.tabs(["전체", "인프라별"])
    
    with tab_all:
        display_df = near_df[['category', '시설명', 'distance']].copy()
        display_df['distance'] = display_df['distance'].apply(lambda x: f"{x*1000:.0f}m")
        display_df = display_df.rename(columns={'category': '분류', 'distance': '거리'})
        st.dataframe(display_df.head(100), use_container_width=True)
        
    with tab_cat:
        available_cats = sorted(near_df['category'].unique())
        if available_cats:
            selected_tab_cat = st.selectbox("조회할 인프라 선택", available_cats)
            filtered_cat_df = near_df[near_df['category'] == selected_tab_cat].copy()
            filtered_cat_df['distance'] = filtered_cat_df['distance'].apply(lambda x: f"{x*1000:.0f}m")
            filtered_cat_df = filtered_cat_df[['시설명', 'distance']].rename(columns={'distance': '거리'})
            st.dataframe(filtered_cat_df, use_container_width=True)
        else:
            st.write("표시할 인프라가 없습니다.")
else:
    st.write("반경 500m 내 시설이 없습니다.")

st.sidebar.markdown("---")
st.sidebar.caption("Data Source: Seoul Open Data Plaza & Custom Cleaned Dataset")
