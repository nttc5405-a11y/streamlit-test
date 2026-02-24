import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="住警器裝設地圖", page_icon="📍", layout="wide")

st.title("📍 住警器裝設地理分佈分析")

# 1. 建立連接
conn = st.connection("gsheets", type=GSheetsConnection)
URL = "https://docs.google.com/spreadsheets/d/1NCGE9kFRh85HJoVlsZhtA4PDc68TCTGtEG9v4TmFY0A/edit?gid=1508388728#gid=1508388728"

try:
    # 讀取 test0225 分頁
    df = conn.read(spreadsheet=URL, worksheet="test0225")
    
    # --- 修正欄位名稱 ---
    # 根據你的檔案，我們定義正確的對應
    lat_col = '緯度座標'
    lon_col = '經度座標'
    type_col = '補助資格(可複選-分類人員&住宅條件)'

    # 轉換經緯度，並強制處理錯誤
    df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
    df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
    
    # 剔除沒有座標的資料
    df_map = df.dropna(subset=[lat_col, lon_col])

    # --- 側邊欄篩選 ---
    st.sidebar.header("🗺️ 資料篩選")

    # 年度篩選
    years = sorted(df['年度'].unique().tolist())
    selected_years = st.sidebar.multiselect("選擇年度", years, default=years)

    # 補助資格篩選
    types = df[type_col].unique().tolist()
    selected_types = st.sidebar.multiselect("選擇對象類別", types, default=types)

    # 執行篩選
    mask = (df_map['年度'].isin(selected_years)) & (df_map[type_col].isin(selected_types))
    filtered_df = df_map[mask]

    # --- 數據展示 ---
    st.metric("當前顯示總數", f"{len(filtered_df)} 戶")

    # 地圖呈現 (重新命名為 lat/lon 以符合 Streamlit 要求)
    st.subheader("📍 成功分隊轄區分佈點位")
    map_data = filtered_df.rename(columns={lat_col: 'lat', lon_col: 'lon'})
    st.map(map_data)

    # 隱私保護：預覽資料
    with st.expander("查看明細資料 (已隱藏個資)"):
        # 排除包含個資的欄位
        display_df = filtered_df.drop(columns=['受補助人姓名', '國民身分證統一編號', '電話'], errors='ignore')
        st.dataframe(display_df)

except Exception as e:
    st.error(f"解析失敗！請確認分頁名稱是否為 'test0225'。錯誤詳細內容: {e}")
