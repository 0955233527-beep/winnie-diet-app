import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 設定 ---
# 這是你在 Google 試算表取的名稱，必須一模一樣
SPREADSHEET_NAME = 'diet_data' 

# --- 頁面設定 ---
st.set_page_config(page_title="🍰飲食日記🧋", page_icon="🍯", layout="centered")

# --- 樣式設定 (手機版優化) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFDF5; }
    h1, h2, h3, h4, .stMarkdown, p, span, div, label { color: #5D4037 !important; }
    div[data-testid="stMetricValue"] { color: #D84315 !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { color: #5D4037 !important; }
    
    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; }
        div[data-testid="stColumn"] { flex: 1 1 0px !important; min-width: 0px !important; padding: 0 1px !important; }
        .stButton button { font-size: 10px !important; padding: 0px !important; min-height: 35px !important; height: auto !important; line-height: 1.2 !important; }
    }
    .stButton button {
        background-color: #FFECB3; color: #5D4037 !important; border: 2px solid #FFE082;
        border-radius: 50%; width: 100%; aspect-ratio: 1 / 1; font-weight: bold;
        margin: 0 auto; display: flex; align-items: center; justify-content: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); white-space: pre-wrap;
    }
    .stButton button:hover { background-color: #FFD54F; border-color: #FFCA28; }
    </style>
""", unsafe_allow_html=True)

# --- Google Sheets 連線設定 ---
def get_google_sheet():
    # 從 Streamlit Secrets 讀取金鑰
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    try:
        sheet = client.open(SPREADSHEET_NAME).sheet1
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"找不到名稱為 '{SPREADSHEET_NAME}' 的試算表，請確認 Google Drive 裡有這個檔案，且已共用給機器人。")
        return None

# --- 功能函數 ---
def load_data():
    sheet = get_google_sheet()
    if sheet:
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            # 轉換欄位名稱 (如果試算表是用英文，這裡可以對應，目前假設試算表第一行是中文)
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
            return df
        else:
            # 初始化標題
            sheet.append_row(['日期', '項目', '價格'])
    return pd.DataFrame(columns=['日期', '項目', '價格'])

def save_data_entry(date_obj, item, price):
    sheet = get_google_sheet()
    if sheet:
        # 寫入 Google Sheet
        sheet.append_row([str(date_obj), item, price])

def delete_entry(index):
    sheet = get_google_sheet()
    if sheet:
        # Google Sheet 的行數從 1 開始，且第 1 行是標題，所以資料索引要 +2
        sheet.delete_rows(index + 2)

# --- 主程式邏輯 ---
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None

st.title("🍰飲食日記🧋 (雲端版)")
# --- 診斷程式碼 (測試完後可以刪除) ---
st.write("🔍 正在診斷連線...")
try:
    test_sheet = get_google_sheet()
    if test_sheet:
        st.success(f"✅ 成功連線到試算表！")
        st.write("目前資料：", test_sheet.get_all_records())
    else:
        st.error("❌ 無法找到試算表，請檢查檔名是否為 'diet_data'，且機器人已加入共用。")
except Exception as e:
    st.error(f"❌ 連線發生錯誤 (請截圖給工程師)：{e}")
# -----------------------------------
# 1. 編輯區塊
if st.session_state.selected_date:
    sel_date = st.session_state.selected_date
    st.info(f"正在編輯：{sel_date.strftime('%Y/%m/%d')}")
    
    with st.container(border=True):
        df = load_data()
        if not df.empty:
            day_records = df[df['日期'].dt.date == sel_date.date()]
            # 重新重置 index 以便正確刪除
            day_records = day_records.reset_index() 
            
            for i, row in day_records.iterrows():
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1: st.write(f"🍽️ {row['項目']}")
                with c2: st.write(f"💰 {row['價格']}")
                with c3: 
                    # 傳入原本 DataFrame 的真實 index
                    original_idx = row['index']
                    if st.button("刪", key=f"del_{original_idx}"):
                        delete_entry(original_idx)
                        st.rerun()
        
        st.write("---")
        st.write("📝 **新增紀錄**")
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            with c1: item = st.text_input("項目")
            with c2: price = st.number_input("價格", step=1)
            
            if st.form_submit_button("✅ 儲存"):
                if item:
                    save_data_entry(sel_date, item, price)
                    st.success("已儲存到 Google 試算表！")
                    st.rerun()
                else:
                    st.warning("請輸入項目名稱")
    
    if st.button("❌ 關閉編輯"):
        st.session_state.selected_date = None
        st.rerun()

st.divider()

# 2. 日曆篩選與統計
col_y, col_m = st.columns(2)
now = datetime.now()
with col_y: y = st.selectbox("年份", range(now.year-2, now.year+3), index=2)
with col_m: m = st.selectbox("月份", range(1, 13), index=now.month-1)

df = load_data()
daily_sum = pd.Series(dtype='float64')
month_total = 0

if not df.empty and '日期' in df.columns:
    df['Y'] = df['日期'].dt.year
    df['M'] = df['日期'].dt.month
    month_data = df[(df['Y'] == y) & (df['M'] == m)]
    
    daily_sum = month_data.groupby(df['日期'].dt.day)['價格'].sum()
    month_total = month_data['價格'].sum()

st.metric("💰 本月總支出", f"${int(month_total)}")

# 3. 日曆顯示
st.write("#### 📅 點擊日期來紀錄")
month_weeks = calendar.monthcalendar(y, m)

for week in month_weeks:
    cols = st.columns(7) 
    for i, d in enumerate(week):
        with cols[i]:
            if d != 0:
                spent = daily_sum.get(d, 0)
                label = f"{d}\n${int(spent)}" if spent > 0 else f"{d}"
                if st.button(label, key=f"cal_{y}_{m}_{d}"):
                    st.session_state.selected_date = datetime(y, m, d)
                    st.rerun()
            else:
                st.write("")

