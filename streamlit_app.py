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
    try:
        requests.post(url, json=payload, headers=headers, timeout=5)
    except:
        pass

# --- 1. アプリ設定とデータ取得 ---
st.set_page_config(page_title="RainCall+", page_icon="☔", layout="centered")

LOCS = {
    "広島": {"lat": 34.38, "lon": 132.45}, "東京": {"lat": 35.68, "lon": 139.69},
    "札幌": {"lat": 43.06, "lon": 141.34}, "大阪": {"lat": 34.69, "lon": 135.5},
    "福岡": {"lat": 33.59, "lon": 130.4}, "那覇": {"lat": 26.21, "lon": 127.68}
}

# --- 【★ここをあなたの好みに書き換えて保存してください★】 ---
if "loc" not in st.session_state: 
    st.session_state.loc = "広島"  # デフォルトの地域

if "threshold" not in st.session_state: 
    st.session_state.threshold = 0  # デフォルトのしきい値（0ならいつでも通知が来る）

if "time_morning" not in st.session_state: 
    st.session_state.time_morning = dt.time(7, 0)  # 朝のチェック時間

if "time_lunch" not in st.session_state: 
    st.session_state.time_lunch = dt.time(12, 0) # 昼のチェック時間

if "time_evening" not in st.session_state: 
    st.session_state.time_evening = dt.time(18, 0) # 晩のチェック時間

# 共通で使用するセッション変数
if "selected_day" not in st.session_state: st.session_state.selected_day = 0
if "history" not in st.session_state:
    st.session_state.history = {"朝": False, "昼": False, "晩": False}

# APIデータ取得
c = LOCS[st.session_state.loc]
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
menu = st.sidebar.radio("メニュー", ["🏠 ホーム", "⚙️ 設定"])

if menu == "🏠 ホーム":
    st.markdown("<h2 style='text-align:center;'>RainCall+</h2>", unsafe_allow_html=True)

    # 通知ロジック
    now = dt.datetime.now().time()
    max_p_today = res["daily"]["precipitation_probability_max"][0]

    if max_p_today >= st.session_state.threshold:
        schedule = [("朝", st.session_state.time_morning), ("昼", st.session_state.time_lunch), ("晩", st.session_state.time_evening)]
        passed = [(label, t) for label, t in schedule if now >= t]
        if passed:
            # 直近の時間帯を1つ選んで送信（重複防止）
            label, target_time = max(passed, key=lambda x: x[1])
            if not st.session_state.history[label]:
                send_line_notification(max_p_today, st.session_state.loc, label)
                st.session_state.history[label] = True
                st.success(f"✅ {label}の通知を送信しました。")

    idx = st.session_state.selected_day
    st.write(f"📅 **{res['daily']['time'][idx]} ({st.session_state.loc})**")
    c1, c2, c3 = st.columns(3)
    c1.metric("最高気温", f"{res['daily']['temperature_2m_max'][idx]}°")
    c2.metric("降水確率", f"{res['daily']['precipitation_probability_max'][idx]}%")
    c3.metric("最低気温", f"{res['daily']['temperature_2m_min'][idx]}°")

    st.write("📈 降水確率の推移")
    h_idx = idx * 24
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[f"{i}h" for i in range(24)], y=res["hourly"]["precipitation_probability"][h_idx:h_idx+24], line=dict(color='#40E0D0', width=3), fill='tozeroy'))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=180, font=dict(color="white"), margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.write("📅 週間予報 (タップで詳細表示)")
    week_cols = st.columns(7)
    for i in range(7):
        with week_cols[i]:
            day = res["daily"]["time"][i][8:]
            icon = get_icon(res["daily"]["weather_code"][i])
            if st.button(f"{day}日\n{icon}\n{res['daily']['temperature_2m_max'][i]}°\n{res['daily']['precipitation_probability_max'][i]}%", key=f"w{i}"):
                st.session_state.selected_day = i
                st.rerun()
else:
    st.markdown("### ⚙️ アプリ詳細設定")
    st.session_state.loc = st.selectbox("予報地域", list(LOCS.keys()), index=list(LOCS.keys()).index(st.session_state.loc))
    st.session_state.threshold = st.slider("通知を出す降水確率しきい値(%)", 0, 100, st.session_state.threshold)
    st.write("---")
    st.write("🔔 **定期通知の時刻設定**")
    st.session_state.time_morning = st.time_input("朝の通知時刻", st.session_state.time_morning)
    st.session_state.time_lunch = st.time_input("昼の通知時刻", st.session_state.time_lunch)
    st.session_state.time_evening = st.time_input("晩の通知時刻", st.session_state.time_evening)
    if st.button("通知履歴のリセット"):
        st.session_state.history = {"朝": False, "昼": False, "晩": False}
        st.success("通知履歴をリセットしました。")
