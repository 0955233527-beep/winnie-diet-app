import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# --- 設定 ---
# 請確保你的 Google 試算表名稱「完全」叫做 diet_data
SPREADSHEET_NAME = 'diet_data' 

# --- 頁面設定 ---
st.set_page_config(page_title="🍰飲食日記🧋", page_icon="🍯", layout="centered")

# --- 樣式設定 (手機版強制並排修正) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFDF5; }
    h1, h2, h3, h4, .stMarkdown, p, span, div, label { color: #5D4037 !important; }
    
    /* 支出金額顏色 */
    div[data-testid="stMetricValue"] { color: #D84315 !important; font-weight: bold; }

    /* 手機版日曆格子強制並排 */
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
        }
        [data-testid="stColumn"] {
            flex: 1 1 0px !important;
            min-width: 0px !important;
            padding: 0 1px !important;
        }
        .stButton button {
            font-size: 10px !important;
            height: 35px !important;
        }
    }

    /* 按鈕圓角樣式 */
    .stButton button {
        background-color: #FFECB3; color: #5D4037 !important; border: 1px solid #FFE082;
        border-radius: 8px; width: 100%; aspect-ratio: 1/1; font-weight: bold;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .stButton button:hover { background-color: #FFD54F; }
    </style>
""", unsafe_allow_html=True)

# --- Google Sheets 連線設定 ---
def get_google_sheet():
    try:
        # 從 Secrets 讀取憑證
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # 嘗試開啟試算表
        return client.open(SPREADSHEET_NAME).sheet1
    except Exception as e:
        # 在網頁上顯示具體錯誤原因
        st.error(f"❌ Google 連線失敗原因：{e}")
        return None

# --- 功能函數 ---
def load_data():
    sheet = get_google_sheet()
