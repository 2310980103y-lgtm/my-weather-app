import streamlit as st
import datetime as dt
import requests
import plotly.graph_objects as go

# --- 1. 設定 & セッション保持 (全設定を完全維持) ---
LOCS = {"広島": {"lat": 34.38, "lon": 132.45}, "東京": {"lat": 35.68, "lon": 139.69}, "札幌": {"lat": 43.06, "lon": 141.34}, "大阪": {"lat": 34.69, "lon": 135.5}, "福岡": {"lat": 33.59, "lon": 130.4}, "那覇": {"lat": 26.21, "lon": 127.68}}
conf = {"loc": "広島", "threshold": 30, "vibrate": True, "complete": False, "selected_day": 0, "time_morning": dt.time(7,0), "time_lunch": dt.time(12,0), "time_evening": dt.time(18,0)}
for k, v in conf.items():
    if k not in st.session_state: st.session_state[k] = v

# --- 2. データ取得 (現在の気温 current_weather を追加) ---
c = LOCS[st.session_state.loc]
res = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={c['lat']}&longitude={c['lon']}&current=temperature_2m&hourly=precipitation_probability&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia/Tokyo").json()
w_code = res["daily"]["weather_code"][st.session_state.selected_day]
current_temp = res["current"]["temperature_2m"] # 現在の気温

# --- 3. アラートロジック (完了ボタン未押下なら鳴り続ける) ---
h_list = [st.session_state.time_morning.hour, st.session_state.time_lunch.hour, st.session_state.time_evening.hour]
max_prob = max([res["hourly"]["precipitation_probability"][i] for i in h_list])
alert_active = st.session_state.selected_day == 0 and max_prob >= st.session_state.threshold and not st.session_state.complete and st.session_state.vibrate

vibrate_script = """
<script>
const vib = () => { if ("vibrate" in navigator) { navigator.vibrate([500, 200, 500]); } };
const interval = setInterval(vib, 2000); // 2秒おきに鳴り続ける
</script>
""" if alert_active else ""

# --- 4. デザイン ---
if w_code >= 51: bg = "https://images.unsplash.com/photo-1428592953211-077101b2021b?q=80&w=2000"
elif 1 <= w_code <= 48: bg = "https://images.unsplash.com/photo-1499346030926-9a72daac6c63?q=80&w=2000"
else: bg = "https://images.unsplash.com/photo-1544933863-482c6cdcd5d1?q=80&w=2000"

st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{ background: linear-gradient(rgba(0,0,0,0.25), rgba(0,0,0,0.25)), url("{bg}&sig={st.session_state.selected_day}"); background-size: cover; background-position: center; }}
    .main .block-container {{ background: rgba(10, 15, 20, 0.9); border-radius: 20px; padding: 1.5rem; color: white; backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1); margin-top: 1rem; }}
    [data-testid="stMetricValue"] {{ color: #40E0D0 !important; font-weight: 900 !important; text-shadow: 0 0 10px rgba(64,224,208,0.4); }}
    .stButton>button {{ background: rgba(255,255,255,0.08); color: white !important; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); font-size: 0.75rem; padding: 5px; }}
    .current-temp-box {{ text-align: center; background: rgba(255,255,255,0.05); border-radius: 15px; padding: 5px; margin-bottom: 15px; border: 1px solid rgba(64,224,208,0.3); }}
</style>
{vibrate_script}
""", unsafe_allow_html=True)

# --- 5. UI本体 ---
page = st.sidebar.radio("Menu", ["🏠 ホーム", "⚙️ 設定"])

if page == "🏠 ホーム":
    st.markdown(f"<h2 style='text-align:center; margin:0;'>RainCall+</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#40E0D0; font-weight:bold; margin-bottom:10px;'>📍 {st.session_state.loc} / {res['daily']['time'][st.session_state.selected_day][5:].replace('-','/')}</p>", unsafe_allow_html=True)

    # 現在の気温 (今日を選択している時だけ表示)
    if st.session_state.selected_day == 0:
        st.markdown(f"<div class='current-temp-box'><p style='font-size:0.9rem; opacity:0.8; margin:0;'>現在の気温</p><h1 style='color:#40E0D0; margin:0; font-size:2.8rem;'>{current_temp}°</h1></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("最高", f"{res['daily']['temperature_2m_max'][st.session_state.selected_day]}°")
    c2.metric("雨率", f"{res['daily']['precipitation_probability_max'][st.session_state.selected_day]}%")
    c3.metric("最低", f"{res['daily']['temperature_2m_min'][st.session_state.selected_day]}°")

    # グラフ
    h_idx = st.session_state.selected_day * 24
    fig = go.Figure(go.Scatter(x=[f"{i}h" for i in range(24)], y=res["hourly"]["precipitation_probability"][h_idx:h_idx+24], mode='lines+markers', line=dict(color='#40E0D0', width=3), marker=dict(size=5, color='white'), fill='tozeroy', fillcolor='rgba(64,224,208,0.1)'))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=160, margin=dict(l=0,r=0,t=10,b=0), xaxis=dict(tickfont=dict(color='white', weight='bold'), dtick=6, showgrid=False), yaxis=dict(range=[0,105], showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='white')))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # アラート表示
    if alert_active:
        st.error(f"⚠️ 傘が必要です！ (最高 {max_prob}%)")
        if st.button("✅ 傘を持ちました（アラート停止）", use_container_width=True):
            st.session_state.complete = True; st.rerun()
    elif st.session_state.complete and st.session_state.selected_day == 0:
        st.success("😊 準備完了！いってらっしゃい")

    st.markdown("---")
    cols = st.columns(7)
    for i in range(7):
        d_str = res["daily"]["time"][i][5:].replace('-','/')
        icon = "☀️" if res["daily"]["weather_code"][i] == 0 else "☔" if res["daily"]["weather_code"][i] >= 51 else "☁️"
        t_max, t_min = res["daily"]["temperature_2m_max"][i], res["daily"]["temperature_2m_min"][i]
        if cols[i].button(f"{d_str}\n{icon}\n{t_max}°\n{t_min}°", key=f"d{i}"):
            st.session_state.selected_day = i; st.rerun()
else:
    st.markdown("### ⚙️ 設定")
    st.session_state.loc = st.selectbox("地域", list(LOCS.keys()))
    st.session_state.threshold = st.slider("しきい値(%)", 0, 100, st.session_state.threshold)
    st.session_state.vibrate = st.toggle("振動通知", st.session_state.vibrate)
    st.session_state.time_morning = st.time_input("朝", st.session_state.time_morning)
    st.session_state.time_lunch = st.time_input("昼", st.session_state.time_lunch)
    st.session_state.time_evening = st.time_input("夜", st.session_state.time_evening)