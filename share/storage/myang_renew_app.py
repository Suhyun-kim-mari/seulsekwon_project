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

# 현재 파일 위치: .../seulsekwon_project/share/storage/renew_app.py
current_dir = os.path.dirname(os.path.abspath(__file__))

# 예상되는 .env 위치 후보들
# 1. seulsekwon_project/.env (현재 파일 기준 상위 3단계)
# 2. pj/.env (현재 파일 기준 상위 4단계 - 프로젝트 루트)
possible_paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), '.env'), # seulsekwon_project/.env
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), '.env') # pj/.env
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
                    "address_name": info.get('place_name', info.get('address_name', query)),
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
                # 주소 검색 결과에서 좌표 추출
                return {
                    "address_name": info['address_name'],
                    "lat": float(info['y']),
                    "lng": float(info['x'])
                }
    except Exception as e:
        st.error(f"좌표 변환 중 예외 발생: {e}")

    return None

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
