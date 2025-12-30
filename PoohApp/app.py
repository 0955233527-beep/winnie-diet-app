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

# --- 樣式設定 (這裡修正了標題顏色) ---
st.markdown("""
    <style>
    /* 設定背景色 */
    .stApp { background-color: #FFFDF5; }
    
    /* [修正] 強制設定標題文字顏色為深咖啡色 */
    h1 { color: #5D4037; }

    /* 按鈕樣式 */
    .stButton button {
        background-color: #FFECB3;
        color: #5D4037;
        border: 2px solid #FFE082;
        aspect-ratio: 1 / 1;
        border-radius: 24px; 
        width: 100%;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .stButton button:hover {
        background-color: #FFD54F;
        border-color: #FFCA28;
        transform: translateY(-2px);
    }
    div[data-testid="stColumn"] button {
        aspect-ratio: auto;
        height: auto !important;
        padding: 0.2rem 0.5rem;
    }
    div[data-testid="stMetricValue"] { color: #D84315; }
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

    new_row = pd.DataFrame({
        '日期': [pd.to_datetime(date_obj)],
        '項目': [item],
        '價格': [price],
        '圖片路徑': [filename]
    })
    header = not os.path.exists(DATA_FILE)
    new_row.to_csv(DATA_FILE, mode='a', header=header, index=
