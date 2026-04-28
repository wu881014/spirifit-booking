import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, time, timedelta

# --- 資料庫設定 ---
def init_db():
    conn = sqlite3.connect('spirifit_bookings.db')
    c = conn.cursor()
    # 增加 status 欄位邏輯
    c.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            phone TEXT,
            coach TEXT,
            booking_date TEXT,
            booking_time TEXT,
            status TEXT DEFAULT '待確認',
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

# 更新預約狀態的功能
def update_status(appointment_id, new_status):
    conn = sqlite3.connect('spirifit_bookings.db')
    c = conn.cursor()
    c.execute('UPDATE appointments SET status = ? WHERE id = ?', (new_status, appointment_id))
    conn.commit()
    conn.close()

def get_bookings():
    conn = sqlite3.connect('spirifit_bookings.db')
    df = pd.read_sql_query("SELECT * FROM appointments", conn)
    conn.close()
    return df

def is_slot_available(coach, date, time):
    conn = sqlite3.connect('spirifit_bookings.db')
    c = conn.cursor()
    # 只要不是「已取消」的預約，都視為佔用時段
    c.execute('''
        SELECT * FROM appointments 
        WHERE coach = ? AND booking_date = ? AND booking_time = ? AND status != '已取消'
    ''', (coach, str(date), str(time)))
    result = c.fetchone()
    conn.close()
    return result is None

# --- 頁面設定 ---
st.set_page_config(page_title="樂勁SpiriFit預約管理系統", page_icon="🏋️‍♂️", layout="wide")

init_db()

tab1, tab2 = st.tabs(["💪 學員預約介面", "⚙️ 工作室管理後台"])

# ==========================================
# Tab 1: 學員預約介面
# ==========================================
with tab1:
    st.title("🏋️‍♂️ 樂勁SpiriFit運動工作室")
    st.info("💡 提醒：提交預約後，需等待教練確認才算預約成功喔！")

    with st.form("booking_form"):
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
        
        submitted = st.form_submit_button("提交預約申請", type="primary", use_container_width=True)
        
        if submitted:
            if not name or not phone:
                st.error("⚠️ 請填寫姓名與電話。")
            else:
                if is_slot_available(coach, date, booking_time):
                    add_booking(name, phone, coach, date, booking_time)
                    st.success(f"📩 申請已送出！教練確認後會再通知您。\n\n時段：{date} {booking_time.strftime('%H:%M')}")
                else:
                    st.error("❌ 該時段已有預約或審核中，請更換時段。")

# ==========================================
# Tab 2: 工作室管理後台
# ==========================================
with tab2:
    st.title("管理員登入")
    password = st.text_input("輸入管理密碼", type="password")
    
    if password == "spirifit888":
        st.divider()
        df = get_bookings()
        
        if not df.empty:
            # 統計面版 (僅計算已確認)
            confirmed_df = df[df['status'] == '已確認']
            st.subheader("📊 營運快報 (僅計
