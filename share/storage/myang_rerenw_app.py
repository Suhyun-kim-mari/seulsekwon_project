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
# .env 파일 로드 (부모 디렉토리의 .env 탐색)
import os
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))

# 예상되는 .env 위치 후보들
possible_paths = [
    os.path.join(current_dir, '.env'), # 현재 디렉토리
    os.path.join(os.path.dirname(os.path.dirname(current_dir)), '.env'), # seoul_seulsekwon/.env (2단계 위)
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), '.env'), # 그 위
]

env_path = None
for path in possible_paths:
    if os.path.exists(path):
        env_path = path
        break

# .env 파일이 발견되면 로드, 없으면 경고 메시지 출력 (혹은 무시)
if env_path:
    load_dotenv(env_path)
    print(f".env loaded from: {env_path}") # 디버깅용 출력
else:
    print("Warning: .env file not found.")

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) # 기존 base_dir 유지 (seulsekwon_project)

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
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {{
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0;
        }}
        
        /* Hide menu */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        /* Footer Styling */
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
        
        .footer-content {{
            max-width: 800px;
            margin: 0 auto;
        }}
        
        .footer-links {{
            margin-top: 1rem;
            display: flex;
            justify-content: center;
            gap: 2rem;
        }}

        /* Floating Report Button */
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
        
        .report-btn:hover {{
            transform: scale(1.05);
            box-shadow: 0 6px 20px rgba(225, 29, 72, 0.6);
        }}
        
        /* Home Page Styles */
        .hero-section {{
            padding: 6rem 2rem;
            text-align: center;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-radius: 2rem;
            color: white;
            margin-bottom: 3rem;
        }}
        
        .hero-title {{
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, #60a5fa, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .intro-section {{
            padding: 4rem 1rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }}
        
        .team-card {{
            background: white;
            padding: 1.5rem 1rem;
            border-radius: 1rem;
            border: 1px solid #f1f5f9;
            text-align: center;
            transition: all 0.3s ease;
            height: 100%;
        }}
        
        .team-card:hover {{
            border-color: #3b82f6;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }}
        
        .team-avatar {{
            width: 70px;
            height: 70px;
            background: #f8fafc;
            border-radius: 50%;
            margin: 0 auto 1rem auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.2rem;
            border: 2px solid #eff6ff;
        }}
        
        .member-name {{
            font-size: 1.05rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.2rem;
        }}
        
        .member-role-title {{
            font-size: 0.85rem;
            font-weight: 600;
            color: #3b82f6;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        /* Updated Search Bar Style (Pill Shape with Icon) */
        div[data-testid="stForm"] {{
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
        }}
        
        .search-container {{
            max-width: 650px;
            margin: 0 auto;
            position: relative;
        }}
        
        div[data-testid="stTextInput"] input {{
            border-radius: 2.5rem !important;
            padding: 1rem 3rem 1rem 1.5rem !important;
            font-size: 1rem !important;
            border: 1px solid #e0e0e0 !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="%23999" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>');
            background-repeat: no-repeat;
            background-position: right 1.5rem center;
            background-size: 1.2rem;
            transition: all 0.3s ease;
        }}
        
        div[data-testid="stTextInput"] input:focus {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
            border-color: #3b82f6 !important;
            outline: none !important;
        }}
        
        div[data-testid="stTextInput"] input::placeholder {{
            color: #9e9e9e !important;
            opacity: 1;
        }}

        .search-sample-text {{
            text-align: center;
            margin-top: 1.5rem;
            color: #70757a;
            font-size: 0.9rem;
        }}
        
        .stButton > button, div[data-testid="stFormSubmitButton"] > button {{
            border-radius: 2.5rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }}
        
        div[data-testid="stFormSubmitButton"] > button {{
            background: linear-gradient(135deg, #f43f5e, #e11d48) !important;
            color: white !important;
            border: none !important;
            height: 3rem !important;
            padding: 0 1.5rem !important;
        }}
        
        div[data-testid="stFormSubmitButton"] > button:hover {{
            box-shadow: 0 4px 12px rgba(225, 29, 72, 0.4) !important;
            transform: translateY(-1px) !important;
        }}
        
        /* Sample Keyword Buttons Styling (Shadow no border) */
        div[data-testid="column"] button:not([kind="primary"]) {{
            border: none !important;
            background-color: white !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.06) !important;
            color: #4b5563 !important;
            font-size: 0.85rem !important;
            padding: 0.5rem 1rem !important;
            height: auto !important;
            min-height: 2.2rem !important;
        }}
        
        div[data-testid="column"] button:not([kind="primary"]):hover {{
            box-shadow: 0 6px 15px rgba(0,0,0,0.1) !important;
            color: {THEME['primary']} !important;
            transform: translateY(-1px);
        }}
        
        .member-tasks {{
            font-size: 0.8rem;
            color: #64748b;
            text-align: left;
            margin-top: 1rem;
            padding-left: 0;
            list-style: none;
        }}
        
        .member-tasks li {{
            margin-bottom: 0.3rem;
            display: flex;
            align-items: flex-start;
            gap: 0.4rem;
        }}
        
        .member-tasks li::before {{
            content: "•";
            color: #cbd5e1;
        }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. Core Engine Functions
# ==========================================

def get_kakao_api_key():
    """kakao_api_key를 secrets 또는 env에서 가져옵니다."""
    try:
        if "KAKAO_REST_API_KEY" in st.secrets:
            return st.secrets["KAKAO_REST_API_KEY"]
    except:
        pass
    return os.getenv("KAKAO_REST_API_KEY")

@st.cache_data(ttl=3600)
def get_coords_from_address(query: str):
    """주소 또는 장소명(ex. 강남경찰서)으로 좌표를 검색합니다. (키워드 -> 주소 순차 검색)"""
    api_key = get_kakao_api_key()
    if not api_key:
        st.error("카카오 API 키가 설정되지 않았습니다.")
        return None
        
    headers = {"Authorization": f"KakaoAK {api_key}"}

    # 1. 키워드 검색 시도 (장소명 위주)
    url_kw = "https://dapi.kakao.com/v2/local/search/keyword.json"
    try:
        res_kw = requests.get(url_kw, headers=headers, params={"query": query, "size": 1}, timeout=5)
        if res_kw.status_code == 200:
            data = res_kw.json()
            if data['documents']:
                info = data['documents'][0]
                return {
                    "address_name": info.get('road_address_name', info.get('address_name', info.get('place_name', query))),
                    "lat": float(info['y']),
                    "lng": float(info['x'])
                }
        elif res_kw.status_code == 401 and "ip mismatched" in res_kw.text:
            st.error("❌ 카카오 API IP 인증 오류가 발생했습니다. 개발자 센터에 현재 서버 IP를 등록해주세요.")
    except Exception as e:
        pass # 키워드 실패 시 주소 검색으로 넘어감

    # 2. 주소 검색 시도 (새주소, 지번주소 위주)
    url_addr = "https://dapi.kakao.com/v2/local/search/address.json"
    try:
        res_addr = requests.get(url_addr, headers=headers, params={"query": query, "size": 1}, timeout=5)
        if res_addr.status_code == 200:
            data = res_addr.json()
            if data['documents']:
                info = data['documents'][0]
                # 도로명 주소를 1순위로, 지번 주소를 2순위로 반환
                addr_name = info['address_name']
                if info.get('road_address'):
                    addr_name = info['road_address']['address_name']
                
                return {
                    "address_name": addr_name,
                    "lat": float(info['y']),
                    "lng": float(info['x'])
                }
    except Exception as e:
        st.error(f"좌표 변환 중 예외 발생: {e}")

    return None

@st.cache_data(ttl=3600)
def get_address_from_coords(lat: float, lng: float):
    """좌표를 주소로 변환합니다. (역지오코딩)"""
    api_key = get_kakao_api_key()
    if not api_key:
        return f"주소 정보 없음 (좌표: {lat:.4f}, {lng:.4f})"
        
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    try:
        res = requests.get(url, headers=headers, params={"x": lng, "y": lat}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data['documents']:
                info = data['documents'][0]
                # 도로명 주소를 1순위로, 지번 주소를 2순위로 반환
                if info.get('road_address'):
                    return info['road_address']['address_name']
                if info.get('address'):
                    return info['address']['address_name']
    except:
        pass
    return f"서울시 (지정 좌표: {lat:.4f}, {lng:.4f})"

def get_dong_name(address):
    """주소에서 행정동 이름을 추출합니다."""
    if not isinstance(address, str):
        return "알 수 없음"
    match = re.search(r'([가-힣]+동)', address)
    return match.group(1) if match else "서울시"

@st.cache_data
def load_infrastructure_data():
    """최종 통합된 인프라 데이터를 로드합니다."""
    # 최종 통합 및 중복 제거된 데이터 파일 경로
    file_path = "/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/share/data/seoul_combined_data_final_v3.csv"
    
    if not os.path.exists(file_path):
        # 상대 경로 시도
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, "..", "data", "seoul_combined_data_final_v3.csv")
        
        if not os.path.exists(file_path):
            st.error(f"데이터 파일을 찾을 수 없습니다: {file_path}")
            return pd.DataFrame()

    try:
        df = pd.read_csv(file_path)
        
        # 내부 스키마에 맞게 컬럼명 매핑 (lat, lon, sub_category)
        df_slim = pd.DataFrame()
        df_slim['name'] = df['name']
        df_slim['lat'] = df['latitude']
        df_slim['lon'] = df['longitude']
        df_slim['sub_category'] = df['category_small']
        
        # 유효성 검사 및 정제
        df_slim = df_slim.dropna(subset=['lat', 'lon'])
        
        return df_slim
    except Exception as e:
        st.error(f"데이터 파일을 읽는 중 오류 발생: {e}")
        return pd.DataFrame()

def calculate_seulsekwon_index(center_lat, center_lon, data, weights, radius_m):
    """슬세권 지수를 계산하고 주변 시설을 반환합니다."""
    if data.empty:
        return 0.0, {}, {}, [], {}

    radius_km = radius_m / 1000.0
    # 카테고리별 정상 기여 최대치 (도심 기준)
    MAX_CAPS = {
        "생활/편의🏪": 15, "교통🚌": 8, "의료💊": 5, 
        "안전/치안🚨": 1, "교육/문화📚": 2, "자연/여가🌳": 2, "금융🏦": 3
    }
    
    # 1차 공간 필터링 (사각형 범위)
    lat_margin, lon_margin = radius_km / 111.0, radius_km / 88.0
    mask = (data['lat'].between(center_lat - lat_margin, center_lat + lat_margin)) & \
           (data['lon'].between(center_lon - lon_margin, center_lon + lon_margin))
    candidates = data[mask].copy()

    scores, counts, nearby, raw_progress = {}, {}, [], {}
    
    for g_name, sub_cats in CATEGORY_GROUPS.items():
        # 서브 카테고리 매칭 (부분 일치)
        pattern = '|'.join([re.escape(str(sc).lower()) for sc in sub_cats])
        g_data = candidates[candidates['sub_category'].str.lower().str.contains(pattern, na=False)]
        
        group_facilities = []
        for _, row in g_data.iterrows():
            dist = geodesic((center_lat, center_lon), (row['lat'], row['lon'])).meters
            if dist <= radius_m:
                d = row.to_dict()
                d['distance'] = dist
                d['group'] = g_name
                d['emoji'] = next((emoji for key, emoji in EMOJI_MAP.items() if key in str(row['sub_category'])), "📍")
                group_facilities.append(d)
        
        # 그룹 내 거리 기반 중복 제거 (같은 이름 && 거리차 < 5m)
        group_facilities = sorted(group_facilities, key=lambda x: x['distance'])
        unique_group_facilities = []
        seen_names = set()
        for item in group_facilities:
            is_dup = False
            for u_item in unique_group_facilities:
                if item['name'] == u_item['name'] and abs(item['distance'] - u_item['distance']) < 5:
                    is_dup = True
                    break
            if not is_dup:
                unique_group_facilities.append(item)
        
        counts[g_name] = len(unique_group_facilities)
        nearby.extend(unique_group_facilities)
        
        cap = MAX_CAPS.get(g_name, 5)
        progress = min(counts[g_name], cap) / cap
        raw_progress[g_name] = progress
        scores[g_name] = round(progress * weights.get(g_name, 0), 2)
    
    nearby = sorted(nearby, key=lambda x: x['distance'])
    total_score = round(sum(scores.values()), 1)
    
    return total_score, scores, counts, nearby, raw_progress

# ==========================================
# 4. Visualizations
# ==========================================

def create_viz_objects(total_score, scores, counts, facilities, raw_progress):
    """보고서 및 대시보드용 시각화 객체를 생성합니다."""
    layout_base = dict(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(family="Pretendard", color=THEME['secondary'])
    )
    
    # Radar Chart
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[v * 100 for v in raw_progress.values()] + [list(raw_progress.values())[0] * 100],
        theta=list(raw_progress.keys()) + [list(raw_progress.keys())[0]],
        fill='toself',
        fillcolor='rgba(99, 102, 241, 0.2)',
        line=dict(color=THEME['accent'], width=2),
        name='카테고리 달성도'
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False, **layout_base
    )
    
    # Gauge Chart (종합 점수 게이지 차트)
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", 
        value=total_score,
        number={'font': {'size': 40, 'color': THEME['primary']}, 'suffix': "점"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': THEME['secondary']}, 
            'bar': {'color': "#6366f1"}, # 메인 바 색상 (Indigo)
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e2e8f0",
            'steps': [
                {'range': [0, 40], 'color': "#fee2e2"},   # Low (Reddish)
                {'range': [40, 70], 'color': "#fef9c3"},  # Medium (Yellowish)
                {'range': [70, 90], 'color': "#dcfce7"},  # High (Greenish)
                {'range': [90, 100], 'color': "#dbeafe"}  # Excellent (Blueish)
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': total_score
            }
        }
    ))
    fig_gauge.update_layout(
        height=280, 
        margin=dict(t=50, b=20, l=30, r=30), 
        **layout_base
    )
    
    # 인프라 구성 비율 비교를 위한 데이터 준비
    # 1. 서울 도심 평균 데이터 (비교용 기준 데이터)
    SEOUL_AVG = {"생활/편의🏪": 20, "교통🚌": 15, "의료💊": 12, "안전/치안🚨": 8, "교육/문화📚": 5, "자연/여가🌳": 12, "금융🏦": 5}
    s_total = sum(SEOUL_AVG.values())
    s_perc = {k: (v/s_total)*100 for k, v in SEOUL_AVG.items()} # 서울 평균의 카테고리별 비중(%)
    
    # 2. 현재 분석 지점의 데이터 비중 계산
    d_total = sum(scores.values()) or 1
    d_perc = {k: (v/d_total)*100 for k, v in scores.items()}    # 현재 지점의 카테고리별 비중(%)
    
    # 인프라 구성 비율 비교 (현재 지점 vs 서울 평균) 시각화 객체 생성
    fig_compare = go.Figure()
    for cat in scores.keys():
        # 막대 위에 표시될 데이터 라벨 (항목명 + 백분율)
        # 예: "교통🚌<br>20.5%"
        text_labels = [f"{cat}<br>{d_perc[cat]:.1f}%", f"{cat}<br>{s_perc[cat]:.1f}%"]
        
        fig_compare.add_trace(go.Bar(
            name=cat, 
            x=["현재 지점", "서울 평균"], 
            y=[d_perc[cat], s_perc[cat]],
            text=text_labels,             # 막대 위에 텍스트 표시
            textposition='auto',           # 텍스트 위치 자동 최적화
            hovertemplate="%{x}<br>%{y:.1f}%" # 마우스 오버 시 상세 정보 표시
        ))
        
    fig_compare.update_layout(

        barmode='stack', 
        height=500, 
        showlegend=True,
        legend=dict(orientation="h", y=-0.2), 
        **layout_base
    )
    
    return {'radar': fig_radar, 'gauge': fig_gauge, 'compare': fig_compare}

def create_folium_map(lat, lon, facilities, radius_m):
    """주변 시설 포함 지도를 생성합니다."""
    m = folium.Map(location=[lat, lon], zoom_start=16, tiles="cartodbpositron")
    folium.Circle([lat, lon], radius=radius_m, color=THEME['primary'], fill=True, fill_opacity=0.05).add_to(m)
    folium.Marker([lat, lon], icon=folium.Icon(color='red', icon='home', prefix='fa'), tooltip="내 중심지").add_to(m)
    
    for f in facilities[:300]: # 성능 최적화를 위해 300개 제한
        html = f"""
        <div style="font-size: 14px; background: white; border-radius: 50%; width: 24px; height: 24px; 
        display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        border: 2px solid {THEME['accent']};">
            {f['emoji']}
        </div>
        """
        folium.Marker(
            [f['lat'], f['lon']], 
            icon=folium.DivIcon(html=html),
            popup=f"<b>{f['name']}</b><br>{f['distance']:.0f}m ({f['sub_category']})"
        ).add_to(m)
    return m

# --- 신규 추가: AI 분석 및 부동산 데이터 관련 함수 ---

def get_ai_analysis_report(t_score, counts, weights):
    """인프라 데이터를 기반으로 현실적인 지역 특성 요약 리포트를 생성합니다."""
    # 시설 개수가 많은 순서대로 정렬
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    # 상위 2개 카테고리 추출
    top_categories = [f"**{k}**({v}개)" for k, v in sorted_counts[:2] if v > 0]
    # 시설이 하나도 없는 카테고리 추출 (취약점)
    missing_categories = [k for k, v in sorted_counts if v == 0]

    # 종합 점수에 따른 현실적인 등급 멘트 설정
    if t_score >= 90:
        grade, eval_context = "S", "모든 생활 편의시설이 완벽하게 갖춰진 **최고의 슬세권**입니다."
    elif t_score >= 75:
        grade, eval_context = "A", "대부분의 인프라가 풍부하여 **매우 쾌적한 주거 환경**을 자랑합니다."
    elif t_score >= 60:
        grade, eval_context = "B", "필수적인 편의시설은 갖춰져 있으나, **일부 항목에서 아쉬움**이 있을 수 있습니다."
    elif t_score >= 40:
        grade, eval_context = "C", "기본 요건은 갖췄으나, 특정 인프라 접근성은 다소 떨어집니다."
    else:
        grade, eval_context = "D", "**인프라가 부족한 편**이며 대중교통 의존도가 높을 것으로 보입니다."

    if not top_categories:
        return f"현재 반경 내에 인프라가 거의 없습니다. 분석 반경을 더 넓혀보세요."

    # 리포트 문구 조합
    report = f"이 지역은 종합 편의 지수 **{t_score}점({grade} 등급)**으로 분석되었습니다.<br>"
    report += f" {', '.join(top_categories)} 접근성이 양호하며, {eval_context}"
    
    if missing_categories:
        # 이모지 등을 제외한 깔끔한 이름으로 변환하여 부족 시설 안내
        missing_str = ", ".join([m.split()[-1] if ' ' in m else m[:-1] for m in missing_categories[:3]])
        report += f"<br>⚠️ 특히 **{missing_str}** 관련 시설 보강이 필요해 보입니다."

    return report

@st.cache_data
def load_real_estate_data():
    """서울 부동산 실거래가 통합 데이터를 데이터프레임으로 로드합니다."""
    # 데이터 파일 경로 설정
    file_path = "share/data/seoul_real_estate_combined_2023_2026_geo.csv"
    if not os.path.exists(file_path):
        # 파일이 없을 경우 상대 경로 재시도
        file_path = os.path.join(os.path.dirname(__file__), "..", "data", "seoul_real_estate_combined_2023_2026_geo.csv")
    
    if not os.path.exists(file_path):
        st.error("부동산 데이터 파일을 찾을 수 없습니다.")
        return pd.DataFrame()

    try:
        # 필요한 열만 선택하여 로드
        df = pd.read_csv(file_path, usecols=['RCPT_YR', 'CGG_NM', 'STDG_NM', 'BLDG_NM', 'THING_AMT', 'ARCH_AREA', 'latitude', 'longitude'])
        # 필수 정보가 없는 행은 제거
        df = df.dropna(subset=['latitude', 'longitude', 'THING_AMT', 'BLDG_NM'])
        # 만 원 단위 금액을 '억' 단위로 변환하여 새 열 생성
        df['price_억'] = df['THING_AMT'] / 10000.0
        return df
    except Exception as e:
        st.error(f"데이터 로드 중 오류: {e}")
        return pd.DataFrame()

def filter_data_within_radius(center_lat, center_lon, data, radius_km):
    """위도/경도 기반으로 지정된 반경 내의 부동산 데이터를 필터링합니다."""
    if data.empty: return pd.DataFrame()
    
    # 사각형 범위로 1차 필터링 (계산 속도 향상)
    lat_margin = radius_km / 111.0
    lon_margin = radius_km / (111.0 * 0.8)
    
    mask = (data['latitude'].between(center_lat - lat_margin, center_lat + lat_margin)) & \
           (data['longitude'].between(center_lon - lon_margin, center_lon + lon_margin))
    candidates = data[mask].copy()
    
    if candidates.empty: return pd.DataFrame()
    
    # 각 점과의 정확한 거리(미터) 계산 후 반경 내 데이터만 반환
    candidates['distance'] = candidates.apply(
        lambda row: geodesic((center_lat, center_lon), (row['latitude'], row['longitude'])).meters, axis=1
    )
    return candidates[candidates['distance'] <= (radius_km * 1000)].copy()

def get_ai_real_estate_report(re_data):
    """부동산 거래 데이터를 분석하여 시장 특성 리포트를 생성합니다."""
    if re_data.empty:
        return "현재 반경 내에 최근 실거래 데이터가 충분하지 않습니다."

    avg_price = re_data['price_억'].mean()
    vol = len(re_data)
    max_row = re_data.loc[re_data['price_억'].idxmax()]
    
    # 평균 가격에 따른 시장 성격 분류
    if avg_price >= 15: market_type = "상급지의 **고급 주거 시장**"
    elif avg_price >= 8: market_type = "준수한 주거 선호도를 가진 **중상급 시장**"
    else: market_type = "실수요자 중심의 **가성비 시장**"
        
    report = f"이 지역은 평균 거래가 **{avg_price:.1f}억**으로 형성된 {market_type}입니다.<br>"
    report += f"최근 해당 반경 내 총 **{vol:,}건**의 거래가 확인되었습니다.<br>"
    report += f"최고가 거래 단지는 **{max_row['BLDG_NM']}**({max_row['price_억']:.1f}억)입니다."
    return report

def create_price_map(lat, lon, re_data, radius_km):
    """실거래가 분포를 시각화한 지도를 생성합니다."""
    m = folium.Map(location=[lat, lon], zoom_start=15, tiles="cartodbpositron")
    folium.Circle([lat, lon], radius=radius_km*1000, color='gray', fill=True, fill_opacity=0.05).add_to(m)
    
    # 가격별 색상 지정 함수 (범례와 일치하도록 5단계로 세분화)
    def get_color(p):
        if p >= 20: return 'darkred'    # 20억 이상
        if p >= 15: return 'red'        # 15억 ~ 20억
        if p >= 10: return 'orange'     # 10억 ~ 15억
        if p >= 5: return 'green'       # 5억 ~ 10억
        return 'blue'                    # 5억 미만

    # 최신 거래 순으로 상위 300개 마커 표시
    display_data = re_data.sort_values('RCPT_YR', ascending=False).head(300)
    for _, row in display_data.iterrows():
        color = get_color(row['price_억'])
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=6, color=color, fill=True, fill_opacity=0.7,
            popup=f"<b>{row['BLDG_NM']}</b><br>가격: {row['price_억']:.1f}억<br>면적: {row['ARCH_AREA']:.1f}㎡"
        ).add_to(m)

    # 🎨 가격 범례 추가 (지도 왼쪽 하단에 고정된 HTML 요소 삽입)
    legend_html = f'''
     <div style="position: fixed; 
     bottom: 50px; left: 50px; width: 150px; height: auto; 
     border: 2px solid #e2e8f0; z-index: 9999; font-size: 13px;
     background-color: white; padding: 12px; border-radius: 12px;
     box-shadow: 0 4px 15px rgba(0,0,0,0.1); pointer-events: none;
     font-family: 'Pretendard', sans-serif;">
     <p style="margin-bottom: 10px; font-weight: bold; border-bottom: 1px solid #eee; padding-bottom: 5px; color: #1e293b;">💰 가격 범례</p>
     <div style="display:flex; align-items:center; margin-bottom:6px;"><span style="background:darkred; width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:8px;"></span>20억 이상</div>
     <div style="display:flex; align-items:center; margin-bottom:6px;"><span style="background:red; width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:8px;"></span>15억 ~ 20억</div>
     <div style="display:flex; align-items:center; margin-bottom:6px;"><span style="background:orange; width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:8px;"></span>10억 ~ 15억</div>
     <div style="display:flex; align-items:center; margin-bottom:6px;"><span style="background:green; width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:8px;"></span>5억 ~ 10억</div>
     <div style="display:flex; align-items:center;"><span style="background:blue; width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:8px;"></span>5억 미만</div>
     </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

# ==========================================
# 5. UI Implementation
# ==========================================

def render_home_page():
    # 1. Hero Section
    st.markdown("""
        <div class="hero-section">
            <h1 class="hero-title">SEOUL SEULSEKWON ANALYTICS</h1>
            <p style="font-size: 1.2rem; opacity: 0.8; margin-bottom: 2rem;">
                우리 동네 편의시설, 얼마나 가까울까요? 데이터를 통한 객관적인 슬세권 분석 서비스
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. Search Box Section
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    # Use a form to capture Enter key
    with st.form("google_search_form", clear_on_submit=False):
        c1, c2 = st.columns([4, 1])
        with c1:
            query = st.text_input("📍 분석할 위치 (주소 또는 키워드)", 
                                 placeholder="Search", 
                                 label_visibility="collapsed")
        with c2:
            btn_submit = st.form_submit_button("검색", use_container_width=True)
    
    # Sample Keywords (Horizontal Layout)
    samples = ["성수동 갤러리아포레", "서초 아크로비스타", "센텀 퍼스트 삼성"]
    cols = st.columns([1.2, 1.5, 1.5, 1.5, 0.3]) 
    
    selected_sample = None
    with cols[0]:
        st.markdown('<p style="margin-top: 0.5rem; color: #70757a; font-size: 0.9rem; text-align: right; font-weight: 500;">💡 추천 키워드:</p>', unsafe_allow_html=True)
    with cols[1]:
        if st.button(samples[0], key="sample_1", use_container_width=True):
            selected_sample = samples[0]
    with cols[2]:
        if st.button(samples[1], key="sample_2", use_container_width=True):
            selected_sample = samples[1]
    with cols[3]:
        if st.button(samples[2], key="sample_3", use_container_width=True):
            selected_sample = samples[2]

    # Handle Search Logic
    search_query = selected_sample if selected_sample else (query if btn_submit else None)
    
    if search_query:
        with st.spinner(f"'{search_query}' 분석 준비 중..."):
            res = get_coords_from_address(search_query)
            if res:
                st.session_state.config['coords'] = (res['lat'], res['lng'])
                st.session_state.config['address'] = search_query
                st.session_state.page = 'dashboard'
                st.rerun()
            else:
                st.error("위치를 찾을 수 없습니다. 주소를 다시 상세히 확인해주세요.")
                
    st.markdown('</div>', unsafe_allow_html=True)
    st.write("") # Spacing

    # 3. Service Introduction
    st.markdown("### 💡 서비스 소개")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="dashboard-card" style="height: 100%;">
            <h4>📊 데이터 기반 분석</h4>
            <p style="color: #64748b;">서울시 공공데이터를 활용하여 실제 편의시설 분포를 분석합니다.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="dashboard-card" style="height: 100%;">
            <h4>⚖️ 나만의 가중치</h4>
            <p style="color: #64748b;">카페가 중요한지, 병원이 중요한지 직접 가중치를 설정할 수 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="dashboard-card" style="height: 100%;">
            <h4>🗺️ 직관적인 지도</h4>
            <p style="color: #64748b;">주변 시설을 한눈에 파악할 수 있는 시각화된 지도를 제공합니다.</p>
        </div>
        """, unsafe_allow_html=True)

    # 4. Team Introduction (Expander Toggle)
    st.write("")
    with st.expander("👥 서울 슬세권 분석팀 R&R (Role and Responsibilities)", expanded=True):
        st.write("")
        
        # 6 virtual members
        team_members = [
            {
                "emoji": "🙋‍♂️", "nick": "팀장", "name": "김서울", "role": "Project Leader",
                "tasks": ["슬세권 통합 지수 모델 설계", "전체 프로젝트 기획 및 총괄"]
            },
            {
                "emoji": "👨‍💻", "nick": "기술장인", "name": "이테크", "role": "System Arch",
                "tasks": ["Streamlit 대시보드 시스템 구축", "전체 프레임워크 최적화"]
            },
            {
                "emoji": "📊", "nick": "데이터허브", "name": "박데이터", "role": "Data Engineer",
                "tasks": ["서울시 공공데이터 API 연동", "인프라 데이터 파이프라인 구축"]
            },
            {
                "emoji": "🎨", "nick": "시각화장인", "name": "최비즈", "role": "UI/UX Designer",
                "tasks": ["인터랙티브 차트 및 지도 설계", "Futuristic 디자인 시스템 적용"]
            },
            {
                "emoji": "📍", "nick": "지오마스터", "name": "정지도", "role": "GIS Specialist",
                "tasks": ["Kakao API 기반 지오코딩 구현", "공간 분석 알고리즘 최적화"]
            },
            {
                "emoji": "✅", "nick": "품질요정", "name": "한검증", "role": "QA / Support",
                "tasks": ["데이터 신뢰도 검증 및 정제", "사용자 피드백 및 에러 대응"]
            }
        ]

        cols = st.columns(6)
        for i, member in enumerate(team_members):
            with cols[i]:
                st.markdown(f"""
                <div class="team-card">
                    <div class="team-avatar">{member['emoji']}</div>
                    <div class="member-name">{member['nick']} / {member['name']}</div>
                    <div class="member-role-title">{member['role']}</div>
                    <ul class="member-tasks">
                        {" ".join([f"<li>{task}</li>" for task in member['tasks']])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)

def render_dashboard_page():
    # 2. Main Header (Internal)
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(f'<h2 style="color: {THEME["secondary"]}; margin: 0;">🗺️ 분석 결과: {st.session_state.config["address"]}</h2>', unsafe_allow_html=True)
    with c2:
        if st.button("🏠 홈으로 돌아가기", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()

    # 3. 위치 변경 및 검색 폼 (불필요한 카드 박스 제거)
    with st.container():
        with st.form("search_form"):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                query = st.text_input("📍 위치 변경", value=st.session_state.config['address']) # 주소 입력창
            with c2:
                # 분석 반경 선택 슬라이더
                radius = st.select_slider("📏 반경 (m)", options=[300, 500, 700, 1000, 1500], value=st.session_state.config['radius'])
            with c3:
                st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True) # 줄맞춤을 위한 공백
                btn_submit = st.form_submit_button("다시 분석하기", use_container_width=True) # 전송 버튼
                
        # 버튼 클릭 시 좌표 재검색 및 페이지 갱신
        if btn_submit and query:
            with st.spinner("위치 업데이트 중..."):
                res = get_coords_from_address(query)
                if res:
                    st.session_state.config['coords'] = (res['lat'], res['lng'])
                    st.session_state.config['address'] = query
                    st.session_state.config['radius'] = radius
                    st.rerun() # 앱 재실행
                else:
                    st.error("위치를 찾을 수 없습니다.")

    # 4. Calculation
    t_score, scores, counts, facilities, raw_progress = calculate_seulsekwon_index(
        st.session_state.config['coords'][0], 
        st.session_state.config['coords'][1], 
        st.session_state.data, 
        st.session_state.config['weights'], 
        st.session_state.config['radius']
    )
    viz = create_viz_objects(t_score, scores, counts, facilities, raw_progress)

    # 5. Layout - Sidebar
    with st.sidebar:
        st.title("⚙️ 분석 설정")
        
        with st.expander("⚖️ 가중치 커스터마이징", expanded=True):
            st.caption("인프라 기여도 가중치를 합계 100으로 조정하세요.")
            new_weights = {}
            for cat, w_val in st.session_state.config['weights'].items():
                new_weights[cat] = st.slider(cat, 0, 50, w_val, step=5, key=f"sidebar_{cat}")
            
            cur_sum = sum(new_weights.values())
            if cur_sum == 100:
                st.success(f"합계: {cur_sum}/100")
                if new_weights != st.session_state.config['weights']:
                    st.session_state.config['weights'] = new_weights
                    st.rerun()
            else:
                st.warning(f"합계: {cur_sum}/100 (차이: {100-cur_sum})")
                
            if st.button("🔄 가중치 초기화", use_container_width=True):
                st.session_state.config['weights'] = DEFAULT_WEIGHTS.copy()
                st.rerun()

        st.markdown("---")
        st.subheader("📥 결과 다운로드")
        st.download_button("📊 분석 데이터 CSV", data=pd.DataFrame(facilities).to_csv(index=False).encode('utf-8-sig'), 
                           file_name=f"analysis_{datetime.datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)
        
        st.markdown("---")
        st.caption(f"Engine v2.5 | {datetime.datetime.now().strftime('%Y-%m-%d')}")

    # ✨ 탭 시스템 추가 (검색창 및 설정 아래)
    tab1, tab2 = st.tabs(["🏙️ 슬세권 인프라 분석", "🏠 주변 실거래가 분석"])

    with tab1:
        # 1. AI 실거주 분석 리포트 섹션
        st.markdown(f'### 🤖 AI 실거주 분석 리포트')
        ai_comment = get_ai_analysis_report(t_score, counts, st.session_state.config['weights'])
        st.markdown(f"""
        <div class="dashboard-card" style="border-left: 5px solid {THEME['accent']}; display: flex; align-items: flex-start; gap: 15px;">
            <div style="font-size: 1.5rem; margin-top: 5px;">💡</div>
            <div style="flex: 1;">
                <p style="font-size: 1.1rem; line-height: 1.7; margin: 0; color: {THEME['text_main']};">{ai_comment}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 2. 지도 및 종합 지표 레이아웃
        col_l, col_r = st.columns([2, 1])
        
        with col_l:
            # 인프라 분포도 제목 및 지도 (카드 박스 형태)
            st.markdown(f'<div class="dashboard-card"><h3>🗺️ 인프라 분포도: {st.session_state.config["address"]}</h3>', unsafe_allow_html=True)
            
            # 🎨 지도 필터 UI (보고 싶은 시설군만 선택)
            selected_groups = st.multiselect("표시할 시설 선택", options=list(CATEGORY_GROUPS.keys()), default=list(CATEGORY_GROUPS.keys()), key="map_view_filter")
            filtered_facilities = [f for f in facilities if f['group'] in selected_groups]

            # 필터링된 시설로 지도 생성 및 출력
            folium_map = create_folium_map(st.session_state.config['coords'][0], st.session_state.config['coords'][1], filtered_facilities, st.session_state.config['radius'])
            map_interaction = st_folium(folium_map, width="100%", height=500, key="main_map")
            
            # 지도 위를 클릭했을 때 해당 위치로 분석 재실행하는 인터랙션 로직
            if map_interaction and map_interaction.get("last_clicked"):
                nc = (map_interaction["last_clicked"]["lat"], map_interaction["last_clicked"]["lng"])
                if round(nc[0], 5) != round(st.session_state.config['coords'][0], 5):
                    with st.spinner("해당 위치의 주소 분석 중..."):
                        address = get_address_from_coords(nc[0], nc[1])
                        st.session_state.config['coords'] = nc
                        st.session_state.config['address'] = address
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with col_r:
            # 종합 점수에 따른 등급 산정
            grade_char = "s" if t_score >= 90 else ("a" if t_score >= 75 else ("b" if t_score >= 60 else ("c" if t_score >= 40 else "d")))
            
            # 3. 이미지 기반 커스텀 종합 점수 카드 구현
            # HTML 문자열 내부의 들여쓰기를 제거하여 텍스트로 노출되는 오류를 방지합니다.
            st.markdown(f"""
<div class="dashboard-card" style="padding: 30px; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 400px; text-align: center;">
    <h3 style="margin-bottom: 25px; color: #1e293b; font-size: 1.6rem; font-weight: 800;">💡 종합 편의 기여도</h3>
    <div style="font-size: 4.5rem; font-weight: 900; color: #5b86e5; margin-bottom: 20px; font-family: 'Pretendard', sans-serif;">
        {t_score:.1f}
    </div>
    <div style="background-color: #f69d12; color: white; padding: 12px 0; width: 100%; border-radius: 40px; font-size: 1.3rem; font-weight: 800; margin-bottom: 35px; box-shadow: 0 4px 10px rgba(246, 157, 18, 0.2);">
        {grade_char.upper()} GRADE
    </div>
    <div style="width: 100%; margin-bottom: 10px;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 700; color: #64748b; margin-bottom: 8px;">
            <span>0</span><span>100</span>
        </div>
        <div style="background-color: #e2e8f0; height: 16px; border-radius: 20px; width: 100%; position: relative; overflow: hidden;">
            <div style="background: linear-gradient(90deg, #5b86e5, #3628e2); width: {t_score}%; height: 100%; border-radius: 20px;"></div>
        </div>
    </div>
    <p style="color: #64748b; margin-top: 20px; font-size: 0.95rem; font-weight: 500;">주변 인프라 밀도 분석 결과입니다.</p>
</div>
""", unsafe_allow_html=True)

        # 3. 상세 분석 차트 영역
        st.markdown("### 📈 상세 데이터 분석")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown('<div class="dashboard-card"><h4>📊 카테고리 밸런스</h4>', unsafe_allow_html=True)
            st.plotly_chart(viz['radar'], use_container_width=True) # 레이더 차트
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="dashboard-card"><h4>⚖️ 인프라 구성 비교</h4>', unsafe_allow_html=True)
            st.plotly_chart(viz['compare'], use_container_width=True) # 비교 막대 차트
            st.markdown('</div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="dashboard-card"><h4>📋 주요 시설 통계</h4>', unsafe_allow_html=True)
            stats_df = pd.DataFrame(counts.items(), columns=['분류', '개수']).sort_values('개수', ascending=False)
            st.dataframe(stats_df, hide_index=True, use_container_width=True) # 통계 표
            st.markdown('</div>', unsafe_allow_html=True)

            # --- Tab 1 전용: 인프라 상세 리스트 복구 ---
            # 하단에 공통으로 노출되던 리스트를 인프라 탭 전용으로 이동시켰습니다.
            with st.expander("📍 현재 지역 인프라 상세 리스트", expanded=False):
                if facilities:
                    infra_df = pd.DataFrame(facilities)[['group', 'name', 'distance', 'emoji']]
                    infra_df.columns = ['카테고리', '시설명', '거리(m)', '아이콘']
                    st.dataframe(infra_df, use_container_width=True)
                else:
                    st.info("표시할 시설 데이터가 없습니다.")

    with tab2:
        # 9. 실거래가 분석 섹션 (반경 3km)
        # 이미지 기반의 고도화된 레이아웃을 적용합니다.
        st.markdown("### 🏠 반경 3km 내 실거래가 분포 분석")
        
        # 세션 상태에 부동산 데이터가 없을 경우를 대비한 방어 코드
        if 're_data' not in st.session_state or st.session_state.re_data.empty:
            with st.spinner("부동산 데이터를 불러오고 있습니다..."):
                st.session_state.re_data = load_real_estate_data()

        with st.spinner("주변 실거래 데이터 분석 중..."):
            recent_re = filter_data_within_radius(
                st.session_state.config['coords'][0], 
                st.session_state.config['coords'][1], 
                st.session_state.re_data, 
                3.0 # 3km radius
            )
            
        if not recent_re.empty:
            # 🤖 AI 실거래 시장 분석 리포트
            st.markdown(f'### 🤖 AI 실거래 시장 분석')
            re_ai_report = get_ai_real_estate_report(recent_re)
            st.markdown(f"""
            <div class="dashboard-card" style="border-left: 5px solid {THEME['primary']}; display: flex; align-items: flex-start; gap: 15px;">
                <div style="font-size: 1.5rem; margin-top: 5px;">📊</div>
                <div style="flex: 1;">
                    <p style="font-size: 1.1rem; line-height: 1.7; margin: 0; color: {THEME['text_main']};">{re_ai_report}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 분석 차트 및 통계 요약 2단 구성
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # 면적 대비 가격 산포도 제목
                st.markdown(f'''
                <div class="dashboard-card" style="padding: 10px 24px; display: flex; align-items: center; min-height: 50px; margin-bottom: 0.8rem;">
                    <h4 style="margin: 0; line-height: 1.2;">💰 면적 대비 가격 분포 (산포도)</h4>
                </div>
                ''', unsafe_allow_html=True)

                # Plotly 산포도 차트 출력 (불필요한 카드 프레임 제거)
                fig_scatter = px.scatter(recent_re, x="ARCH_AREA", y="price_억",
                                       color="price_억", color_continuous_scale="Viridis",
                                       hover_data=["BLDG_NM", "RCPT_YR"],
                                       labels={'ARCH_AREA': '전용면적 (㎡)', 'price_억': '거래가 (억 원)'})
                fig_scatter.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif", color=THEME['secondary']),
                    margin=dict(t=10, b=10, l=10, r=10), height=350,
                    showlegend=False
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

            with col2:
                # 3km 반경 시장 요약 제목
                st.markdown(f'''
                <div class="dashboard-card" style="padding: 10px 24px; display: flex; align-items: center; min-height: 50px; margin-bottom: 0.8rem;">
                    <h4 style="margin: 0; line-height: 1.2;">📋 3km 반경 시장 요약</h4>
                </div>
                ''', unsafe_allow_html=True)

                # 통계 수치 계산
                avg_price = recent_re['price_억'].mean()
                median_price = recent_re['price_억'].median()
                
                # 최고가 거래 정보 추출
                max_row = recent_re.loc[recent_re['price_억'].idxmax()]
                max_price = max_row['price_억']
                max_bldg = max_row['BLDG_NM']
                max_area = max_row['ARCH_AREA']
                
                # 시장 요약 지표 카드
                st.markdown(f"""
                <div class="dashboard-card" style="height: 388px; display: flex; flex-direction: column; justify-content: center;">
                    <div style="display: flex; flex-direction: column; gap: 20px;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #64748b;">평균 거래가</span>
                            <span style="font-weight: 700; color: {THEME['primary']};">{avg_price:.1f}억</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #64748b;">중간 거래가</span>
                            <span style="font-weight: 700;">{median_price:.1f}억</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <span style="color: #64748b;">최고 거래가</span>
                            <div style="text-align: right;">
                                <div style="font-weight: 700; color: #ef4444;">{max_price:.1f}억</div>
                                <div style="font-size: 0.8rem; color: #64748b;">{max_bldg} ({max_area:.1f}㎡)</div>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #64748b;">분석 거래 건수</span>
                            <span style="font-weight: 700;">{len(recent_re):,}건</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            # 실거래 위치 분포 지도 섹션
            st.markdown(f'''
            <div class="dashboard-card" style="padding: 10px 24px; display: flex; align-items: center; min-height: 50px; margin-bottom: 0.8rem;">
                <h4 style="margin: 0; line-height: 1.2;">📍 실거래 위치 분포 (최근 500건)</h4>
            </div>
            ''', unsafe_allow_html=True)
            # 부동산 가격 지도 생성 (불필요한 카드 프레임 제거)
            p_map = create_price_map(st.session_state.config['coords'][0], st.session_state.config['coords'][1], recent_re, 3.0)
            st_folium(p_map, width="100%", height=500, key="re_price_map")

            # 10. 실거래 상세 데이터 리스트 (Tab 2 전용 Expander)
            # 지도에 표시된 마커(최근 실거래 내역)들의 정보를 데이터프레임으로 제공합니다.
            with st.expander("📋 지도에 표시된 최근 실거래 상세 리스트", expanded=False):
                # 표시용 컬럼 정리 및 정렬 (최근 거래순)
                display_re_list = recent_re.sort_values('RCPT_YR', ascending=False).head(300).copy()
                display_re_list = display_re_list[['RCPT_YR', 'BLDG_NM', 'price_억', 'ARCH_AREA', 'CGG_NM', 'STDG_NM']]
                display_re_list.columns = ['거래연도', '건물명', '거래가(억)', '전용면적(㎡)', '자치구', '법정동']
                
                # 데이터프레임 출력
                st.dataframe(display_re_list, use_container_width=True, hide_index=True)
                st.caption("※ 정보 광장 데이터를 바탕으로 최근 3km 내 주요 거래 내역 300건을 표시합니다.")
        else:
            # 데이터가 없을 경우 경고 메시지
            st.warning("반경 3km 내에 필터링된 실거래 데이터가 없습니다.")


def main():
    inject_custom_css()
    
    # 1. 앱 실행을 위한 데이터 초기화 및 로드
    # 인프라 데이터 및 부동산 데이터가 세션 상태에 없을 경우 로드합니다.
    if 'data' not in st.session_state or 're_data' not in st.session_state:
        with st.status("🚀 분석 엔진 및 부동산 데이터 준비 중...", expanded=True) as status:
            # 인프라 데이터 로드 (서울 생활권 기반)
            if 'data' not in st.session_state:
                st.session_state.data = load_infrastructure_data()
            
            # 실거래가 부동산 데이터 로드 (서울 아파트/건물 기반)
            if 're_data' not in st.session_state:
                st.session_state.re_data = load_real_estate_data()
            
            # 로드 성공 여부 확인 및 알림 업데이트
            if not st.session_state.data.empty:
                status.update(label=f"준비 완료 (인프라 {len(st.session_state.data):,}건 로드)", state="complete")
            else:
                st.error("기본 데이터 로드에 실패했습니다. 파일을 확인해주세요.")
                st.stop()
    
    if 'page' not in st.session_state:
        st.session_state.page = 'home'

    if 'config' not in st.session_state:
        st.session_state.config = {
            'coords': (37.5665, 126.9780),
            'address': "서울시청",
            'radius': 500,
            'weights': DEFAULT_WEIGHTS.copy()
        }

    # Page Routing
    if st.session_state.page == 'home':
        render_home_page()
    else:
        render_dashboard_page()

    # 8. Shared Footer Section
    st.markdown("""
        <div class="custom-footer">
            <div class="footer-content">
                <p>💡 <b>본 서비스는 fcicb6 데이터분석 코스 프로젝트의 일환으로 제작되었습니다.</b></p>
                <div class="footer-links">
                    <span>📊 <b>참고 데이터:</b> 서울시 공공데이터포털, 카카오 API, 소상공인시장진흥공단</span>
                    <span>✉️ <b>문의 contact:</b> <a href="mailto:samplenotreal@gmail.com" style="color: #3b82f6; text-decoration: none;">samplenotreal@gmail.com</a></span>
                </div>
                <p style="margin-top: 1.5rem; font-size: 0.8rem; opacity: 0.6;">© 2026 SEOUL SEULSEKWON ANALYTICS. All rights reserved.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 9. Shared Floating Report Button
    st.markdown("""
        <a href="https://forms.gle/UAQXVBgi9owJ7JgF8" target="_blank" class="report-btn" style="text-decoration: none;">
            🚨 오류 제보하기
        </a>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    import time
    main()
