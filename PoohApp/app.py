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

# --- 樣式設定 (手機版強制並排) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFDF5; }
    h1, h2, h3, h4, .stMarkdown, p, span, div, label { color: #5D4037 !important; }
    div[data-testid="stMetricValue"] { color: #D84315 !important; font-weight: bold; }
    
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; }
        [data-testid="stColumn"] { flex: 1 1 0px !important; min-width: 0px !important; padding: 0 1px !important; }
        .stButton button { font-size: 10px !important; height: 35px !important; }
    }
    .stButton button {
        background-color: #FFECB3; color: #5D4037 !important; border: 1px solid #FFE082;
        border-radius: 8px; width: 100%; aspect-ratio: 1/1; font-weight: bold;
    }
    img { border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- Google Sheets 連線 ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open(SPREADSHEET_NAME).sheet1
        return sheet
    except Exception as e:
        st.error(f"⚠️ 連線失敗原因：{e}")
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

def save_data_entry(date_obj, item, price, uploaded_file):
    sheet = get_google_sheet()
    if sheet:
        filename = ""
        if uploaded_file:
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            with open(os.path.join(IMAGE_DIR, filename), "wb") as f:
                f.write(uploaded_file.getbuffer())
        sheet.append_row([str(date_obj.date()), item, price, filename])

def delete_entry(index):
    sheet = get_google_sheet()
    if sheet:
        sheet.delete_rows(index + 2)

# --- 主程式 ---
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None

st.title("🍰飲食日記🧋")

# 1. 編輯區
if st.session_state.selected_date:
    sel_date = st.session_state.selected_date
    st.info(f"📅 編輯日期：{sel_date.strftime('%Y/%m/%d')}")
    with st.container(border=True):
        df = load_data()
        if not df.empty:
            day_records = df[df['日期'].dt.date == sel_date.date()].reset_index()
            for i, row in day_records.iterrows():
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1: st.write(f"🍽️ {row['項目']}")
                with c2: st.write(f"💰 {row['價格']}")
                with c3:
                    if st.button("刪", key=f"del_{row['index']}"):
                        delete_entry(row['index'])
                        st.rerun()
        with st.form("add"):
            item = st.text_input("項目")
            price = st.number_input("價格", step=1)
            file = st.file_uploader("上傳照片", type=['jpg','png','jpeg'])
            if st.form_submit_button("✅ 儲存"):
                if item:
                    save_data_entry(sel_date, item, price, file)
                    st.success("成功！")
                    st.rerun()
    if st.button("❌ 關閉編輯"):
        st.session_state.selected_date = None
        st.rerun()

st.divider()

# 2. 統計
col_y, col_m = st.columns(2)
now = datetime.now()
with col_y: y = st.selectbox("年份", range(now.year-1, now.year+2), index=1)
with col_m: m = st.selectbox("月份", range(1, 13), index=now.month-1)

df = load_data()
daily_sum = pd.Series(dtype='float64')
month_total = 0
if not df.empty and '價格' in df.columns:
    df['Y'] = df['日期'].dt.year
    df['M'] = df['日期'].dt.month
    month_data = df[(df['Y'] == y) & (df['M'] == m)]
    daily_sum = month_data.groupby(df['日期'].dt.day)['價格'].sum()
    month_total = month_data['價格'].sum()

st.metric("💰 本月總支出", f"${int(month_total)}")

# 3. 日曆
weeks = calendar.monthcalendar(y, m)
for week in weeks:
    cols = st.columns(7)
    for i, d in enumerate(week):
        with cols[i]:
            if d != 0:
                spent = daily_sum.get(d, 0)
                label = f"{d}\n${int(spent)}" if spent > 0 else f"{d}"
                if st.button(label, key=f"cal_{y}_{m}_{d}"):
                    st.session_state.selected_date = datetime(y, m, d)
                    st.rerun()

st.divider()

# 4. 📸 相簿功能
st.subheader("📸 飲食相簿")
if not df.empty and '圖片路徑' in df.columns:
    gallery_df = df[df['圖片路徑'].astype(str).str.len() > 5]
    if not gallery_df.empty:
        img_cols = st.columns(3)
        for i, (idx, row) in enumerate(gallery_df.iterrows()):
            img_path = os.path.join(IMAGE_DIR, str(row['圖片路徑']))
            if os.path.exists(img_path):
                with img_cols[i % 3]:
                    st.image(img_path)
                    st.caption(f"{row['日期'].strftime('%m/%d')} - {row['項目']}")
