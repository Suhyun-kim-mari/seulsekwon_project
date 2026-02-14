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

load_dotenv()

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
def get_coords_from_address(address: str):
    """주소를 위도/경도로 변환합니다."""
    api_key = get_kakao_api_key()
    if not api_key:
        return None
        
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    try:
        response = requests.get(url, headers=headers, params={"query": address}, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if result['documents']:
                info = result['documents'][0]
                return {
                    "address_name": info['address_name'],
                    "lat": float(info['y']),
                    "lng": float(info['x'])
                }
    except Exception as e:
        st.error(f"주소 검색 중 오류 발생: {e}")
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
    # 최종 통합 및 중복 제거된 데이터 파일 경로 (v2)
    file_path = "/Users/kimsuhyun/Desktop/fcicb6/seoul_seulsekwon/data/seoul_combined_data_final_v3.csv"
    
    if not os.path.exists(file_path):
        # 상대 경로 시도
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, "..", "data", "seoul_combined_data_final.csv")
        
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
    
    if 'config' not in st.session_state:
        st.session_state.config = {
            'coords': (37.5665, 126.9780),
            'address': "서울시청",
            'radius': 500,
            'weights': DEFAULT_WEIGHTS.copy()
        }

    # 2. Main Header
    st.markdown(f'<h1 style="text-align: center; color: {THEME["secondary"]}; margin-bottom: 2rem;">🏙️ SEOUL SEULSEKWON ANALYTICS</h1>', unsafe_allow_html=True)

    # 3. Search Form
    with st.container():
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        with st.form("search_form"):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                query = st.text_input("📍 분석할 위치 (주소 또는 키워드)", value=st.session_state.config['address'])
            with c2:
                radius = st.select_slider("📏 반경 (m)", options=[300, 500, 700, 1000, 1500], value=st.session_state.config['radius'])
            with c3:
                st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
                btn_submit = st.form_submit_button("지수 산출하기", use_container_width=True)
                
        if btn_submit and query:
            with st.spinner("위치 동기화 중..."):
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
        st.subheader("📥 결과 다운로드")
        # 간단한 JSON 또는 CSV 내보내기 가능
        st.download_button("📊 분석 데이터 CSV", data=pd.DataFrame(facilities).to_csv(index=False).encode('utf-8-sig'), 
                           file_name=f"analysis_{datetime.datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)
        
        st.markdown("---")
        st.caption(f"Engine v2.5 | {datetime.datetime.now().strftime('%Y-%m-%d')}")

    # 6. Layout - Dash Performance
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.markdown(f'<div class="dashboard-card"><h3>🗺️ 인프라 분포도: {st.session_state.config["address"]}</h3>', unsafe_allow_html=True)
        folium_map = create_folium_map(st.session_state.config['coords'][0], st.session_state.config['coords'][1], facilities, st.session_state.config['radius'])
        map_interaction = st_folium(folium_map, width="100%", height=500, key="main_map")
        
        # 지도 클릭시 중심지 변경 로직
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

if __name__ == "__main__":
    main()
