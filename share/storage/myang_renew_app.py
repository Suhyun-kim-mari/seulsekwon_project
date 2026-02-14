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
