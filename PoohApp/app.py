import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import calendar
from datetime import datetime

# --- 設定 ---
# 這裡設定你的 Google Sheet 名稱
SHEET_NAME = 'diet_data'

# --- 頁面設定與 CSS (維持維尼風格) ---
st.set_page_config(page_title="維尼雲端記帳", page_icon="☁️", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFFDF5; }
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
        color: #BF360C;
        transform: translateY(-2px);
    }
    div[data-testid="stColumn"] button {
        aspect-ratio: auto;
        height: auto !important;
        padding: 0.2rem 0.5rem;
    }
    div[data-testid="stMetricValue"] { color: #D84315; }
    </style>
""", unsafe_allow_html=True)

# --- 1. 連線 Google Sheets 函數 ---
# 使用 st.cache_resource 避免每次操作都重新連線 Google，加快速度
@st.cache_resource
def get_google_sheet():
    # 這裡會從 Streamlit 的 Secrets 裡讀取鑰匙
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    sheet = client.open(SHEET_NAME).sheet1
    return sheet

# --- 2. 資料讀取與寫入 ---

def load_data():
    """從 Google Sheets 讀取所有資料"""
    try:
        sh = get_google_sheet()
        # 讀取所有紀錄轉成 DataFrame
        all_records = sh.get_all_records()
        if not all_records:
            return pd.DataFrame(columns=['日期', '項目', '價格'])
            
        df = pd.DataFrame(all_records)
        # 處理日期格式
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        return df
    except Exception as e:
        # 如果發生錯誤 (例如還沒設定 Secrets)
        # st.error(f"連線錯誤: {e}") 
        return pd.DataFrame(columns=['日期', '項目', '價格'])

def save_data_entry(date_obj, item, price):
    """新增一筆資料到 Google Sheets"""
    sh = get_google_sheet()
    # 將日期轉字串
    date_str = date_obj.strftime("%Y-%m-%d")
    # 寫入一行新資料 (Append)
    sh.append_row([date_str, item, price])
    # 清除快取，確保下次讀取是最新的
    st.cache_data.clear()

def delete_entry(original_index):
    """
    刪除資料
    注意：Google Sheets 是第 1 行開始，且第 1 行是標題。
    所以資料的 index 0 對應到 Sheet 的 Row 2。
    """
    sh = get_google_sheet()
    # 因為 gspread 刪除是看列號 (Row Number)
    # DataFrame index 0 -> Sheet Row 2 (標題佔 1 行)
    row_to_delete = original_index + 2
    sh.delete_rows(row_to_delete)
    st.cache_data.clear()

# --- 初始化 Session State ---
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None

# --- 主畫面邏輯 ---
st.title("☁️ 維尼雲端記帳本")
st.caption("資料直接存在 Google 雲端，手機也能用！")

# --- 上方：編輯與刪除區 ---
if st.session_state.selected_date:
    sel_date = st.session_state.selected_date
    st.info(f"正在編輯：{sel_date.strftime('%Y/%m/%d')}")
    
    with st.container(border=True):
        df = load_data()
        
        if not df.empty:
            # 篩選當日資料
            # 為了能正確刪除，我們需要保留原始的 index
            df['original_index'] = df.index
            day_records = df[df['日期'].dt.date == sel_date.date()]
            
            if not day_records.empty:
                st.write("📝 **今日已記錄：**")
                for _, row in day_records.iterrows():
                    c1, c2, c3 = st.columns([3, 2, 1])
                    with c1:
                        st.write(f"🍽️ {row['項目']}")
                    with c2:
                        st.write(f"💰 ${row['價格']}")
                    with c3:
                        # 傳入原始 index 進行刪除
                        if st.button("刪除", key=f"del_{row['original_index']}"):
                            delete_entry(row['original_index'])
                            st.rerun()
                st.divider()
        
        # 新增表單
        with st.form("entry_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                item = st.text_input("吃了什麼？")
            with c2:
                price = st.number_input("價格", min_value=0, step=1)
            
            if st.form_submit_button("✅ 存入雲端"):
                if item:
                    save_data_entry(sel_date, item, price)
                    st.success("已飛到雲端！")
                    st.rerun()

    if st.button("❌ 關閉"):
        st.session_state.selected_date = None
        st.rerun()

st.divider()

# --- 中間：年月選擇 ---
col_y, col_m = st.columns(2)
now = datetime.now()
with col_y:
    sel_year = st.selectbox("年份", range(now.year-2, now.year+3), index=2)
with col_m:
    sel_month = st.selectbox("月份", range(1, 13), index=now.month-1)

# --- 下方：日曆顯示 ---
df = load_data()
daily_sum = pd.Series(dtype='float64')

if not df.empty:
    df['Year'] = df['日期'].dt.year
    df['Month'] = df['日期'].dt.month
    month_data = df[(df['Year'] == sel_year) & (df['Month'] == sel_month)]
    daily_sum = month_data.groupby(df['日期'].dt.day)['價格'].sum()

# 產生格子
month_range = calendar.monthrange(sel_year, sel_month)
days_in_month = month_range[1]
cols_per_row = 4
cols = st.columns(cols_per_row)

for day in range(1, days_in_month + 1):
    col_index = (day - 1) % cols_per_row
    current_date = datetime(sel_year, sel_month, day)
    spent = daily_sum.get(day, 0)
    
    label = f"{day}\n\n${int(spent)}" if spent > 0 else f"{day}"

    with cols[col_index]:
        if st.button(label, key=f"btn_{day}", use_container_width=True):
            st.session_state.selected_date = current_date
            st.rerun()

st.markdown("---")
total_month = daily_sum.sum() if not daily_sum.empty else 0
st.metric("本月總支出", f"${int(total_month):,}")