import streamlit as st
import streamlit.components.v1 as components
import datetime
import pandas as pd
import time
import base64
import os

st.title("バーコード照合アプリ")

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
# ★ コールバック関数群（ボタンを押した瞬間に裏で動く処理）
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
    # 1. ダウンロード完了（ロック解除）の記録
    with open(status_file, "w", encoding="utf-8") as f:
        f.write(target_date_str)
    
    # 2. マスターCSVの更新（ダウンロードした分だけを消去し、残りを上書き）
    if df_remaining.empty:
        if os.path.exists(master_file):
            os.remove(master_file)
    else:
        df_remaining.to_csv(master_file, index=False, encoding="utf-8-sig")
    
    # 3. 画面の履歴をリセットして綺麗にする
    clear_session_state()

def handle_no_data(target_date_str, status_file):
    with open(status_file, "w", encoding="utf-8") as f:
        f.write(target_date_str)
    clear_session_state()

def handle_download_all(master_file):
    # マスターCSVを完全に消去
    if os.path.exists(master_file):
        os.remove(master_file)
    # 画面の履歴をリセット
    clear_session_state()

# ====================================================
# ★ 13時締めの時刻計算とダウンロード判定
# ====================================================
now = datetime.datetime.now()
jst_now = now + datetime.timedelta(hours=9)

if jst_now.hour >= 13:
    end_thresh = jst_now.replace(hour=13, minute=0, second=0, microsecond=0)
    start_thresh = end_thresh - datetime.timedelta(days=1)
    target_date_str = jst_now.strftime("%Y%m%d") # 今日の13時締めID
else:
    end_thresh = (jst_now - datetime.timedelta(days=1)).replace(hour=13, minute=0, second=0, microsecond=0)
    start_thresh = end_thresh - datetime.timedelta(days=1)
    target_date_str = (jst_now - datetime.timedelta(days=1)).strftime("%Y%m%d") # 昨日の13時締めID

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
    
    # ダウンロード対象データと、それ以外の残すデータを分ける
    mask = (df_m['時刻(DT)'] > start_thresh) & (df_m['時刻(DT)'] <= end_thresh)
    df_daily = df_m[mask].drop(columns=['時刻(DT)'])
    df_remaining = df_m[~mask].drop(columns=['時刻(DT)']) # ダウンロードした分を除外した残り
    
    if not df_daily.empty:
        has_daily_data = True
        csv_daily = df_daily.to_csv(index=False).encode('utf-8-sig')

# ====================================================
# ★ ダウンロード強制アラート画面
# ====================================================
if needs_download:
    st.markdown(
        """
        <div style="background-color:#ffe6e6; border:5px solid #ff4b4b; padding:25px; border-radius:15px; text-align:center; margin-bottom:25px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);">
            <h1 style="margin:0; font-size:36px; color:#d9363e; font-weight:900;">⚠️ 【重要】13時を過ぎました ⚠️</h1>
            <p style="margin-top:15px; font-size:22px; color:#333; font-weight:bold;">午後の作業を開始する前に、必ず日次データをダウンロードしてください。</p>
            <p style="margin-top:5px; font-size:16px; color:#666;">※データをダウンロードすると、対象の履歴はアプリ内から消去されロックが解除されます。</p>
        </div>
        """, unsafe_allow_html=True
    )
    
    col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
    with col_dl2:
        if has_daily_data:
            # 💡 押された瞬間に on_click で裏側のデータ消去が走る
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

