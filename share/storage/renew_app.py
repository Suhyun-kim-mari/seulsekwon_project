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
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)

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
        return 0.0, {{}}, {{}}, [], {{}}

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
    
    # Gauge Chart
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=total_score,
        gauge={
            'axis': {'range': [0, 100]}, 
            'bar': {'color': THEME['primary']},
            'steps': [
                {'range': [0, 60], 'color': "#f1f5f9"},
                {'range': [60, 85], 'color': "#e2e8f0"},
                {'range': [85, 100], 'color': "#dee2e6"}
            ]
        }
    ))
    fig_gauge.update_layout(height=300, margin=dict(t=30, b=20), **layout_base)
    
    # Infrastructure Balance (Comparison)
    # 서울 도심 평균 데이터 (가상)
    SEOUL_AVG = {"생활/편의🏪": 20, "교통🚌": 15, "의료💊": 12, "안전/치안🚨": 8, "교육/문화📚": 5, "자연/여가🌳": 12, "금융🏦": 5}
    s_total = sum(SEOUL_AVG.values())
    s_perc = {k: (v/s_total)*100 for k, v in SEOUL_AVG.items()}
    
    d_total = sum(scores.values()) or 1
    d_perc = {k: (v/d_total)*100 for k, v in scores.items()}
    
    fig_compare = go.Figure()
    for cat in scores.keys():
        fig_compare.add_trace(go.Bar(
            name=cat, x=["현재 지점", "서울 평균"], 
            y=[d_perc[cat], s_perc[cat]],
            hovertemplate="%{x}<br>%{y:.1f}%"
        ))
    fig_compare.update_layout(
        barmode='stack', height=400, showlegend=True,
        legend=dict(orientation="h", y=-0.2), **layout_base
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
                st.session_state.config['address'] = res['address_name']
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

    # 3. Search Form (Sidebar or Internal)
    with st.container():
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        with st.form("search_form"):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                query = st.text_input("📍 위치 변경", value=st.session_state.config['address'])
            with c2:
                radius = st.select_slider("📏 반경 (m)", options=[300, 500, 700, 1000, 1500], value=st.session_state.config['radius'])
            with c3:
                st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
                btn_submit = st.form_submit_button("다시 분석하기", use_container_width=True)
                
        if btn_submit and query:
            with st.spinner("위치 업데이트 중..."):
                res = get_coords_from_address(query)
                if res:
                    st.session_state.config['coords'] = (res['lat'], res['lng'])
                    st.session_state.config['address'] = res['address_name']
                    st.session_state.config['radius'] = radius
                    st.rerun()
                else:
                    st.error("위치를 찾을 수 없습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

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

    # 6. Layout - Dash Performance
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.markdown(f'<div class="dashboard-card"><h3>🗺️ 인프라 분포도</h3>', unsafe_allow_html=True)
        folium_map = create_folium_map(st.session_state.config['coords'][0], st.session_state.config['coords'][1], facilities, st.session_state.config['radius'])
        map_interaction = st_folium(folium_map, width="100%", height=500, key="main_map")
        
        if map_interaction and map_interaction.get("last_clicked"):
            nc = (map_interaction["last_clicked"]["lat"], map_interaction["last_clicked"]["lng"])
            if round(nc[0], 5) != round(st.session_state.config['coords'][0], 5):
                st.session_state.config['coords'] = nc
                st.session_state.config['address'] = f"지정 포인트 ({nc[0]:.4f}, {nc[1]:.4f})"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.subheader("💡 종합 편의 기여도")
        grade = "s" if t_score >= 90 else ("a" if t_score >= 80 else ("b" if t_score >= 70 else "c"))
        st.markdown(f'<div class="metric-value">{t_score}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="grade-badge grade-{grade}">{grade.upper()} GRADE</div>', unsafe_allow_html=True)
        st.plotly_chart(viz['gauge'], use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 7. Layout - Detailed Charts
    st.markdown("### 📈 상세 데이터 분석")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown('<div class="dashboard-card"><h4>📊 카테고리 밸런스</h4>', unsafe_allow_html=True)
        st.plotly_chart(viz['radar'], use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="dashboard-card"><h4>⚖️ 인프라 구성 비교</h4>', unsafe_allow_html=True)
        st.plotly_chart(viz['compare'], use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="dashboard-card"><h4>📋 주요 시설 통계</h4>', unsafe_allow_html=True)
        stats_df = pd.DataFrame(counts.items(), columns=['분류', '개수']).sort_values('개수', ascending=False)
        st.dataframe(stats_df, hide_index=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("📍 전체 시설 리스트 보기", expanded=False):
        if facilities:
            st.dataframe(pd.DataFrame(facilities)[['group', 'name', 'distance', 'emoji']], use_container_width=True)
        else:
            st.info("데이터가 없습니다.")

def main():
    inject_custom_css()
    
    # 1. State Initialization
    if 'data' not in st.session_state:
        with st.status("🚀 분석 엔진 준비 중...", expanded=True) as status:
            st.session_state.data = load_infrastructure_data()
            if not st.session_state.data.empty:
                status.update(label=f"준비 완료 ({len(st.session_state.data):,}건 로드)", state="complete")
            else:
                st.error("데이터 로드 실패")
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
