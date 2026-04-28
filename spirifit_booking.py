import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, time, timedelta

# --- 頁面設定 ---
st.set_page_config(page_title="樂勁SpiriFit雲端管理系統", page_icon="🏋️‍♂️", layout="wide")

# --- 建立 Google Sheets 連線 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取資料
def get_data():
    return conn.read(ttl="0")

# 更新資料
def update_sheet(df):
    conn.update(data=df)
    st.cache_data.clear()

# --- 頁面邏輯 ---
st.title("🏋️‍♂️ 樂勁SpiriFit 雲端預約系統")
tab1, tab2 = st.tabs(["💪 學員預約介面", "⚙️ 工作室管理後台"])

# ==========================================
# Tab 1: 學員預約介面
# ==========================================
with tab1:
    st.info("💡 預約申請送出後，請等待教練審核確認。")
    
    with st.form("booking_form", clear_on_submit=True):
        coach = st.selectbox("指定教練", ["Lily 教練", "Nick 教練", "Aaron 教練"])
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("預約日期", min_value=datetime.today() + timedelta(days=1))
        with col2:
            booking_time = st.selectbox("預約時間", [time(i, 0) for i in range(9, 22)], format_func=lambda t: t.strftime("%H:%M"))
        
        name = st.text_input("學員姓名 *")
        phone = st.text_input("聯絡電話 *")
        submitted = st.form_submit_button("提交預約申請", type="primary", use_container_width=True)
        
        if submitted:
            if not name or not phone:
                st.error("⚠️ 欄位未填寫完整")
            else:
                existing_data = get_data()
                # 檢查重複
                is_taken = not existing_data[
                    (existing_data['coach'] == coach) & 
                    (existing_data['booking_date'] == str(date)) & 
                    (existing_data['booking_time'] == str(booking_time)) &
                    (existing_data['status'] != '已取消')
                ].empty
                
                if is_taken:
                    st.error("❌ 該時段已有預約，請更換。")
                else:
                    new_entry = pd.DataFrame([{
                        "id": len(existing_data) + 1,
                        "client_name": name,
                        "phone": phone,
                        "coach": coach,
                        "booking_date": str(date),
                        "booking_time": str(booking_time),
                        "status": "待確認",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
                    update_sheet(updated_df)
                    st.success("📩 申請成功！請靜候教練確認通知。")
                    st.balloons()

# ==========================================
# Tab 2: 工作室管理後台
# ==========================================
with tab2:
    password = st.text_input("後台管理密碼", type="password")
    if password == "spirifit888":
        df = get_data()
        
        # 數據面板
        confirmed = df[df['status'] == '已確認']
        st.subheader("📊 營運快報") # 剛才發生錯誤的地方
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("已確認課程", len(confirmed))
        c2.metric("Lily", len(confirmed[confirmed['coach'] == 'Lily 教練']))
        c3.metric("Nick", len(confirmed[confirmed['coach'] == 'Nick 教練']))
        c4.metric("Aaron", len(confirmed[confirmed['coach'] == 'Aaron 教練']))
        
        st.divider()
        st.subheader("📝 待處理預約")
        pending_df = df[df['status'] == '待確認'].sort_values('created_at', ascending=False)
        
        if pending_df.empty:
            st.info("目前沒有待處理的申請。")
        else:
            for _, row in pending_df.iterrows():
                with st.expander(f"待確認：{row['booking_date']} {row['booking_time']} - {row['client_name']}"):
                    st.write(f"教練：{row['coach']} | 電話：{row['phone']}")
                    b1, b2 = st.columns(2)
                    if b1.button("✅ 核准", key=f"ok_{row['id']}"):
                        df.loc[df['id'] == row['id'], 'status'] = '已確認'
                        update_sheet(df)
                        st.rerun()
                    if b2.button("❌ 取消", key=f"no_{row['id']}"):
                        df.loc[df['id'] == row['id'], 'status'] = '已取消'
                        update_sheet(df)
                        st.rerun()

        st.divider()
        if st.checkbox("查看所有歷史紀錄"):
            st.dataframe(df, use_container_width=True)
