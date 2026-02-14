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

# .env 파일 명시적 로드 (현재 스크립트 위치 기준 2단계 상위 폴더)
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "../../.env")
load_dotenv(dotenv_path=env_path)

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
            color: {THEME['text_main']} !important;
        }}
        
        h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown {{
            color: {THEME['text_main']} !important;
        }}
        
        .dashboard-card, div[data-testid="stForm"] {{
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
            color: white !important;
            text-align: center;
            width: 100%;
        }}
        
        .grade-s {{ background-color: #f59e0b; }}
        .grade-a {{ background-color: #10b981; }}
        .grade-b {{ background-color: #3b82f6; }}
        .grade-c {{ background-color: #64748b; }}
        .grade-d {{ background-color: #ef4444; }}
        
        section[data-testid="stSidebar"] {{
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0;
        }}
        
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
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
    """주소 또는 장소명(ex. 강남경찰서)으로 좌표를 검색합니다. (키워드 -> 주소 순차 검색)"""
    api_key = get_kakao_api_key()
    if not api_key:
        st.error("카카오 API 키가 설정되지 않았습니다.")
        return None
        
    headers = {"Authorization": f"KakaoAK {api_key}"}

    # 1. 키워드 검색 시도
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
        else:
            if res_kw.status_code == 401 and "ip mismatched" in res_kw.text:
                st.error("❌ IP 인증 오류: 현재 IP(122.43.50.6)가 카카오 개발자 센터에 등록되지 않았거나 아직 적용되지 않았습니다. 잠시 후 다시 시도해 보세요.")
            else:
                st.error(f"키워드 검색 API 오류: {res_kw.status_code} - {res_kw.text}")
    except Exception as e:
        st.error(f"키워드 검색 중 예외 발생: {e}")

    # 2. 주소 검색 시도 (키워드 검색 실패 시)
    url_addr = "https://dapi.kakao.com/v2/local/search/address.json"
    try:
        res_addr = requests.get(url_addr, headers=headers, params={"query": query, "size": 1}, timeout=5)
        if res_addr.status_code == 200:
            data = res_addr.json()
            if data['documents']:
                info = data['documents'][0]
                return {
                    "address_name": info['address_name'],
                    "lat": float(info['y']),
                    "lng": float(info['x'])
                }
    except Exception as e:
        st.error(f"주소 검색 중 오류 발생: {e}")

    return None

@st.cache_data
def load_infrastructure_data():
    file_path = "share/data/seoul_combined_data_final_v3.csv"
    if not os.path.exists(file_path):
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, "..", "data", "seoul_combined_data_final_v3.csv")
        if not os.path.exists(file_path):
            st.error(f"데이터 파일을 찾을 수 없습니다: {file_path}")
            return pd.DataFrame()

    try:
        df = pd.read_csv(file_path)
        df_slim = pd.DataFrame()
        df_slim['name'] = df['name']
        df_slim['lat'] = df['latitude']
        df_slim['lon'] = df['longitude']
        df_slim['sub_category'] = df['category_small']
        df_slim = df_slim.dropna(subset=['lat', 'lon'])
        return df_slim
    except Exception as e:
        st.error(f"데이터 파일을 읽는 중 오류 발생: {e}")
        return pd.DataFrame()

@st.cache_data
def load_real_estate_data():
    """서울실거래가 데이터를 로드합니다."""
    file_path = "share/data/seoul_real_estate_combined_2023_2026_geo.csv"
    if not os.path.exists(file_path):
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, "..", "data", "seoul_real_estate_combined_2023_2026_geo.csv")
        if not os.path.exists(file_path):
            st.error(f"실거래가 데이터 파일을 찾을 수 없습니다: {file_path}")
            return pd.DataFrame()

    try:
        # RCPT_YR,THING_AMT,BLDG_NM,BLDG_USG,latitude,longitude 등 필요 컬럼만 로드
        df = pd.read_csv(file_path, usecols=['RCPT_YR', 'CGG_NM', 'STDG_NM', 'BLDG_NM', 'THING_AMT', 'ARCH_AREA', 'BLDG_USG', 'latitude', 'longitude'])
        # 건물명(BLDG_NM)이 없거나 위도/경도/금액 정보가 없는 행 삭제
        df = df.dropna(subset=['latitude', 'longitude', 'THING_AMT', 'BLDG_NM'])
        # 빈 문자열도 처리
        df = df[df['BLDG_NM'].astype(str).str.strip() != ""]
        # THING_AMT는 만 원 단위이므로 억 단위로 변환 (표시용)
        df['price_억'] = df['THING_AMT'] / 10000.0
        # 평당 가격 계산 (ARCH_AREA: 전용면적 m2)
        df['price_per_m2'] = df['THING_AMT'] / df['ARCH_AREA']
        df['price_per_pyung'] = df['price_per_m2'] * 3.30578
        return df
    except Exception as e:
        st.error(f"실거래가 데이터를 읽는 중 오류 발생: {e}")
        return pd.DataFrame()

def filter_data_within_radius(center_lat, center_lon, data, radius_km):
    """지정한 반경 내의 데이터를 필터링합니다."""
    if data.empty:
        return pd.DataFrame()
    
    # 1차 사각 필터링 (속도 최적화)
    lat_margin = radius_km / 111.0
    lon_margin = radius_km / (111.0 * 0.8) # 대략적인 서울 위도 기준
    
    mask = (data['latitude'].between(center_lat - lat_margin, center_lat + lat_margin)) & \
           (data['longitude'].between(center_lon - lon_margin, center_lon + lon_margin))
    candidates = data[mask].copy()
    
    if candidates.empty:
        return pd.DataFrame()
        
    # 2차 정밀 거리 필터링
    candidates['distance'] = candidates.apply(
        lambda row: geodesic((center_lat, center_lon), (row['latitude'], row['longitude'])).meters, axis=1
    )
    return candidates[candidates['distance'] <= (radius_km * 1000)].copy()

def calculate_seulsekwon_index(center_lat, center_lon, data, weights, radius_m):
    if data.empty:
        return 0.0, {}, {}, [], {}

    radius_km = radius_m / 1000.0
    MAX_CAPS = {
        "생활/편의🏪": 15, "교통🚌": 8, "의료💊": 5, 
        "안전/치안🚨": 1, "교육/문화📚": 2, "자연/여가🌳": 2, "금융🏦": 3
    }
    
    lat_margin, lon_margin = radius_km / 111.0, radius_km / 88.0
    mask = (data['lat'].between(center_lat - lat_margin, center_lat + lat_margin)) & \
           (data['lon'].between(center_lon - lon_margin, center_lon + lon_margin))
    candidates = data[mask].copy()

    scores, counts, nearby, raw_progress = {}, {}, [], {}
    
    for g_name, sub_cats in CATEGORY_GROUPS.items():
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
        
        group_facilities = sorted(group_facilities, key=lambda x: x['distance'])
        unique_group_facilities = []
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
# 4. Analysis & Visualizations
# ==========================================

def get_ai_analysis_report(t_score, counts, weights):
    """데이터를 기반으로 현실적이고 직관적인 지역 특성 요약 (Fact-based + Critical Analysis)"""
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_categories = [f"**{k}**({v}개)" for k, v in sorted_counts[:2] if v > 0]
    
    # 0개인 항목 찾기 (취약점) - 이모지 제거 트릭 필요
    missing_categories = [k for k, v in sorted_counts if v == 0]

    # 현실적인 등급 산정 (S, A, B, C, D)
    if t_score >= 90:
        grade = "S"
        eval_context = "모든 생활 편의시설이 완벽하게 갖춰진 **최고의 슬세권**입니다. 도보 생활에 전혀 불편함이 없습니다."
    elif t_score >= 75:
        grade = "A"
        eval_context = "대부분의 인프라가 풍부하여 **매우 쾌적한 주거 환경**을 자랑합니다."
    elif t_score >= 60:
        grade = "B"
        eval_context = "필수적인 편의시설은 갖춰져 있으나, **일부 항목에서 아쉬움**이 있을 수 있습니다."
    elif t_score >= 40:
        grade = "C"
        eval_context = "주거지로서 기본 요건은 갖췄으나, **편의점 외 다양한 인프라 접근성은 다소 떨어집니다.**"
    else:
        grade = "D"
        eval_context = "**인프라가 부족한 편**입니다. 도보보다는 **차량이나 대중교통 의존도가 높은 지역**으로 보입니다."

    if not top_categories:
        return f"종합 점수 **{t_score}점(D 등급)**. 현재 반경 내에 분석 가능한 주요 인프라가 거의 없습니다. 분석 반경을 1km 이상으로 넓혀보시는 것을 추천합니다."

    # 멘트 조합
    report = f"이 지역은 종합 편의 지수 **{t_score}점({grade} 등급)**으로 분석되었습니다.<br>"
    
    report += f" {', '.join(top_categories)} 접근성이 상대적으로 양호하지만, "
    report += f"{eval_context}"
    
    if missing_categories:
        # 이모지 제거 등 깔끔하게 포맷팅
        missing_str = ", ".join([m.split()[-1] if ' ' in m else m[:-1] for m in missing_categories[:3]])
        report += f"<br>⚠️ 특히 **{missing_str}** 관련 시설이 반경 내에 부족하므로 이 점을 유의해야 합니다."

    return report

def get_ai_real_estate_report(re_data):
    """실거래가 데이터를 분석하여 AI 리포트를 생성합니다."""
    if re_data.empty:
        return "현재 반경 3km 내에 최근 실거래 데이터가 충분하지 않아 분석이 어렵습니다."

    avg_price = re_data['price_억'].mean()
    median_price = re_data['price_억'].median()
    max_row = re_data.loc[re_data['price_억'].idxmax()]
    vol = len(re_data)
    
    # 가격대별 비율 계산
    high_tier = len(re_data[re_data['price_억'] >= 20])
    mid_tier = len(re_data[(re_data['price_억'] >= 10) & (re_data['price_억'] < 20)])
    
    # 시장 성격 진단
    if avg_price >= 20:
        market_type = "초고가 주거 단지 중심의 **하이엔드 시장**"
    elif avg_price >= 12:
        market_type = "서울 상위권 시세를 형성하고 있는 **고급 주거지**"
    elif avg_price >= 8:
        market_type = "안정적인 실거주 수요가 뒷받침되는 **중상급 시장**"
    else:
        market_type = "진입 장벽이 상대적으로 낮은 **보급형/가성비 위주 시장**"
        
    report = f"이 지역은 평균 거래가 **{avg_price:.1f}억**으로 구성된 {market_type}입니다.<br>"
    report += f"최근 3km 반경 내에서 총 **{vol:,}건**의 거래가 발생했으며, "
    
    if high_tier > 20:
        report += "**20억 이상의 초고가 거래**가 빈번하게 발생하는 상급지 특성을 보입니다. "
    elif mid_tier > (vol * 0.3):
        report += "**10억~20억 사이의 중고가 거래**가 활발하여 시장 활력이 높은 편입니다. "
    else:
        report += "대부분 중저가 위주의 거래가 주를 이루며 **실수요 중심**으로 시장이 형성되어 있습니다. "
        
    report += f"<br>최고가 매물은 **{max_row['BLDG_NM']}**({max_row['price_억']:.1f}억)으로, 해당 지역의 **랜드마크 단지** 역할을 하고 있습니다."
    
    return report

def create_viz_objects(total_score, scores, counts, facilities, raw_progress):
    layout_base = dict(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(family="Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif", color=THEME['secondary'])
    )
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[v * 100 for v in raw_progress.values()] + [list(raw_progress.values())[0] * 100],
        theta=list(raw_progress.keys()) + [list(raw_progress.keys())[0]],
        fill='toself',
        fillcolor='rgba(99, 102, 241, 0.2)',
        line=dict(color=THEME['accent'], width=2),
        name='카테고리 달성도'
    ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, **layout_base)
    
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
    fig_compare.update_layout(barmode='stack', height=400, showlegend=True, legend=dict(orientation="h", y=-0.2), **layout_base)
    
    return {'radar': fig_radar, 'gauge': fig_gauge, 'compare': fig_compare}

def create_folium_map(lat, lon, facilities, radius_m):
    m = folium.Map(location=[lat, lon], zoom_start=16, tiles="cartodbpositron")
    folium.Circle([lat, lon], radius=radius_m, color=THEME['primary'], fill=True, fill_opacity=0.05).add_to(m)
    folium.Marker([lat, lon], icon=folium.Icon(color='red', icon='home', prefix='fa'), tooltip="내 중심지").add_to(m)
    
    for f in facilities[:300]:
        html = f"""
        <div style="font-size: 14px; background: white; border-radius: 50%; width: 24px; height: 24px; 
        display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        border: 2px solid {THEME['accent']};">
            {f['emoji']}
        </div>
        """
        popup_html = f"""
        <div style="font-family: 'Pretendard', sans-serif; font-size: 13px;">
            <b style="color: {THEME['primary']};">{f['name']}</b><br>
            거리: {f['distance']:.0f}m
        </div>
        """
        folium.Marker(
            [f['lat'], f['lon']],
            icon=folium.DivIcon(html=html),
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"{f['emoji']} {f['name']}"
        ).add_to(m)
    return m

def create_price_map(lat, lon, re_data, radius_km):
    """실거래가 분포를 보여주는 지도를 생성합니다."""
    m = folium.Map(location=[lat, lon], zoom_start=14, tiles="cartodbpositron")
    folium.Circle([lat, lon], radius=radius_km*1000, color='gray', fill=True, fill_opacity=0.05).add_to(m)
    
    # 가격대에 따른 색상 맵핑
    def get_color(amt_ok):
        if amt_ok >= 20: return 'darkred'    # 20억 이상
        if amt_ok >= 15: return 'red'        # 15억 이상
        if amt_ok >= 10: return 'orange'     # 10억 이상
        if amt_ok >= 5: return 'green'       # 5억 이상
        return 'blue'                        # 5억 미만

    # 상위 500개만 표시 (성능)
    display_data = re_data.sort_values('RCPT_YR', ascending=False).head(500)
    
    for _, row in display_data.iterrows():
        color = get_color(row['price_억'])
        popup_html = f"""
        <div style="font-family: 'Pretendard', sans-serif; font-size: 13px;">
            <b style="color: {color};">{row['BLDG_NM']}</b><br>
            가격: <b>{row['price_억']:.1f}억</b><br>
            면적: {row['ARCH_AREA']:.1f}㎡<br>
            연도: {row['RCPT_YR']}
        </div>
        """
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{row['BLDG_NM']} ({row['price_억']:.1f}억)"
        ).add_to(m)
    
    # 🎨 범례 추가
    legend_html = f'''
     <div style="position: fixed; 
     bottom: 30px; left: 30px; width: 140px; height: auto; 
     border: 2px solid #e2e8f0; z-index: 9999; font-size: 13px;
     background-color: white; padding: 10px; border-radius: 10px;
     box-shadow: 0 4px 15px rgba(0,0,0,0.1); pointer-events: none;
     font-family: 'Pretendard', sans-serif;">
     <p style="margin-bottom: 8px; font-weight: bold; border-bottom: 1px solid #eee; padding-bottom: 5px;">💰 가격 범례</p>
     <div style="display:flex; align-items:center; margin-bottom:4px;"><span style="background:darkred; width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:8px;"></span>20억↑</div>
     <div style="display:flex; align-items:center; margin-bottom:4px;"><span style="background:red; width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:8px;"></span>15억 ~ 20억</div>
     <div style="display:flex; align-items:center; margin-bottom:4px;"><span style="background:orange; width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:8px;"></span>10억 ~ 15억</div>
     <div style="display:flex; align-items:center; margin-bottom:4px;"><span style="background:green; width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:8px;"></span>5억 ~ 10억</div>
     <div style="display:flex; align-items:center;"><span style="background:blue; width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:8px;"></span>5억 미만</div>
     </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

# ==========================================
# 5. UI Implementation
# ==========================================

def main():
    inject_custom_css()
    
    if 'data' not in st.session_state:
        with st.status("🚀 분석 엔진 준비 중...", expanded=True) as status:
            st.session_state.data = load_infrastructure_data()
            if not st.session_state.data.empty:
                status.update(label=f"준비 완료 ({len(st.session_state.data):,}건 로드)", state="complete")
            else:
                st.error("데이터 로드 실패")
                st.stop()
    
    if 'config' not in st.session_state:
        st.session_state.config = {
            'coords': (37.5665, 126.9780),
            'address': "서울시청",
            'radius': 500,
            'weights': DEFAULT_WEIGHTS.copy()
        }

    if 're_data' not in st.session_state:
        with st.spinner("🏥 실거래가 통계 정보 로드 중..."):
            st.session_state.re_data = load_real_estate_data()

    # 3. Search Form (강력하게 개선된 버전)
    with st.container():
        # [Box 1] 제목 박스
        st.markdown(f'''
        <div class="dashboard-card" style="text-align: center; margin-bottom: 2rem;">
            <h1 style="color: {THEME["secondary"]}; margin: 0;">🏙️ SEOUL SEULSEKWON ANALYTICS</h1>
        </div>
        ''', unsafe_allow_html=True)
        
        # [Box 2] 검색 폼 박스 (CSS로 stForm 자체에 카드 스타일 적용됨)
        with st.form("search_form"):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                query = st.text_input("📍 위치 검색 (장소명 혹은 주소)", 
                                    value=st.session_state.config['address'],
                                    placeholder="예: 강남경찰서, 성수동 아크로포레스트 등")
            with c2:
                # 반경 최대 1000m로 수정
                radius = st.select_slider("📏 반경 (m)", options=[300, 500, 700, 1000], value=st.session_state.config['radius'])
            with c3:
                st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
                btn_submit = st.form_submit_button("분석 시작하기", use_container_width=True)
                
        if btn_submit and query:
            with st.spinner(f"'{query}' 위치 찾는 중..."):
                res = get_coords_from_address(query)
                if res:
                    st.session_state.config['coords'] = (res['lat'], res['lng'])
                    st.session_state.config['address'] = res['address_name']
                    st.session_state.config['radius'] = radius
                    st.rerun()
                else:
                    st.error(f"'{query}' 위치를 찾을 수 없습니다. 정확한 명칭이나 주소로 다시 시도해 주세요.")

    # 4. Calculation
    t_score, scores, counts, facilities, raw_progress = calculate_seulsekwon_index(
        st.session_state.config['coords'][0], 
        st.session_state.config['coords'][1], 
        st.session_state.data, 
        st.session_state.config['weights'], 
        st.session_state.config['radius']
    )
    viz = create_viz_objects(t_score, scores, counts, facilities, raw_progress)

    # 5. Sidebar
    with st.sidebar:
        st.title("⚙️ 설정 및 보고서")
        with st.expander("⚖️ 가중치 커스터마이징", expanded=True):
            st.caption("인프라 기여도 가중치를 합계 100으로 조정하세요.")
            new_weights = {}
            for cat, w_val in st.session_state.config['weights'].items():
                new_weights[cat] = st.slider(cat, 0, 50, w_val, step=5)
            
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
        st.download_button("📊 분석 데이터 CSV", data=pd.DataFrame(facilities).to_csv(index=False).encode('utf-8-sig'), 
                           file_name=f"analysis_{datetime.datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)

    # ✨ 탭 시스템 추가 (검색창 아래)
    tab1, tab2 = st.tabs(["🏙️ 슬세권 인프라 분석", "🏠 주변 실거래가 분석"])

    with tab1:
        # 7. AI Analysis Section
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

        # 6. Performance Layout (Map & Gauge)
        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.markdown(f'''
            <div class="dashboard-card" style="padding: 10px 24px; display: flex; align-items: center; min-height: 50px; margin-bottom: 0.8rem;">
                <h3 style="margin: 0; line-height: 1.2;">🗺️ 인프라 분포도: {st.session_state.config["address"]}</h3>
            </div>
            ''', unsafe_allow_html=True)
            st.markdown('<div class="dashboard-card" style="padding-top: 1rem;">', unsafe_allow_html=True)
            
            # 지도 필터 UI
            selected_groups = st.multiselect("표시할 시설 선택", options=list(CATEGORY_GROUPS.keys()), default=list(CATEGORY_GROUPS.keys()), key="map_view_filter")
            filtered_facilities = [f for f in facilities if f['group'] in selected_groups]

            folium_map = create_folium_map(st.session_state.config['coords'][0], st.session_state.config['coords'][1], filtered_facilities, st.session_state.config['radius'])
            map_interaction = st_folium(folium_map, width="100%", height=500, key="main_map")
            
            if map_interaction and map_interaction.get("last_clicked"):
                nc = (map_interaction["last_clicked"]["lat"], map_interaction["last_clicked"]["lng"])
                if round(nc[0], 5) != round(st.session_state.config['coords'][0], 5):
                    st.session_state.config['coords'] = nc
                    st.session_state.config['address'] = f"지정 포인트 ({nc[0]:.4f}, {nc[1]:.4f})"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with col_r:
            if t_score >= 90: grade_char = "s"
            elif t_score >= 75: grade_char = "a"
            elif t_score >= 60: grade_char = "b"
            elif t_score >= 40: grade_char = "c"
            else: grade_char = "d"
            
            st.markdown(f"""
            <div class="dashboard-card" style="height: 100%; display: flex; flex-direction: column; justify-content: center; padding: 20px;">
            <h3 style="text-align: center; margin-bottom: 10px;">💡 종합 편의 기여도</h3>
            <div class="metric-value">{t_score}</div>
            <div class="grade-badge grade-{grade_char}">{grade_char.upper()} GRADE</div>
            <div style="margin-top: 25px; width: 100%;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px; font-weight:bold; color:#64748b; font-size: 0.8rem;">
            <span>0</span><span>100</span>
            </div>
            <div style="background: #e2e8f0; border-radius: 12px; height: 16px; width: 100%; overflow: hidden;">
            <div style="background: linear-gradient(90deg, {THEME['primary']}, {THEME['accent']}); width: {t_score}%; height: 100%; border-radius: 12px;"></div>
            </div>
            </div>
            <p style="text-align: center; color: #64748b; margin-top: 20px; font-size: 0.9rem;">주변 인프라 밀도 분석 결과입니다.</p>
            </div>
            """, unsafe_allow_html=True)

        # 8. Detailed Charts
        st.markdown("### 📈 상세 데이터 분석")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'''
            <div class="dashboard-card" style="padding: 10px 24px; display: flex; align-items: center; min-height: 50px; margin-bottom: 0.8rem;">
                <h4 style="margin: 0; line-height: 1.2;">📊 카테고리 밸런스</h4>
            </div>
            ''', unsafe_allow_html=True)
            st.markdown('<div class="dashboard-card" style="padding-top: 1rem;">', unsafe_allow_html=True)
            st.plotly_chart(viz['radar'], use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'''
            <div class="dashboard-card" style="padding: 10px 24px; display: flex; align-items: center; min-height: 50px; margin-bottom: 0.8rem;">
                <h4 style="margin: 0; line-height: 1.2;">⚖️ 인프라 구성 비교</h4>
            </div>
            ''', unsafe_allow_html=True)
            st.markdown('<div class="dashboard-card" style="padding-top: 1rem;">', unsafe_allow_html=True)
            st.plotly_chart(viz['compare'], use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'''
            <div class="dashboard-card" style="padding: 10px 24px; display: flex; align-items: center; min-height: 50px; margin-bottom: 0.8rem;">
                <h4 style="margin: 0; line-height: 1.2;">📋 주요 시설 통계</h4>
            </div>
            ''', unsafe_allow_html=True)
            st.markdown('<div class="dashboard-card" style="padding-top: 1rem;">', unsafe_allow_html=True)
            stats_df = pd.DataFrame(counts.items(), columns=['분류', '개수']).sort_values('개수', ascending=False)
            st.dataframe(stats_df, hide_index=True, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("📍 전체 시설 리스트 보기", expanded=False):
            if facilities:
                st.dataframe(pd.DataFrame(facilities)[['group', 'name', 'distance', 'emoji']], use_container_width=True)
            else:
                st.info("데이터가 없습니다.")

    with tab2:
        # 9. Real Estate Analysis Section (3km Radius)
        st.markdown("### 🏠 반경 3km 내 실거래가 분포 분석")
        
        with st.spinner("주변 실거래 데이터 분석 중..."):
            recent_re = filter_data_within_radius(
                st.session_state.config['coords'][0], 
                st.session_state.config['coords'][1], 
                st.session_state.re_data, 
                3.0 # 3km radius
            )
            
        if not recent_re.empty:
            # AI 실거래 분석 리포트 추가
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

            col1, col2 = st.columns([1, 1])
            
            with col1:
                # 제목 박스 (높이 축소 및 중앙 정렬)
                st.markdown(f'''
                <div class="dashboard-card" style="padding: 10px 24px; display: flex; align-items: center; min-height: 50px; margin-bottom: 0.8rem;">
                    <h4 style="margin: 0; line-height: 1.2;">💰 면적 대비 가격 분포 (산포도)</h4>
                </div>
                ''', unsafe_allow_html=True)

                # 차트 카드
                st.markdown('<div class="dashboard-card" style="padding-top: 1rem;">', unsafe_allow_html=True)
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
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                # 제목 박스 (높이 축소 및 중앙 정렬)
                st.markdown(f'''
                <div class="dashboard-card" style="padding: 10px 24px; display: flex; align-items: center; min-height: 50px; margin-bottom: 0.8rem;">
                    <h4 style="margin: 0; line-height: 1.2;">📋 3km 반경 시장 요약</h4>
                </div>
                ''', unsafe_allow_html=True)

                avg_price = recent_re['price_억'].mean()
                median_price = recent_re['price_억'].median()
                
                # 최고가 매물 정보 추출
                max_row = recent_re.loc[recent_re['price_억'].idxmax()]
                max_price = max_row['price_억']
                max_bldg = max_row['BLDG_NM']
                max_area = max_row['ARCH_AREA']
                
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
                
            # 위치 분포 지도 제목 박스
            st.markdown(f'''
            <div class="dashboard-card" style="padding: 10px 24px; display: flex; align-items: center; min-height: 50px; margin-bottom: 0.8rem;">
                <h4 style="margin: 0; line-height: 1.2;">📍 실거래 위치 분포 (최근 500건)</h4>
            </div>
            ''', unsafe_allow_html=True)
            st.markdown('<div class="dashboard-card" style="padding-top: 1rem;">', unsafe_allow_html=True)
            p_map = create_price_map(st.session_state.config['coords'][0], st.session_state.config['coords'][1], recent_re, 3.0)
            st_folium(p_map, width="100%", height=500, key="re_price_map")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("반경 3km 내에 필터링된 실거래 데이터가 없습니다.")

if __name__ == "__main__":
    main()