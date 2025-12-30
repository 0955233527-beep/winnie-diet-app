import streamlit as st
import pandas as pd
import os
import calendar
from datetime import datetime

# --- 設定 ---
DATA_FILE = 'diet_data.csv'
IMAGE_DIR = 'images'

# 確保圖片資料夾存在
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# --- 頁面設定 ---
st.set_page_config(page_title="🍰飲食日記🧋", page_icon="🍯", layout="centered")

# --- 樣式設定 ---
st.markdown("""
    <style>
    /* 設定背景色 */
    .stApp { background-color: #FFFDF5; }
    
    /* [超級修正] 強制所有標題與文字變色，加上 !important 防止被手機深色模式蓋過 */
    h1, h2, h3, h4, .stMarkdown, p { 
        color: #5D4037 !important; 
    }
    
    /* 讓輸入框標題也變深色 */
    label {
        color: #5D4037 !important;
    }

    /* 按鈕樣式 */
    .stButton button {
        background-color: #FFECB3;
        color: #5D4037 !important;
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
    div[data-testid="stMetricValue"] { color: #D84315 !important; }
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
    new_row.to_csv(DATA_FILE, mode='a', header=header, index=False)

def delete_entry(index):
    df = load_data()
    df = df.drop(index)
    df.to_csv(DATA_FILE, index=False)

# --- 主程式邏輯 ---
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None

st.title("🍰飲食日記🧋")

if st.session_state.selected_date:
    sel_date = st.session_state.selected_date
    st.info(f"編輯：{sel_date.strftime('%Y/%m/%d')}")
    
    with st.container(border=True):
        df = load_data()
        if not df.empty:
            day_records = df[df['日期'].dt.date == sel_date.date()]
            for idx, row in day_records.iterrows():
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1: st.write(f"🍽️ {row['項目']}")
                with c2: st.write(f"💰 {row['價格']}")
                with c3: 
                    if st.button("刪", key=f"d_{idx}"):
                        delete_entry(idx)
                        st.rerun()
        
        with st.form("add"):
            c1, c2 = st.columns(2)
            with c1: item = st.text_input("項目")
            with c2: price = st.number_input("價格", step=1)
            file = st.file_uploader("照片", type=['jpg','png'])
            
            if st.form_submit_button("✅ 儲存"):
                if item:
                    save_data_entry(sel_date, item, price, file)
                    st.success("已儲存")
                    st.rerun()
    
    if st.button("❌ 關閉"):
        st.session_state.selected_date = None
        st.rerun()

st.divider()

col_y, col_m = st.columns(2)
now = datetime.now()
with col_y: y = st.selectbox("年", range(now.year-2, now.year+3), index=2)
with col_m: m = st.selectbox("月", range(1, 13), index=now.month-1)

df = load_data()
daily_sum = pd.Series(dtype='float64')
month_data = pd.DataFrame()

if not df.empty:
    df['Y'] = df['日期'].dt.year
    df['M'] = df['日期'].dt.month
    month_data = df[(df['Y'] == y) & (df['M'] == m)]
    daily_sum = month_data.groupby(df['日期'].dt.day)['價格'].sum()

cols = st.columns(4)
days = calendar.monthrange(y, m)[1]

for d in range(1, days+1):
    spent = daily_sum.get(d, 0)
    label = f"{d}\n\n${int(spent)}" if spent > 0 else f"{d}"
    
    with cols[(d-1)%4]:
# 如果你的迴圈變數是 i
if st.button(label, key=f"b_{i}"):