# 💡【変更点】現在のセットのみリセット（履歴は消さない）
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
max_count = st.number_input("照合する個数を設定してください（最大30）", min_value=1, max_value=30, value=5, disabled=needs_download)

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

    if scanned_text == st.session_state.reference_code:
        st.session_state.scanned_count += 1
        st.session_state.last_scan_ng = False
        st.session_state.last_scan_ok = True
        st.session_state.ok_text = scanned_text
        
        log_entry = {
            "グループID": st.session_state.group_id,
            "目標数": max_count,
            "判定": "⭕ OK", 
            "参照先": f"{st.session_state.reference_code} ({ref_mark_name})",
            "読込内容": f"{scanned_text} ({scanned_mark_name})",
            "時刻": time_str
        }
        st.session_state.scan_history.insert(0, log_entry)
        save_to_master_csv(log_entry)
        
        if st.session_state.scanned_count >= max_count and st.session_state.cycle_has_ng:
            st.session_state.play_completion_warning = True

    else:
        st.session_state.last_scan_ng = True
        st.session_state.last_scan_ok = False
        st.session_state.play_voice = True
        st.session_state.ng_text = scanned_text
        st.session_state.cycle_has_ng = True 
        
        log_entry = {
            "グループID": st.session_state.group_id,
            "目標数": max_count,
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
st.write("---")

if st.session_state.reference_code:
    mark_text = master_data.get(st.session_state.reference_code, "（登録なし）")

    st.markdown(
        f"""
        <div style="background-color:#e6f7ff; border:2px solid #1890ff; padding:20px; border-radius:10px; text-align:center; margin-bottom:20px;">
            <p style="margin:0; font-size:18px; color:#0050b3; font-weight:bold;">🎯 現在の参照先（チューブマーク）</p>
            <p style="margin:0; font-size:48px; font-weight:bold; color:#002c8c; letter-spacing: 2px;">{st.session_state.reference_code}</p>
            <p style="margin:15px 0 0 0; font-size:36px; font-weight:bold; color:#d9363e;">【 {mark_text} 】</p>
        </div>
        """, unsafe_allow_html=True
    )

# --- 目標達成した場合の特大表示 ---
if st.session_state.reference_code and st.session_state.scanned_count >= max_count:
    if st.session_state.cycle_has_ng:
        st.markdown(
            """
            <div style="background-color:#fff3cd; border:4px solid #ffc107; padding:30px; border-radius:15px; text-align:center; margin-bottom:20px;">
                <p style="margin:0; font-size:40px; font-weight:bold; color:#856404;">⚠️ 照合完了（※要確認） ⚠️</p>
                <p style="margin-top:10px; font-size:22px; color:#856404; font-weight:bold;">作業中にNGが発生しました。表から履歴を確認してください。</p>
            </div>
            """, unsafe_allow_html=True
        )
        if st.session_state.play_completion_warning:
            play_completion_warning_wav_file()
            st.session_state.play_completion_warning = False
    else:
        st.markdown(
            """
            <div style="background-color:#d4edda; border:4px solid #28a745; padding:30px; border-radius:15px; text-align:center; margin-bottom:20px;">
                <p style="margin:0; font-size:40px; font-weight:bold; color:#155724;">✨ 照合完了（完全一致） ✨</p>
            </div>
            """, unsafe_allow_html=True
        )

    if st.button("次のセットへ進む", type="primary", use_container_width=True, disabled=needs_download):
        reset_cycle()
        st.rerun()

# --- 通常の読み込み待ち状態の場合 ---
else:
    if not st.session_state.reference_code:
        if needs_download:
            st.warning("🔒 データをダウンロードするまで読み込みはできません")
        else:
            st.info("💡 【1】最初のバーコード（参照先）を読み込んでください")
    else:
        st.write(f"**現在の目標:** {st.session_state.scanned_count} / {max_count} 個完了")
        
        if st.session_state.last_scan_ng:
            st.error(f"❌ NG! 一致しませんでした。（読込: {st.session_state.ng_text}）\n\nもう一度、正しいバーコードを読み込んでください。")
            if st.session_state.play_voice:
                play_error_wav_file()
                st.session_state.play_voice = False
                
        elif st.session_state.last_scan_ok:
            st.success(f"⭕ OK! 一致しました。（読込: {st.session_state.ok_text}）")
            st.info(f"💡 【2】 {st.session_state.scanned_count + 1}個目の照合先を読み込んでください")
            
        else:
            st.info(f"💡 【2】 {st.session_state.scanned_count + 1}個目の照合先を読み込んでください")

    st.text_input("▼ ここにカーソルがある状態で読み込んでください", key="scan_input", on_change=process_scan, disabled=needs_download)
    
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
    st.write("### 📋 照合履歴（現在のセッション・最新が上）")
    
    df_history = pd.DataFrame(st.session_state.scan_history)
    st.dataframe(df_history, use_container_width=True)

# ====================================================
# ★ 途中でやり直す（リセット）ボタンを1つに統合
# ====================================================
st.write("---")
if st.button("🔄 現在のセットを最初からやり直す", disabled=needs_download, use_container_width=True):
    reset_cycle()
    st.rerun()


# ====================================================
# ★ クラウド対応：全件ダウンロードメニュー
# ====================================================
st.write("---")
st.write("### 📦 過去の全データ 強制バックアップ")

if os.path.exists(master_file):
    df_master_all = pd.read_csv(master_file, encoding="utf-8-sig")
    csv_master_all = df_master_all.to_csv(index=False).encode('utf-8-sig')
    
    # 💡 全データダウンロードでも消去処理を連動
    st.download_button(
        label="📦 アプリに溜まっている【全履歴データ】をすべてダウンロードして消去",
        data=csv_master_all,
        file_name=f"All_History_Export_{jst_now.strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
        on_click=handle_download_all,
        args=(master_file,)
    )
else:
    st.info("まだ保存されたマスターデータがありません。（バーコードを読み込むと生成されます）")
