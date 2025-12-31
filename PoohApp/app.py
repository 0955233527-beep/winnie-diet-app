import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# --- 設定 ---
SPREADSHEET_NAME = 'diet_data' 
IMAGE_DIR = 'images'

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# --- 頁面設定 ---
st.set_page_config(page_title="🍰飲食日記🧋", page_icon="🍯", layout="centered")

# --- 樣式設定 (再次強化日曆美觀度) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFDF5; }
    h1, h2, h3, h4, .stMarkdown, p, span, div, label { color: #5D4037 !important; }
    div[data-testid="stMetricValue"] { color: #D84315 !important; font-weight: bold; }
    
    [data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; }
    [data-testid="stColumn"] { flex: 1 1 0px !important; min-width: 0px !important; padding: 0 1px !important; }

    .stButton button {
        background-color: #FFECB3; color: #5D4037 !important; border: 1px solid #FFE082;
        border-radius: 8px; width: 100%; aspect-ratio: 1/1; font-weight: bold;
        padding: 2px !important; font-size: 11px !important; line-height: 1.1 !important;
        display: flex; align-items: center; justify-content: center;
        white-space: pre-line !important;
    }
    .stButton button:hover { background-color: #FFD54F; }
    img { border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- Google Sheets 連線 ---
@st.cache_resource # 使用快取減少連線次數，更穩定
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            return client.open(SPREADSHEET_NAME).sheet1
        else:
            return None
    except Exception as e:
        st.error(f"連線偵測中... 請確認 Secrets 設定或重啟 App")
        return None

# --- 功能函數 ---
def load_data():
    sheet = get_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty and '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
                return df
        except: pass
    return pd.DataFrame(columns=['日期', '項目', '價格', '圖片路徑'])

# --- 剩下的主程式邏輯與昨天相同 ---
# (為了節省篇幅，請確保你保留了昨天的 save_data_entry 和日曆邏輯)
