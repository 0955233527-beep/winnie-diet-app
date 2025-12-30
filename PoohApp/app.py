import streamlit as st
import pandas as pd
import os
import calendar
from datetime import datetime

# --- 設定 ---
DATA_FILE = 'diet_data.csv'
IMAGE_DIR = 'images'

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# --- 頁面設定 ---
st.set_page_config(page_title="🍰飲食日記🧋", page_icon="🍯", layout="centered")

# --- 樣式設定 (針對手機強制修正) ---
st.markdown("""
    <style>
    /* 全域背景與文字顏色 */
    .stApp { background-color: #FFFDF5; }
    h1, h2, h3, h4, .stMarkdown, p, span, div, label { 
        color: #5D4037 !important; 
    }
    
    /* 統計數字顏色 */
    div[data-testid="stMetricValue"] {
        color: #D84315 !important;
        font-weight: bold;
    }
    div[data-testid="stMetricLabel"] {
        color: #5D4037 !important;
    }
    
    /* [手機版核心修正] 強制欄位不堆疊，保持橫向排列 */
    @media (max-width: 768px) {
        div[data-testid="stColumn"] {
            width: auto !important;
            flex: 1 1 auto !important;
            min-width: 1px !important;
            padding: 0 2px !important;
        }
        /* 手機上按鈕字體縮小 */
        .stButton button {
            font-size: 12px !important; 
            padding: 0px !important;
            height: 35px !important;
        }
    }

    /* 按鈕樣式 (圓形) */
    .stButton button {
        background-color: #FFECB3;
        color: #5D4037 !important;
        border: 2px solid #FFE082;
        border-radius: 50%;
        width: 100%;
        aspect-ratio: 1 / 1;
        font-weight: bold;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton button:hover {
        background-color: #FFD54F;
        border-color: #FFCA28;
    }

    /* 圖片圓角 */
    img { border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- 功能函數 ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
            return df
        except: pass
    return pd.DataFrame(columns=['日期', '項目', '價格', '圖片路徑'])

def save_data_entry(date_obj, item, price, uploaded_file):
    filename = None
    if uploaded_file:
        file_ext = uploaded_file.name.split('.')[-1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}.{file_ext}"
        with open(os.path.join(IMAGE_DIR, filename), "wb") as f:
            f.write(uploaded_file.getbuffer())
