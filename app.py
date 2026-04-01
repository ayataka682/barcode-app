import streamlit as st
import streamlit.components.v1 as components
import datetime
import pandas as pd
import time
import base64
import os

st.set_page_config(page_title="バーコード照合アプリ", layout="wide")

# ====================================================
# ★ CSSで画面幅を100%限界まで使い切る超拡張設定
# ====================================================
st.markdown("""<style>
    /* 画面左右の余白を極限まで削り、横幅100%を強制 */
    .main .block-container { 
        padding-top: 1rem; 
        padding-bottom: 1rem; 
        padding-left: 2%; 
        padding-right: 2%; 
        max-width: 100% !important; 
    }
    /* Streamlitの標準ボタンをすべて巨大化＆太字に */
    .stButton > button {
        font-size: 20px !important;
        font-weight: 900 !important;
        padding: 15px !important;
        border-radius: 12px !important;
    }
    /* テキスト入力欄の文字も大きく */
    .stTextInput > div > div > input {
        font-size: 24px !important;
        font-weight: bold !important;
        padding: 10px !important;
    }
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
            <h1 style="margin:0; font-size:42px; color:#d9363e; font-weight:900;">⚠️ 【重要】13時を過ぎました ⚠️</h1>
            <p style="margin-top:15px; font-size:26px; color:#333; font-weight:bold;">午後の作業を開始する前に、必ず日次データをダウンロードしてください。</p>
            <p style="margin-top:5px; font-size:18px; color:#666;">※データをダウンロードすると、対象の履歴はアプリ内から消去されロックが解除されます。</p>
        </div>
        """, unsafe_allow_html=True
    )
    
    col_dl1, col_dl2, col_dl3 = st.columns([1, 4, 1]) # ボタンの横幅も広げる
    with col_dl2:
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

    # ★ 変更：パネルをさらに巨大化・フォントサイズMAX・横幅100%
    st.markdown(
        f"""
        <div style="display: flex; flex-wrap: wrap; gap: 30px; margin-bottom:30px; width: 100%;">
            <div style="flex: 1; min-width: 350px; background-color:#e6f7ff; border:4px solid #1890ff; padding:30px; border-radius:15px; text-align:center; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <p style="margin:0; font-size:24px; color:#0050b3; font-weight:bold;">🎯 現在の参照先（チューブマーク）</p>
                <p style="margin:10px 0; font-size:64px; font-weight:900; color:#002c8c; letter-spacing: 4px;">{st.session_state.reference_code}</p>
                <p style="margin:0; font-size:48px; font-weight:900; color:#d9363e;">【 {mark_text} 】</p>
            </div>
            <div style="flex: 1; min-width: 350px; background-color:#f6ffed; border:4px solid #52c41a; padding:30px; border-radius:15px; text-align:center; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <p style="margin:0; font-size:24px; color:#389e0d; font-weight:bold;">📊 現在の進捗（OK数 / 目標数）</p>
                <p style="margin:15px 0 0 0; font-weight:900; color:#237804; display: flex; align-items: baseline; justify-content: center; gap: 10px;">
                    <span style="font-size:100px; color:#52c41a; line-height:0.8;">{st.session_state.scanned_count}</span> 
                    <span style="font-size:48px;">/ {max_count}</span>
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

# --- 目標達成した場合の特大表示 ---
if st.session_state.reference_code and st.session_state.scanned_count >= max_count:
    if st.session_state.cycle_has_ng:
        st.markdown(
            """
            <div style="background-color:#fff3cd; border:5px solid #ffc107; padding:40px; border-radius:15px; text-align:center; margin-bottom:30px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);">
                <p style="margin:0; font-size:48px; font-weight:900; color:#856404;">⚠️ 照合完了（※要確認） ⚠️</p>
                <p style="margin-top:15px; font-size:28px; color:#856404; font-weight:bold;">作業中にNGが発生しました。表から履歴を確認してください。</p>
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
                <p style="margin:0; font-size:56px; font-weight:900; color:#155724;">✨ 照合完了（完全一致） ✨</p>
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
        if st.session_state.last_scan_ng:
            st.error(f"❌ NG! 一致しませんでした。（読込: {st.session_state.ng_text}）\n\nもう一度、正しいバーコードを読み込んでください。")
            if st.session_state.play_voice:
                play_error_wav_file()
                st.session_state.play_voice = False
                
        elif st.session_state.last_scan_ok:
            st.success(f"⭕ OK! 一致しました。（読込: {st.session_state.ok_text}）")
            
        else:
            st.info(f"💡 【2】 {st.session_state.scanned_count + 1}個目の照合先を読み込んでください")

    st.markdown("<p style='font-size:20px; font-weight:bold; color:#333; margin-bottom:0;'>▼ ここにカーソルがある状態で読み込んでください</p>", unsafe_allow_html=True)
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
    st.markdown("<h3 style='font-size:28px; font-weight:bold;'>📋 照合履歴（現在のセッション・最新が上）</h3>", unsafe_allow_html=True)
    
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
st.markdown("<h3 style='font-size:28px; font-weight:bold;'>📦 過去の全データ 強制バックアップ</h3>", unsafe_allow_html=True)

if os.path.exists(master_file):
    df_master_all = pd.read_csv(master_file, encoding="utf-8-sig")
    csv_master_all = df_master_all.to_csv(index=False).encode('utf-8-sig')
    
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
