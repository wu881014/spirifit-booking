import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, time, timedelta

# --- 資料庫設定 (SQLite) ---
def init_db():
    conn = sqlite3.connect('spirifit_bookings.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            phone TEXT,
            coach TEXT,
            booking_date TEXT,
            booking_time TEXT,
            status TEXT DEFAULT '已確認',
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_booking(name, phone, coach, date, time):
    conn = sqlite3.connect('spirifit_bookings.db')
    c = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO appointments (client_name, phone, coach, booking_date, booking_time, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, phone, coach, str(date), str(time), created_at))
    conn.commit()
    conn.close()

def get_bookings():
    conn = sqlite3.connect('spirifit_bookings.db')
    df = pd.read_sql_query("SELECT * FROM appointments", conn)
    conn.close()
    return df

# --- 頁面與佈局設定 ---
st.set_page_config(page_title="樂勁SpiriFit預約系統", page_icon="🏋️‍♂️", layout="centered")

# 系統啟動時初始化資料庫
init_db()

tab1, tab2 = st.tabs(["💪 學員預約介面", "⚙️ 工作室後台管理"])

# ==========================================
# Tab 1: 學員預約介面
# ==========================================
with tab1:
    st.title("🏋️‍♂️ 樂勁SpiriFit運動工作室")
    st.write("歡迎預約教練課程！每堂課為 1 小時，請選擇您屬意的教練與時段。")

    with st.form("booking_form", clear_on_submit=True):
        st.subheader("1. 選擇教練與時段")
        
        # 選擇教練
        coach = st.selectbox(
            "指定教練",
            ["Lily 教練", "Nick 教練", "Aaron 教練"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            # 日期：預設只能預約明天之後
            date = st.date_input("選擇日期", min_value=datetime.today() + timedelta(days=1))
        with col2:
            # 時間：早上9點到晚上10點 (最後預約時間為21:00，剛好上到22:00)
            available_times = [time(i, 0) for i in range(9, 22)]
            booking_time = st.selectbox("選擇時間", available_times, format_func=lambda t: t.strftime("%H:%M"))

        st.subheader("2. 學員資訊")
        name = st.text_input("學員姓名 *")
        phone = st.text_input("聯絡電話 *")
        
        submitted = st.form_submit_button("確認預約", type="primary", use_container_width=True)
        
        if submitted:
            if not name or not phone:
                st.error("⚠️ 請務必填寫姓名與聯絡電話！")
            else:
                add_booking(name, phone, coach, date, booking_time)
                st.success(f"🎉 預約成功！期待與您在工作室相見。\n\n**教練：** {coach}\n**時間：** {date} {booking_time.strftime('%H:%M')}")
                st.balloons()

# ==========================================
# Tab 2: 後台管理系統
# ==========================================
with tab2:
    st.title("系統管理後台")
    st.write("樂勁SpiriFit 內部預約資料庫")
    
    df = get_bookings()
    
    if not df.empty:
        # 依照日期與時間排序，讓最新的預約排在前面
        df = df.sort_values(by=['booking_date', 'booking_time'], ascending=[True, True])
        
        st.dataframe(
            df[['id', 'client_name', 'phone', 'coach', 'booking_date', 'booking_time', 'status']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": "編號",
                "client_name": "學員姓名",
                "phone": "電話",
                "coach": "教練",
                "booking_date": "預約日期",
                "booking_time": "預約時間",
                "status": "狀態"
            }
        )
        
        st.markdown("### 📊 預約統計")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("總預約數", len(df))
        
        # 簡單計算各教練的預約數
        coach_counts = df['coach'].value_counts()
        col2.metric("Lily 預約數", coach_counts.get("Lily 教練", 0))
        col3.metric("Nick 預約數", coach_counts.get("Nick 教練", 0))
        col4.metric("Aaron 預約數", coach_counts.get("Aaron 教練", 0))
        
        # 匯出資料為 CSV
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 匯出預約資料 (CSV)",
            data=csv,
            file_name=f"SpiriFit_bookings_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )
    else:
        st.info("目前尚無預約紀錄。")