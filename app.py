import streamlit as st
import streamlit.components.v1 as components
import datetime
import pandas as pd
import time
import base64
import os

# レイアウトはwideのまま、CSSで最大幅をコントロールします
st.set_page_config(page_title="バーコード照合アプリ", layout="centered")

# ====================================================
# ★ CSSで画面幅のバランスと文字サイズを強制最適化
# ====================================================
st.markdown("""<style>
    /* 1. 画面幅の確実な調整（標準の狭い幅を、ちょうどいい1100pxまで広げる） */
    .block-container { 
        max-width: 1100px !important; 
        padding-top: 2rem !important; 
        padding-bottom: 2rem !important; 
    }
    
    /* 2. アプリ全体の標準テキストを約1.5倍（24px）に巨大化 */
    div[data-testid="stMarkdownContainer"] > p {
        font-size: 24px !important;
    }
    
    /* 見出しも合わせて大きく */
    h1 { font-size: 48px !important; }
    h3 { font-size: 32px !important; }

    /* Streamlitの標準ボタンを巨大化 */
    .stButton > button {
        font-size: 24px !important; 
        font-weight: 900 !important;
        padding: 15px !important;
        border-radius: 12px !important;
    }

    /* 3. アラート（情報・エラー等の帯）の文字を1.5倍大きく */
    div[data-testid="stAlert"] {
        padding: 20px !important;
        border-radius: 10px !important;
    }
    div[data-testid="stAlert"] div[data-testid="stMarkdownContainer"] > p {
        font-size: 26px !important;
        font-weight: bold !important;
        line-height: 1.5 !important;
    }

    /* 4. データフレーム（照合履歴の表）の文字を大きく */
    div[data-testid="stDataFrame"] {
        font-size: 20px !important;
    }

    /* ================================================= */
    /* ★ 修正：入力BOXの白と灰色の2色問題を解決！ */
    /* ================================================= */
    div[data-baseweb="input"], 
    div[data-baseweb="base-input"] {
        background-color: #f0f2f6 !important; 
        border-radius: 10px !important;
        border: none !important;
    }
    input[type="text"], input[type="number"] {
        background-color: transparent !important;
        border: none !important;
    }
    input[type="text"] {
        font-size: 32px !important;
        font-weight: bold !important;
        padding: 15px !important;
        height: 75px !important;
    }
    input[type="number"] {
        font-size: 48px !important;
        font-weight: 900 !important;
        text-align: center !important;
        height: 75px !important;
        color: #0050b3 !important;
    }
    div[data-baseweb="input"] button {
        width: 3.5rem !important;
        background-color: #f0f2f6 !important;
    }

    /* ================================================= */
    /* ★ 修正：特大パネルの文字が縮まないようにする専用CSS */
    /* ================================================= */
    .panel-title-blue { font-size: 32px !important; color: #0050b3; font-weight: bold; margin: 0; }
    .panel-val-blue { font-size: 100px !important; font-weight: 900; color: #002c8c; letter-spacing: 4px; line-height: 1.2; margin: 10px 0; }
    .panel-sub-blue { font-size: 64px !important; font-weight: 900; color: #d9363e; line-height: 1.2; margin: 0; }
    
    .panel-title-green { font-size: 32px !important; color: #389e0d; font-weight: bold; margin: 0; }
    .panel-val-green { font-size: 150px !important; color: #52c41a; line-height: 0.8; }
    .panel-sub-green { font-size: 72px !important; }
    .panel-val-wrapper { font-weight: 900; color: #237804; display: flex; align-items: baseline; justify-content: center; gap: 10px; margin: 15px 0 0 0; }

    .result-title { font-size: 100px !important; margin: 0; font-weight: 900; line-height: 1.2; }
    .result-val { font-size: 48px !important; margin: 25px 0; font-weight: bold; }
    .result-sub { font-size: 36px !important; margin: 0; font-weight: bold; }

</style>""", unsafe_allow_html=True)

st.title("📦 バーコード照合アプリ")

