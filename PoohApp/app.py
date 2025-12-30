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
    .stApp { background-color: #FFFDF5; }
    h1, h2, h3, h4, .stMarkdown, p, span, div { 
        color: #5D4037 !important; 
    }
    label {
        color: #5D4037 !important;
    }
    .stButton button {
        background-color: #FFECB3;
        color: #5D4037 !important;
        border: 2px solid #FFE082;
        border-radius: 50%;
        width: 100%;
        aspect-ratio: 1 / 1;
        font-weight: bold;
        padding: 0;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .stButton button:hover {
        background-color: #FFD54F;
        border-color: #FFCA28;
    }
    div[data-testid="stColumn"] {
        text-align: center;
    }
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

# 1. 編輯區塊
if st.session_state.selected_date:
    sel_date = st.session_state.selected_date
    st.info(f"正在編輯：{sel_date.strftime('%Y/%m/%d')}")
    
    with st.container(border=True):
        df = load_data()
        if not df.empty:
            day_records = df[df['日期'].dt.date == sel_date.date()]
            for idx, row in day_records.iterrows():
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1: st.write(f"🍽️ {row['項目']}")
                with c2: st.write(f"💰 {row['價格']}")
                with c3: 
                    if st.button("刪", key=f"del_{idx}"):
                        delete_entry(idx)
                        st.rerun()
        
        st.write("---")
        st.write("📝 **新增紀錄**")
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            with c1: item = st.text_input("項目")
            with c2: price = st.number_input("價格", step=1)
            file = st.file_uploader("照片 (選填)", type=['jpg','png', 'jpeg'])
            
            if st.form_submit_button("✅ 儲存"):
                if item:
                    save_data_entry(sel_date, item, price, file)
                    st.success("已儲存！")
                    st.rerun()
                else:
                    st.warning("請輸入項目名稱")
    
    if st.button("❌ 關閉編輯"):
        st.session_state.selected_date = None
        st.rerun()

st.divider()

# 2. 日曆篩選區
col_y, col_m = st.columns(2)
now = datetime.now()
with col_y: y = st.selectbox("年份", range(now.year-2, now.year+3), index=2)
with col_m: m = st.selectbox("月份", range(1, 13), index=now.month-1)

df = load_data()
daily_sum = pd.Series(dtype='float64')

if not df.empty:
    df['Y'] = df['日期'].dt.year
    df['M'] = df['日期'].dt.month
    month_data = df[(df['Y'] == y) & (df['M'] == m)]
    daily_sum = month_data.groupby(df['日期'].dt.day)['價格'].sum()

# 3. 日曆顯示 (7欄)
st.write("#### 📅 點擊日期來紀錄")
cols = st.columns(7) 
days = calendar.monthrange(y, m)[1]

for d in range(1, days+1):
    spent = daily_sum.get(d, 0)
    label = f"{d}\n${int(spent)}" if spent > 0 else f"{d}"
    
    with cols[(d-1)%7]:
        if st.button(label, key=f"cal_btn_{d}"):
            st.session_state.selected_date = datetime(y, m, d)
            st.rerun()

st.divider()

# 4. 相簿功能
st.subheader("📸 飲食相簿")

# 這裡就是容易出錯的地方，我已經確保縮排正確
if not df.empty:
    gallery_df = df[df['圖片路徑'].notna()]
    gallery_df = gallery_df[(gallery_df['Y'] == y) & (gallery_df['M'] == m)]
    
    if not gallery_df.empty:
        img_cols = st.columns(3)
        for i, (idx, row) in enumerate(gallery_df.iterrows()):
            img_path = os.path.join(IMAGE_DIR, row['圖片路徑'])
            if os.path.exists(img_path):
                with img_cols[i % 3]:
                    st.image(img_path, use_container_width=True)
                    st.caption(f"{row['日期'].strftime('%m/%d')} - {row['項目']}")
    else:
        st.info("這個月份還沒有上傳照片喔！")
else:
    st.info("目前沒有任何紀錄。")
