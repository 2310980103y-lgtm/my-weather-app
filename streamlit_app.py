import streamlit as st
# (中略)

# --- ここを一番上（importのすぐ後）に追加 ---
st.markdown("""
    <head>
        <link rel="manifest" href="/manifest.json">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    </head>
""", unsafe_allow_html=True)
import streamlit as st
import datetime as dt
import requests
import plotly.graph_objects as go

# --- 1. アプリ設定 ---
st.set_page_config(page_title="RainCall+", page_icon="☔", layout="centered")

# --- 2. 設定 ---
LOCS = {
    "広島": {"lat": 34.38, "lon": 132.45}, "東京": {"lat": 35.68, "lon": 139.69},
    "札幌": {"lat": 43.06, "lon": 141.34}, "大阪": {"lat": 34.69, "lon": 135.5},
    "福岡": {"lat": 33.59, "lon": 130.4}, "那覇": {"lat": 26.21, "lon": 127.68}
}

conf = {
    "loc": "広島", "threshold": 30, "vibrate": True, 
    "complete": False, "selected_day": 0,
    "time_morning": dt.time(7,0), "time_lunch": dt.time(12,0), "time_evening": dt.time(18,0)
}
for k, v in conf.items():
    if k not in st.session_state: st.session_state[k] = v

# --- 3. データ取得 (湿度 relative_humidity_2m を追加) ---
c = LOCS[st.session_state.loc]
api_url = f"https://api.open-meteo.com/v1/forecast?latitude={c['lat']}&longitude={c['lon']}&current=temperature_2m,relative_humidity_2m&hourly=precipitation_probability,relative_humidity_2m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia/Tokyo"
res = requests.get(api_url).json()

# --- 4. アイコン変換辞書 ---
def get_icon(code):
    if code == 0: return "☀️"
    if code <= 3: return "🌤️"
    if code <= 48: return "☁️"
    if code <= 67: return "☔"
    return "⚡"

# --- 5. デザイン ---
w_code = res["daily"]["weather_code"][st.session_state.selected_day]
if w_code >= 51: bg = "https://images.unsplash.com/photo-1428592953211-077101b2021b?w=1000"
elif 1 <= w_code <= 48: bg = "https://images.unsplash.com/photo-1499346030926-9a72daac6c63?w=1000"
else: bg = "https://images.unsplash.com/photo-1544933863-482c6cdcd5d1?w=1000"

st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{ background: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url("{bg}"); background-size: cover; }}
    .main .block-container {{ background: rgba(10, 15, 20, 0.85); border-radius: 20px; color: white; backdrop-filter: blur(15px); padding: 1.5rem; }}
    .week-card {{ background: rgba(255,255,255,0.1); border-radius: 10px; padding: 5px; text-align: center; border: 1px solid rgba(255,255,255,0.1); }}
</style>
""", unsafe_allow_html=True)

# --- 6. メイン画面 ---
page = st.sidebar.radio("Menu", ["🏠 ホーム", "⚙️ 詳細設定"])

if page == "🏠 ホーム":
    st.markdown("<h2 style='text-align:center;'>RainCall+</h2>", unsafe_allow_html=True)
    
    # 今の状況
    if st.session_state.selected_day == 0:
        c1, c2 = st.columns(2)
        c1.metric("今の気温", f"{res['current']['temperature_2m']}°")
        c2.metric("今の湿度", f"{res['current']['relative_humidity_2m']}%")

    st.write("---")
    # 選択日の詳細
    st.write(f"📅 {res['daily']['time'][st.session_state.selected_day]} ({st.session_state.loc})")
    col1, col2, col3 = st.columns(3)
    col1.metric("最高", f"{res['daily']['temperature_2m_max'][st.session_state.selected_day]}°")
    col2.metric("雨率", f"{res['daily']['precipitation_probability_max'][st.session_state.selected_day]}%")
    col3.metric("最低", f"{res['daily']['temperature_2m_min'][st.session_state.selected_day]}°")

    # グラフ (降水確率と湿度)
    h_idx = st.session_state.selected_day * 24
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[f"{i}h" for i in range(24)], y=res["hourly"]["precipitation_probability"][h_idx:h_idx+24], name="雨率(%)", line=dict(color='#40E0D0', width=3)))
    fig.add_trace(go.Scatter(x=[f"{i}h" for i in range(24)], y=res["hourly"]["relative_humidity_2m"][h_idx:h_idx+24], name="湿度(%)", line=dict(color='#FFA500', width=2, dash='dot')))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=220, font=dict(color="white"), margin=dict(l=0,r=0,t=10,b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

    # --- 週間一目瞭然タップエリア ---
    st.write("### 週間予報 (タップで詳細)")
    week_cols = st.columns(7)
    for i in range(7):
        with week_cols[i]:
            icon = get_icon(res["daily"]["weather_code"][i])
            date_label = res["daily"]["time"][i][8:] # 日にちだけ
            max_t = res["daily"]["temperature_2m_max"][i]
            prob = res["daily"]["precipitation_probability_max"][i]
            
            # デザインされたボタン
            if st.button(f"{date_label}\n{icon}\n{max_t}°\n{prob}%", key=f"week_{i}"):
                st.session_state.selected_day = i
                st.rerun()

else:
    # 設定画面 (前回の内容を維持)
    st.markdown("### ⚙️ 詳細設定")
    st.session_state.loc = st.selectbox("地域を選択", list(LOCS.keys()), index=list(LOCS.keys()).index(st.session_state.loc))
    st.session_state.threshold = st.slider("通知を出す降水確率(%)", 0, 100, st.session_state.threshold)
    st.write("---")
    st.session_state.time_morning = st.time_input("朝のチェック", st.session_state.time_morning)
    st.session_state.time_lunch = st.time_input("昼のチェック", st.session_state.time_lunch)
    st.session_state.time_evening = st.time_input("晩のチェック", st.session_state.time_evening)
    st.session_state.vibrate = st.toggle("振動を有効にする", st.session_state.vibrate)