# いただいた実データ
master_data = {
    "0201": "Ａ", "0202": "Ｂ", "0203": "蝶", "0204": "チューリップ",
    "0205": "鉛筆", "0206": "クジラ", "0207": "飛行機", "0208": "リ",
    "0209": "足跡", "0210": "＃", "0211": "★", "0212": "３３３",
    "0213": "トンボ", "0214": "魚", "0215": "ウサギ", "0216": "電話",
    "0217": "ハサミ", "0218": "サッカーボール", "0219": "チョキ", "0220": "ピストル",
    "0221": "音符", "0222": "ペンギン", "0223": "セミ", "0224": "車",
    "0225": "かたつむり", "0226": "テルテル坊主", "0227": "ハート", "0228": "牛",
    "0229": "かさ", "0230": "（二重丸）", "0231": "日の丸（ハタ）", "0232": "ト音記号",
    "0233": "温泉", "0234": "へび", "0235": "バナナ", "0236": "〒（郵便マーク）",
    "0237": "ヘリコプター", "0238": "新幹線", "0239": "家", "0240": "自転車"
}

# ====================================================
# ★ コールバック関数群
# ====================================================
def clear_session_state():
    st.session_state.reference_code = ""
    st.session_state.group_id = ""
    st.session_state.scanned_count = 0
    st.session_state.last_scan_ng = False
    st.session_state.last_scan_ok = False
    st.session_state.play_voice = False
    st.session_state.cycle_has_ng = False 
    st.session_state.play_completion_warning = False
    st.session_state.scan_history = []
    st.session_state.scan_input = ""

def handle_download_1300(target_date_str, df_remaining, master_file, status_file):
    with open(status_file, "w", encoding="utf-8") as f:
        f.write(target_date_str)
    if df_remaining.empty:
        if os.path.exists(master_file):
            os.remove(master_file)
    else:
        df_remaining.to_csv(master_file, index=False, encoding="utf-8-sig")
    clear_session_state()

def handle_no_data(target_date_str, status_file):
    with open(status_file, "w", encoding="utf-8") as f:
        f.write(target_date_str)
    clear_session_state()

def handle_download_all(master_file):
    if os.path.exists(master_file):
        os.remove(master_file)
    clear_session_state()

# ====================================================
# ★ 13時締めの時刻計算とダウンロード判定
# ====================================================
now = datetime.datetime.now()
jst_now = now + datetime.timedelta(hours=9)

if jst_now.hour >= 13:
    end_thresh = jst_now.replace(hour=13, minute=0, second=0, microsecond=0)
    start_thresh = end_thresh - datetime.timedelta(days=1)
    target_date_str = jst_now.strftime("%Y%m%d") 
else:
    end_thresh = (jst_now - datetime.timedelta(days=1)).replace(hour=13, minute=0, second=0, microsecond=0)
    start_thresh = end_thresh - datetime.timedelta(days=1)
    target_date_str = (jst_now - datetime.timedelta(days=1)).strftime("%Y%m%d") 

status_file = "last_download_status.txt"
last_download = ""
if os.path.exists(status_file):
    with open(status_file, "r", encoding="utf-8") as f:
        last_download = f.read().strip()

needs_download = (last_download != target_date_str)

master_file = "scan_master_history.csv"
has_daily_data = False
csv_daily = b""
df_remaining = pd.DataFrame()

if os.path.exists(master_file):
    df_m = pd.read_csv(master_file, encoding="utf-8-sig")
    df_m['時刻(DT)'] = pd.to_datetime(df_m['時刻'], errors='coerce')
    
    mask = (df_m['時刻(DT)'] > start_thresh) & (df_m['時刻(DT)'] <= end_thresh)
    df_daily = df_m[mask].drop(columns=['時刻(DT)'])
    df_remaining = df_m[~mask].drop(columns=['時刻(DT)'])
    
    if not df_daily.empty:
        has_daily_data = True
        csv_daily = df_daily.to_csv(index=False).encode('utf-8-sig')

# ====================================================
# ★ ダウンロード強制アラート画面
# ====================================================
if needs_download:
    st.markdown(
        """
        <div style="background-color:#ffe6e6; border:5px solid #ff4b4b; padding:30px; border-radius:15px; text-align:center; margin-bottom:30px; box-shadow: 0px 8px 15px rgba(0,0,0,0.2);">
            <h1 style="margin:0; font-size:42px; color:#d9363e; font-weight:900;">⚠️ 【重要】 ⚠️</h1>
            <p style="margin-top:15px; font-size:26px; color:#333; font-weight:bold;">午後の作業を開始する前に、必ず日次データをダウンロードしてください。</p>
            <p style="margin-top:5px; font-size:18px; color:#666;">※データをダウンロードすると、対象の履歴はアプリ内から消去されロックが解除されます。</p>
        </div>
        """, unsafe_allow_html=True
    )
    
    if has_daily_data:
        st.download_button(
            label=f"📥 ここをクリックして【{start_thresh.strftime('%m/%d 13:00')}〜{end_thresh.strftime('%m/%d 13:00')}】のデータを保存・消去",
            data=csv_daily,
            file_name=f"Daily_Export_{target_date_str}_1300.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary",
            on_click=handle_download_1300,
            args=(target_date_str, df_remaining, master_file, status_file)
        )
    else:
        st.button(
            "✅ 対象期間のデータなし（クリックしてロック解除・作業開始）", 
            use_container_width=True, 
            type="primary",
            on_click=handle_no_data,
            args=(target_date_str, status_file)
        )
    st.write("---")

