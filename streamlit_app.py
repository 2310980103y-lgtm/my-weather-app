import streamlit as st
import datetime as dt
import requests
import plotly.graph_objects as go

# --- 1. アプリとしての基本設定 (PWA対応) ---
st.set_page_config(
    page_title="RainCall+",
    page_icon="☔",
    layout="centered"
)

# スマホの「アプリモード」を有効にするメタタグ
st.markdown("""
    <head>
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <link rel="manifest" href="/manifest.json">
    </head>
""", unsafe_allow_html=True)

# --- 2. 設定 & セッション保持 ---
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
    if k not in st.session_state:
        st.session_state[k] = v

# --- 3. データ取得 ---
c = LOCS[st.session_state.loc]
api_url = f"https://api.open-meteo.com/v1/forecast?latitude={c['lat']}&longitude={c['lon']}&current=temperature_2m&hourly=precipitation_probability&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia/Tokyo"
res = requests.get(api_url).json()

w_code = res["daily"]["weather_code"][st.session_state.selected_day]
current_temp = res["current"]["temperature_2m"]

# --- 4. アラートロジック ---
h_list = [st.session_state.time_morning.hour, st.session_state.time_lunch.hour, st.session_state.time_evening.hour]
probs = [res["hourly"]["precipitation_probability"][i] for i in h_list]
max_prob = max(probs)
alert_active = st.session_state.selected_day == 0 and max_prob >= st.session_state.threshold and not st.session_state.complete and st.session_state.vibrate

# 振動JS (一度画面を触ると発動)
vibrate_script = """
<script>
const vib = () => { if ("vibrate" in navigator) { navigator.vibrate([500, 200, 500]); } };
const interval = setInterval(vib, 2000);
</script>
""" if alert_active else ""

# --- 5. デザイン ---
st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{ 
        background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url("https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1000"); 
        background-size: cover; 
    }}
    .main .block-container {{ background: rgba(0,0,0,0.7); border-radius: 20px; color: white; backdrop-filter: blur(10px); }}
</style>
{vibrate_script}
""", unsafe_allow_html=True)

# --- 6. UI ---
st.title("☔ RainCall+")
if alert_active:
    st.error(f"⚠️ 雨の予報です！傘を忘れずに。")
    if st.button("✅ 準備完了（アラート停止）"):
        st.session_state.complete = True
        st.rerun()

st.metric("現在の気温", f"{current_temp}°")
st.write(f"📍 {st.session_state.loc} の予報")

# グラフ
fig = go.Figure(go.Scatter(x=[f"{i}h" for i in range(24)], y=res["hourly"]["precipitation_probability"][:24], fill='tozeroy'))
fig.update_layout(height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
st.plotly_chart(fig, use_container_width=True)
