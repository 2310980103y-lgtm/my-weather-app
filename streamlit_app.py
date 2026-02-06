import streamlit as st
import datetime as dt
import requests
import plotly.graph_objects as go

# --- 1. アプリ設定 (PWA/スマホ対応) ---
st.set_page_config(
    page_title="RainCall+",
    page_icon="☔",
    layout="centered"
)

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

# --- 4. アラートロジック (降水確率チェック) ---
h_list = [st.session_state.time_morning.hour, st.session_state.time_lunch.hour, st.session_state.time_evening.hour]
probs_to_check = [res["hourly"]["precipitation_probability"][i] for i in h_list]
max_prob = max(probs_to_check)
alert_active = st.session_state.selected_day == 0 and max_prob >= st.session_state.threshold and not st.session_state.complete and st.session_state.vibrate

# 振動JS
vibrate_script = """
<script>
const vib = () => { if ("vibrate" in navigator) { navigator.vibrate([500, 200, 500]); } };
const interval = setInterval(vib, 2000);
</script>
""" if alert_active else ""

# --- 5. デザイン (背景切り替え機能維持) ---
if w_code >= 51: # 雨
    bg = "https://images.unsplash.com/photo-1428592953211-077101b2021b?q=80&w=2000"
elif 1 <= w_code <= 48: # 曇り
    bg = "https://images.unsplash.com/photo-1499346030926-9a72daac6c63?q=80&w=2000"
else: # 晴れ
    bg = "https://images.unsplash.com/photo-1544933863-482c6cdcd5d1?q=80&w=2000"

st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{ 
        background: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url("{bg}&sig={st.session_state.selected_day}"); 
        background-size: cover; background-position: center; 
    }}
    .main .block-container {{ 
        background: rgba(10, 15, 20, 0.85); border-radius: 20px; padding: 1.5rem; color: white; 
        backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1); margin-top: 1rem; 
    }}
    [data-testid="stMetricValue"] {{ color: #40E0D0 !important; font-weight: 900 !important; }}
</style>
<head>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
</head>
{vibrate_script}
""", unsafe_allow_html=True)

# --- 6. UI表示 ---
page = st.sidebar.radio("Menu", ["🏠 ホーム", "⚙️ 設定"])

if page == "🏠 ホーム":
    st.markdown(f"<h2 style='text-align:center; margin:0;'>RainCall+</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#40E0D0; font-weight:bold;'>📍 {st.session_state.loc} / {res['daily']['time'][st.session_state.selected_day][5:].replace('-','/')}</p>", unsafe_allow_html=True)

    if st.session_state.selected_day == 0:
        st.markdown(f"<div style='text-align:center; background:rgba(255,255,255,0.05); border-radius:15px; padding:10px; border:1px solid rgba(64,224,208,0.3);'><p style='margin:0; opacity:0.7;'>NOW</p><h1 style='color:#40E0D0; margin:0;'>{current_temp}°</h1></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("最高", f"{res['daily']['temperature_2m_max'][st.session_state.selected_day]}°")
    c2.metric("雨率", f"{res['daily']['precipitation_probability_max'][st.session_state.selected_day]}%")
    c3.metric("最低", f"{res['daily']['temperature_2m_min'][st.session_state.selected_day]}°")

    if alert_active:
        st.error(f"⚠️ 傘が必要です！")
        if st.button("✅ 準備完了（アラート停止）"):
            st.session_state.complete = True
            st.rerun()

    # グラフ推移
    h_idx = st.session_state.selected_day * 24
    fig = go.Figure(go.Scatter(x=[f"{i}h" for i in range(24)], y=res["hourly"]["precipitation_probability"][h_idx:h_idx+24], fill='tozeroy', line=dict(color='#40E0D0')))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=180, font=dict(color="white"), margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig, use_container_width=True)

    # 週間ボタン
    cols = st.columns(7)
    for i in range(7):
        d_str = res["daily"]["time"][i][5:].replace('-','/')
        if cols[i].button(f"{d_str}", key=f"d{i}"):
            st.session_state.selected_day = i
            st.rerun()

else:
    st.markdown("### ⚙️ 設定")
    st.session_state.loc = st.selectbox("地域", list(LOCS.keys()))
    st.session_state.threshold = st.slider("しきい値(%)", 0, 100, st.session_state.threshold)
    st.session_state.vibrate = st.toggle("振動通知", st.session_state.vibrate)
    if st.button("設定をリセット"):
        st.session_state.complete = False
        st.rerun()