# ====================================================
# 1. 初期状態の準備
# ====================================================
if 'reference_code' not in st.session_state:
    clear_session_state()

# 💡 目標個数もセッションで管理
if 'target_count' not in st.session_state:
    st.session_state.target_count = 30

def reset_cycle():
    st.session_state.reference_code = ""
    st.session_state.group_id = ""
    st.session_state.scanned_count = 0
    st.session_state.last_scan_ng = False
    st.session_state.last_scan_ok = False
    st.session_state.play_voice = False
    st.session_state.cycle_has_ng = False 
    st.session_state.play_completion_warning = False

def save_to_master_csv(log_entry):
    df = pd.DataFrame([log_entry])
    if not os.path.exists(master_file):
        df.to_csv(master_file, index=False, encoding="utf-8-sig")
    else:
        df.to_csv(master_file, mode='a', header=False, index=False, encoding="utf-8-sig")

# ====================================================
# 2. 音声ファイルを読み込んで再生する仕組み
# ====================================================
def play_error_wav_file():
    WAV_FILE = "ng_voice.wav.wav"
    if not os.path.exists(WAV_FILE):
        st.error(f"音声ファイル {WAV_FILE} が見つかりません。")
        return
    with open(WAV_FILE, "rb") as f:
        audio_bytes = f.read()
    encoded_audio = base64.b64encode(audio_bytes).decode()
    components.html(
        f"""
        <audio autoplay="autoplay" style="display:none;" timestamp="{time.time()}">
            <source src="data:audio/wav;base64,{encoded_audio}" type="audio/wav">
        </audio>
        """, height=0
    )

def play_completion_warning_wav_file():
    WAV_FILE = "warning_voice.wav" 
    if not os.path.exists(WAV_FILE):
        st.error(f"音声ファイル {WAV_FILE} が見つかりません。")
        return
    with open(WAV_FILE, "rb") as f:
        audio_bytes = f.read()
    encoded_audio = base64.b64encode(audio_bytes).decode()
    components.html(
        f"""
        <audio autoplay="autoplay" style="display:none;" timestamp="{time.time()}">
            <source src="data:audio/wav;base64,{encoded_audio}" type="audio/wav">
        </audio>
        """, height=0
    )

# ====================================================
# 3. 読み込まれた瞬間に動く自動処理
# ====================================================
def process_scan():
    scanned_text = st.session_state.scan_input
    if not scanned_text:
        return

    now = datetime.datetime.now()
    jst_now = now + datetime.timedelta(hours=9) 
    time_str = jst_now.strftime("%Y-%m-%d %H:%M:%S") 

    if not st.session_state.reference_code:
        st.session_state.reference_code = scanned_text
        st.session_state.group_id = f"SET-{jst_now.strftime('%Y%m%d-%H%M%S')}"
        st.session_state.scan_input = ""
        st.session_state.last_scan_ng = False
        st.session_state.last_scan_ok = False
        return

    ref_mark_name = master_data.get(st.session_state.reference_code, "（登録なし）")
    scanned_mark_name = master_data.get(scanned_text, "（登録なし）")
    
    target_max = st.session_state.target_count # 設定された目標数

    if scanned_text == st.session_state.reference_code:
        st.session_state.scanned_count += 1
        st.session_state.last_scan_ng = False
        st.session_state.last_scan_ok = True
        st.session_state.ok_text = scanned_text
        
        log_entry = {
            "グループID": st.session_state.group_id,
            "目標数": target_max,
            "判定": "⭕ OK", 
            "参照先": f"{st.session_state.reference_code} ({ref_mark_name})",
            "読込内容": f"{scanned_text} ({scanned_mark_name})",
            "時刻": time_str
        }
        st.session_state.scan_history.insert(0, log_entry)
        save_to_master_csv(log_entry)
        
        if st.session_state.scanned_count >= target_max and st.session_state.cycle_has_ng:
            st.session_state.play_completion_warning = True

    else:
        st.session_state.last_scan_ng = True
        st.session_state.last_scan_ok = False
        st.session_state.play_voice = True
        st.session_state.ng_text = scanned_text
        st.session_state.cycle_has_ng = True 
        
        log_entry = {
            "グループID": st.session_state.group_id,
            "目標数": target_max,
            "判定": "❌ NG", 
            "参照先": f"{st.session_state.reference_code} ({ref_mark_name})",
            "読込内容": f"{scanned_text} ({scanned_mark_name})",
            "時刻": time_str
        }
        st.session_state.scan_history.insert(0, log_entry)
        save_to_master_csv(log_entry)
        
    st.session_state.scan_input = ""

