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

# 檢查該時段是否已被預約
def is_slot_available(coach, date, time):
    conn = sqlite3.connect('spirifit_bookings.db')
    c = conn.cursor()
    c.execute('''
        SELECT * FROM appointments 
        WHERE coach = ? AND booking_date = ? AND booking_time = ?
    ''', (coach, str(date), str(time)))
    result = c.fetchone()
    conn.close()
    return result is None

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

# --- 頁面設定 ---
st.set_page_config(page_title="樂勁SpiriFit預約系統", page_icon="🏋️‍♂️", layout="centered")

init_db()

tab1, tab2 = st.tabs(["💪 學員預約介面", "⚙️ 工作室後台管理"])

# ==========================================
# Tab 1: 學員預約介面
# ==========================================
with tab1:
    st.title("🏋️‍♂️ 樂勁SpiriFit運動工作室")
    st.write("歡迎預約教練課程！每堂課 1 小時。")

    with st.form("booking_form", clear_on_submit=False): # 改為 False 方便預約失敗時保留資料
        st.subheader("1. 選擇教練與時段")
        
        coach = st.selectbox("指定教練", ["Lily 教練", "Nick 教練", "Aaron 教練"])
        
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("選擇日期", min_value=datetime.today() + timedelta(days=1))
        with col2:
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
                # 執行檢查邏輯
                if is_slot_available(coach, date, booking_time):
                    add_booking(name, phone, coach, date, booking_time)
                    st.success(f"🎉 預約成功！\n\n**教練：** {coach}\n**時間：** {date} {booking_time.strftime('%H:%M')}")
                    st.balloons()
                else:
                    st.error(f"❌ 預約失敗：{coach} 在 {date} {booking_time.strftime('%H:%M')} 已經有預約了，請選擇其他時段或教練。")

# ==========================================
# Tab 2: 後台管理系統
# ==========================================
with tab2:
    st.title("系統管理後台")
    
    # --- 密碼鎖設定 ---
    password = st.text_input("請輸入管理員密碼", type="password")
    
    # 這裡可以修改你的密碼
    if password == "spirifit888":
        st.success("密碼正確，歡迎回來！")
        
        df = get_bookings()
        if not df.empty:
            df = df.sort_values(by=['booking_date', 'booking_time'], ascending=[True, True])
            st.dataframe(
                df[['id', 'client_name', 'phone', 'coach', 'booking_date', 'booking_time', 'status']],
                use_container_width=True, hide_index=True
            )
            
            st.markdown("### 📊 營運統計")
            col1, col2, col3, col4 = st.columns(4)
            coach_counts = df['coach'].value_counts()
            col1.metric("總預約", len(df))
            col2.metric("Lily", coach_counts.get("Lily 教練", 0))
            col3.metric("Nick", coach_counts.get("Nick 教練", 0))
            col4.metric("Aaron", coach_counts.get("Aaron 教練", 0))
        else:
            st.info("目前尚無預約紀錄。")
    elif password == "":
        st.info("請輸入密碼以查看預約清單。")
    else:
        st.error("密碼錯誤，請重新輸入。")
