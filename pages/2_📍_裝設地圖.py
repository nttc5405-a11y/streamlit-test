import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 頁面基本設定
st.set_page_config(page_title="住警器裝設地圖", page_icon="📍", layout="wide")

st.title("📍 住警器裝設地理分佈分析")
st.write("目前顯示：臺東縣政府補助安裝住宅用火災警報器清冊數據")

# --- 1. 建立連接與讀取資料 ---
conn = st.connection("gsheets", type=GSheetsConnection)
# 請確認此處 URL 為你的 Google Sheets 網址，且工作表名稱正確
URL = "https://docs.google.com/spreadsheets/d/1NCGE9kFRh85HJoVlsZhtA4PDc68TCTGtEG9v4TmFY0A/edit?gid=1508388728#gid=1508388728"

try:
    # 讀取資料，假設工作表名稱為 "成功分隊" 或你的實際名稱
    df = conn.read(spreadsheet=URL, worksheet="test0225")
    
    # --- 2. 資料清洗與格式轉換 ---
    # 根據你的截圖，經緯度欄位名稱可能是 'G' 或 'H' 欄（或是你命名的 '緯度', '經度'）
    # 請確保下方的欄位名稱與你試算表首行的文字完全一致
    lat_col = '緯度' # 如果你的標題是'緯度'，請更換
    lon_col = '經度' # 如果你的標題是'經度'，請更換
    
    # 轉換經緯度為數字格式，並剔除無法轉換的空值
    df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
    df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
    df = df.dropna(subset=[lat_col, lon_col])

    # --- 3. 側邊欄篩選器 (根據你的截圖欄位) ---
    st.sidebar.header("🗺️ 資料篩選")

    # (1) 年度篩選
    years = sorted(df['年度'].unique().tolist())
    selected_years = st.sidebar.multiselect("選擇年度", years, default=years)

    # (2) 補助資格篩選 (對應你的 '補助資格' 欄位)
    if '補助資格' in df.columns:
        types = df['補助資格'].unique().tolist()
        selected_types = st.sidebar.multiselect("選擇對象類別", types, default=types)
    else:
        selected_types = None

    # (3) 裝置位置篩選
    positions = df['裝置位置'].unique().tolist()
    selected_pos = st.sidebar.multiselect("選擇裝置位置", positions, default=positions)

    # --- 4. 執行篩選邏輯 ---
    query_mask = (df['年度'].isin(selected_years)) & (df['裝置位置'].isin(selected_pos))
    if selected_types:
        query_mask &= (df['補助資格'].isin(selected_types))
        
    filtered_df = df[query_mask]

    # --- 5. 數據看板展示 ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("總裝設戶數", f"{len(filtered_df)} 戶")
    with col2:
        st.metric("最新裝設年度", f"{max(selected_years) if selected_years else 'N/A'}")
    with col3:
        # 計算一下本頁顯示的總數量 (對應你的 '裝置數量' 欄位)
        total_units = filtered_df['裝置數量'].sum() if '裝置數量' in df.columns else len(filtered_df)
        st.metric("總裝設顆數", f"{int(total_units)} 顆")

    # --- 6. 地圖呈現 ---
    st.subheader("📍 成功分隊轄區分佈點位")
    
    # 準備地圖專用資料格式 (Streamlit 辨識 lat, lon)
    map_display_df = filtered_df.rename(columns={lat_col: 'lat', lon_col: 'lon'})
    
    if not map_display_df.empty:
        # 顯示地圖
        st.map(map_display_df)
    else:
        st.warning("目前篩選條件下沒有可顯示的座標數據。")

    # --- 7. 資料預覽 (自動隱藏個資欄位) ---
    with st.expander("查看明細資料 (已自動隱藏身分證字號與電話)"):
        # 這裡為了隱私，過濾掉身分證和電話欄位不顯示在網頁上
        safe_display = filtered_df.drop(columns=['國民身分證統一編號', '電話'], errors='ignore')
        st.dataframe(safe_display, use_container_width=True)

except Exception as e:
    st.error(f"連線或解析失敗。請確認：\n1. 網址是否正確\n2. 欄位名稱(年度/緯度/經度)是否與試算表一致\n錯誤訊息: {e}")