# ====================================================
# 4. 画面の表示部分
# ====================================================
is_working = (st.session_state.reference_code != "")

# --- 参照先と進捗の特大パネル ---
if is_working:
    mark_text = master_data.get(st.session_state.reference_code, "（登録なし）")
    # ★修正：CSSクラスを使って、絶対に文字が縮まないように保護しました
    st.markdown(
        f"""
        <div style="display: flex; flex-wrap: wrap; gap: 30px; margin-bottom:30px; width: 100%;">
            <div style="flex: 1; min-width: 350px; background-color:#e6f7ff; border:4px solid #1890ff; padding:30px; border-radius:15px; text-align:center; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <div class="panel-title-blue">🎯 現在の参照先（チューブマーク）</div>
                <div class="panel-val-blue">{st.session_state.reference_code}</div>
                <div class="panel-sub-blue">【 {mark_text} 】</div>
            </div>
            <div style="flex: 1; min-width: 350px; background-color:#f6ffed; border:4px solid #52c41a; padding:30px; border-radius:15px; text-align:center; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <div class="panel-title-green">📊 現在の進捗（OK数 / 目標数）</div>
                <div class="panel-val-wrapper">
                    <div class="panel-val-green">{st.session_state.scanned_count}</div> 
                    <div class="panel-sub-green">/ {st.session_state.target_count}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

# --- 目標達成した場合の特大表示 ---
if is_working and st.session_state.scanned_count >= st.session_state.target_count:
    if st.session_state.cycle_has_ng:
        st.markdown(
            """
            <div style="background-color:#fff3cd; border:5px solid #ffc107; padding:40px; border-radius:15px; text-align:center; margin-bottom:30px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);">
                <div style="margin:0; font-size:48px !important; font-weight:900; color:#856404;">⚠️ 照合完了（※要確認） ⚠️</div>
                <div style="margin-top:15px; font-size:28px !important; color:#856404; font-weight:bold;">作業中にNGが発生しました。表から履歴を確認してください。</div>
            </div>
            """, unsafe_allow_html=True
        )
        if st.session_state.play_completion_warning:
            play_completion_warning_wav_file()
            st.session_state.play_completion_warning = False
    else:
        st.markdown(
            """
            <div style="background-color:#d4edda; border:5px solid #28a745; padding:40px; border-radius:15px; text-align:center; margin-bottom:30px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);">
                <div style="margin:0; font-size:56px !important; font-weight:900; color:#155724;">✨ 照合完了（完全一致） ✨</div>
            </div>
            """, unsafe_allow_html=True
        )

    if st.button("次のセットへ進む", type="primary", use_container_width=True, disabled=needs_download):
        reset_cycle()
        st.rerun()

# --- 通常の読み込み待ち状態の場合 ---
else:
    if is_working:
        # ★修正：OK/NGの表示テキストもCSSクラスで保護しました
        if st.session_state.last_scan_ng:
            st.markdown(f"""
            <div style="background-color:#ff4b4b; color:white; padding:40px; border-radius:15px; text-align:center; margin-bottom:25px; box-shadow: 0 8px 16px rgba(255,75,75,0.4);">
                <div class="result-title">❌ NG! 不一致</div>
                <div class="result-val">読込内容: <span style="background-color: white; color: #ff4b4b; padding: 5px 20px; border-radius: 8px;">{st.session_state.ng_text}</span></div>
                <div class="result-sub">もう一度、正しいバーコードを読み込んでください</div>
            </div>
            """, unsafe_allow_html=True)
            if st.session_state.play_voice:
                play_error_wav_file()
                st.session_state.play_voice = False
                
        elif st.session_state.last_scan_ok:
            st.markdown(f"""
            <div style="background-color:#52c41a; color:white; padding:40px; border-radius:15px; text-align:center; margin-bottom:25px; box-shadow: 0 8px 16px rgba(82,196,26,0.4);">
                <div class="result-title">⭕ OK! 一致</div>
                <div class="result-val">読込内容: <span style="background-color: white; color: #52c41a; padding: 5px 20px; border-radius: 8px;">{st.session_state.ok_text}</span></div>
            </div>
            """, unsafe_allow_html=True)

    # ====================================================
    # ★ 入力エリア ＆ ステップガイドの統合
    # ====================================================
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
    
    col_lbl1, col_lbl2 = st.columns([1, 3])
    with col_lbl1:
        if needs_download:
            label_1 = "🔒 ロック中"
            color_1 = "#ff4b4b"
        elif not is_working:
            label_1 = "🔰 STEP 1：積載個数を確認"
            color_1 = "#0050b3"
        else:
            label_1 = "🎯 積載個数（作業中ロック）"
            color_1 = "#666666"

        st.markdown(f"<div style='font-size:24px !important; font-weight:bold; color:{color_1}; margin-bottom:5px; white-space: nowrap;'>{label_1}</div>", unsafe_allow_html=True)
        
    with col_lbl2:
        if needs_download:
            label_2 = "🔒 データをダウンロードするまで読み込みできません"
            color_2 = "#ff4b4b"
        elif not is_working:
            label_2 = "🔰 STEP 2：最初のバーコード(基準)をスキャン ▼"
            color_2 = "#0050b3"
        else:
            label_2 = f"🔰 STEP 3：次の照合用バーコードをスキャン（{st.session_state.scanned_count + 1}個目）▼"
            color_2 = "#237804"
            
        st.markdown(f"<div style='font-size:24px !important; font-weight:bold; color:{color_2}; margin-bottom:5px; white-space: nowrap;'>{label_2}</div>", unsafe_allow_html=True)

    col_inp1, col_inp2 = st.columns([1, 3])
    with col_inp1:
        def update_target():
            st.session_state.target_count = st.session_state.target_count_widget
            
        st.number_input(
            "", 
            min_value=1, 
            max_value=100, 
            value=st.session_state.target_count, 
            key="target_count_widget", 
            on_change=update_target,
            disabled=(needs_download or is_working), 
            label_visibility="collapsed"
        )
        
    with col_inp2:
        st.text_input("", key="scan_input", on_change=process_scan, disabled=needs_download, label_visibility="collapsed")
    
    if not needs_download:
        components.html(
            """
            <script>
            try {
                const doc = window.parent.document;
                let attempts = 0;
                const focusInterval = setInterval(function() {
                    var inputs = doc.querySelectorAll('input[type="text"]');
                    for (var i = 0; i < inputs.length; i++) {
                        if (!inputs[i].disabled) {
                            inputs[i].focus();
                            clearInterval(focusInterval);
                            return;
                        }
                    }
                    attempts++;
                    if (attempts > 20) clearInterval(focusInterval);
                }, 100);
            } catch (e) {
            }
            </script>
            """, height=0
        )

# --- 照合履歴の表示 ---
if st.session_state.scan_history:
    st.write("---")
    st.markdown("<h3>📋 照合履歴（現在のセッション・最新が上）</h3>", unsafe_allow_html=True)
    
    df_history = pd.DataFrame(st.session_state.scan_history)
    st.dataframe(df_history, use_container_width=True)

# ====================================================
# ★ 途中でやり直す（リセット）ボタン
# ====================================================
st.write("---")
if st.button("🔄 現在の台車を最初からやり直す", disabled=needs_download, use_container_width=True):
    reset_cycle()
    st.rerun()

# ====================================================
# ★ クラウド対応：全件ダウンロードメニュー
# ====================================================
st.write("---")
st.markdown("<h3>📦 過去のデータ 強制バックアップ</h3>", unsafe_allow_html=True)

if os.path.exists(master_file):
    df_master_all = pd.read_csv(master_file, encoding="utf-8-sig")
    csv_master_all = df_master_all.to_csv(index=False).encode('utf-8-sig')
    
    st.download_button(
        label="📦 【全履歴データ】をすべてダウンロードして消去",
        data=csv_master_all,
        file_name=f"All_History_Export_{jst_now.strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
        on_click=handle_download_all,
        args=(master_file,)
    )
else:
    st.info("まだ保存されたマスターデータがありません。（バーコードを読み込むと生成されます）")
