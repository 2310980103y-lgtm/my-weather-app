import datetime as dt
import requests
import streamlit as st
import plotly.graph_objects as go

# --- 0. LINE通知設定 ---
LINE_ACCESS_TOKEN = "BPMnqthIbERoA/henksTFQtd4ROKB9tteKutj5OBluN0/szlOeIg9R6ktfANariIFI2E2NBbGVzChCs7xGpsFxbsiI3guxuE8SjBjtBkV2N+YHXwUTIeT1ovDvw4uzp1EzlTtz9WWpeiRz+JwfbZ0QdB04t89/1O/w1cDnyilFU="
LINE_USER_ID = "Uff099522ed83e1eb005f1103c8ac92eb"

def send_line_notification(prob, loc, timing_label):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": f"📢【RainCall+ {timing_label}通知】\n📍 {loc}\n☔ 降水確率: {prob}%\n傘の準備をしてください！"}]
    }
    try: requests.post(url, json=payload, headers=headers, timeout=5)
    except: pass

# --- 1. アプリ設定とデータ取得 ---
st.set_page_config(page_title="RainCall+", page_icon="☔", layout="centered")

LOCS = {
    "広島": {"lat": 34.38, "lon": 132.45}, "東京": {"lat": 35.68, "lon": 139.69},
    "札幌": {"lat": 43.06, "lon": 141.34}, "大阪": {"lat": 34.69, "lon": 135.5},
    "福岡": {"lat": 33.59, "lon": 130.4}, "那覇": {"lat": 26.21, "lon": 127.68}
}

if "loc" not in st.session_state: st.session_state.loc = "広島"
if "threshold" not in st.session_state: st.session_state.threshold = 30
if "selected_day" not in st.session_state: st.session_state.selected_day = 0
if "time_morning" not in st.session_state: st.session_state.time_morning = dt.time(7, 0)
if "time_lunch" not in st.session_state: st.session_state.time_lunch = dt.time(12, 0)
if "time_evening" not in st.session_state: st.session_state.time_evening = dt.time(18, 0)
if "history" not in st.session_state: st.session_state.history = {"朝": False, "昼": False, "晩": False}

c = LOCS[st.session_state.loc]
# 温度データ（temperature_2m_max, min）をしっかり取得
api_url = f"https://api.open-meteo.com/v1/forecast?latitude={c['lat']}&longitude={c['lon']}&hourly=precipitation_probability&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia/Tokyo"
res = requests.get(api_url).json()

def get_icon(code):
    if code == 0: return "☀️"
    if code <= 3: return "🌤️"
    if code <= 48: return "☁️"
    if code <= 67: return "☔"
    return "⚡"

# --- 2. 画面デザイン ---
w_code = res["daily"]["weather_code"][st.session_state.selected_day]
bg = "https://images.unsplash.com/photo-1544933863-482c6cdcd5d1?w=1000"
if w_code >= 51: bg = "https://images.unsplash.com/photo-1428592953211-077101b2021b?w=1000"
elif 1 <= w_code <= 48: bg = "https://images.unsplash.com/photo-1499346030926-9a72daac6c63?w=1000"

st.markdown(f"<style>[data-testid='stAppViewContainer'] {{ background: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('{bg}'); background-size: cover; }} .main .block-container {{ background: rgba(10, 15, 20, 0.85); border-radius: 20px; color: white; backdrop-filter: blur(15px); padding: 1.5rem; }}</style>", unsafe_allow_html=True)

# --- 3. メインUI ---
menu = st.sidebar.radio("Menu", ["🏠 ホーム", "⚙️ 設定"])

if menu == "🏠 ホーム":
    st.markdown("<h2 style='text-align:center;'>RainCall+</h2>", unsafe_allow_html=True)
    
    # スケジュール通知チェック
    now = dt.datetime.now().time()
    max_p_today = res["daily"]["precipitation_probability_max"][0]
    if max_p_today >= st.session_state.threshold:
        for label, t in [("朝", st.session_state.time_morning), ("昼", st.session_state.time_lunch), ("晩", st.session_state.time_evening)]:
            if now >= t and not st.session_state.history[label]:
                send_line_notification(max_p_today, st.session_state.loc, label)
                st.session_state.history[label] = True
                st.success(f"✅ {label}の通知を送信しました")

    # メイン予報表示
    idx = st.session_state.selected_day
    st.write(f"📅 **{res['daily']['time'][idx]} ({st.session_state.loc})**")
    c1, c2, c3 = st.columns(3)
    c1.metric("最高気温", f"{res['daily']['temperature_2m_max'][idx]}°", delta_color="normal")
    c2.metric("降水確率", f"{res['daily']['precipitation_probability_max'][idx]}%")
    c3.metric("最低気温", f"{res['daily']['temperature_2m_min'][idx]}°", delta_color="inverse")

    # 24時間グラフ
    st.write("📈 時間ごとの降水確率推移")
    h_idx = idx * 24
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[f"{i}h" for i in range(24)], y=res["hourly"]["precipitation_probability"][h_idx:h_idx+24], line=dict(color='#40E0D0', width=3), fill='tozeroy'))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=180, font=dict(color="white"), margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig, use_container_width=True)

    # 【進化！】1週間予報（温度と確率をすべて表示）
    st.write("📅 週間予報 (タップで詳細に切り替え)")
    # 1週間分の温度推移を見やすくするため、スクロール可能な列を作成
    week_cols = st.columns(7)
    for i in range(7):
        with week_cols[i]:
            day_label = res["daily"]["time"][i][8:] # 日付の「日」だけ抽出
            icon = get_icon(res["daily"]["weather_code"][i])
            t_max = res["daily"]["temperature_2m_max"][i]
            t_min = res["daily"]["temperature_2m_min"][i]
            p_max = res["daily"]["precipitation_probability_max"][i]
            
            # ボタンの中に情報を詰め込む
            button_text = f"{day_label}日\n{icon}\n{t_max}°\n{t_min}°\n{p_max}%"
            if st.button(button_text, key=f"w{i}"):
                st.session_state.selected_day = i
                st.rerun()

else:
    # 設定画面
    st.markdown("### ⚙️ アプリ設定")
    st.session_state.loc = st.selectbox("地域", list(LOCS.keys()))
    st.session_state.threshold = st.slider("通知しきい値(%)", 0, 100, st.session_state.threshold)
    st.write("---")
    st.write("🔔 **通知時間の設定**")
    st.session_state.time_morning = st.time_input("朝の通知", st.session_state.time_morning)
    st.session_state.time_lunch = st.time_input("昼の通知", st.session_state.time_lunch)
    st.session_state.time_evening = st.time_input("晩の通知", st.session_state.time_evening)
    
    if st.button("送信記録リセット"):
        st.session_state.history = {"朝": False, "昼": False, "晩": False}
        st.success("リセット完了")
