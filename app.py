import streamlit as st
import streamlit.components.v1 as components
import datetime
import pandas as pd
import time
import base64
import os

# レイアウトはwideのまま、CSSで最大幅をコントロールしま
st.set_page_config(page_title="バーコード照合アプリ", layout="centered")

# ====================================================
# ★ CSSで画面幅のバランスと文字サイズを強制最適化
# ====================================================
st.markdown("""<style>
    /* 1. 画面幅の確実な調整（標準の狭い幅を、ちょうどいい1100pxまで広げる */
    .block-container { 
        max-width: 1100px !important; 
        padding-top: 2rem !important; 
        padding-bottom: 2rem !important; 
    }
    
    /* 2. アプリ全体の標準テキストを約1.5倍（24px）に巨大化 */
    div[data-testid="stMarkdownContainer"] > p {
        font-size: 24px;
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

    /* 4. データフレーム/データエディタ（照合履歴の表）の文字を大きく */
    div[data-testid="stDataFrame"] {
        font-size: 20px !important;
    }

    /* ================================================= */
    /* ★ 入力BOXの白と灰色の2色問題を完全に解決！ */
    /* ================================================= */
    /* 外枠・内枠すべてを強制的に同じ灰色で塗りつぶす */
    div[data-baseweb="input"], 
    div[data-baseweb="base-input"],
    div[data-baseweb="select"] > div {
        background-color: #f0f2f6 !important; 
        border-radius: 10px !important;
        border: none !important;
    }
    
    /* 入力部分の背景も同じ灰色にする */
    input[type="text"], input[type="number"] {
        background-color: transparent !important;
        border: none !important;
    }

    /* ★ バーコード入力欄の文字を強制的に大きく */
    input[type="text"] {
        font-size: 32px !important;
        font-weight: bold !important;
        padding: 15px !important;
        height: 75px !important;
    }
    
    /* 🌟 新規：プルダウン（セレクトボックス）の文字と高さを強制的に特大化 */
    div[data-baseweb="select"] > div {
        min-height: 80px !important;
        font-size: 32px !important;
        font-weight: bold !important;
    }
    
    /* 🌟 新規：プルダウンを開いた時のリストの選択肢も特大化 */
    li[role="option"] {
        font-size: 28px !important;
        font-weight: bold !important;
        padding: 15px 20px !important;
    }

    /* ★ 目標個数（数字入力欄）の文字を強制的に「超特大」にする */
    input[type="number"] {
        font-size: 48px !important;
        font-weight: 900 !important;
        text-align: center !important;
        height: 75px !important;
        color: #0050b3 !important;
    }
    
    /* 目標個数のプラス・マイナスボタンも押しやすく大きくする */
    div[data-baseweb="input"] button {
        width: 3.5rem !important;
        background-color: #f0f2f6 !important; /* ボタン部分も色を合わせる */
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

# 🌟 プルダウンの選択肢（一元管理）
ACTION_OPTIONS = [
    "選択してください", 
    "該当品を除外（廃棄）して続行", 
    "正しいラベルに貼り替えて続行", 
    "責任者へ報告し保留", 
    "その他"
]

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
    if "ng_action_input" in st.session_state:
        st.session_state.ng_action_input = "選択してください"

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

# 新規追加：プルダウンで選んだ「処置」を保存する関数
def save_ng_action():
    action = st.session_state.get("ng_action_input", "選択してください")
    if action == "選択してください" or not st.session_state.scan_history:
        return

    # セッションの最新履歴を更新（直近がNGの場合のみ）
    latest_log = st.session_state.scan_history[0]
    if "NG" in latest_log["判定"]:
        latest_log["処置"] = action

        # CSVファイルの一番下の行（最新行）を書き換え
        master_file = "scan_master_history.csv"
        if os.path.exists(master_file):
            try:
                df = pd.read_csv(master_file, encoding="utf-8-sig")
                last_idx = df.index[-1]
                # 安全確認：グループIDと時刻が一致しているか確認してから上書き
                if df.at[last_idx, "グループID"] == latest_log["グループID"] and df.at[last_idx, "時刻"] == latest_log["時刻"]:
                    df.at[last_idx, "処置"] = action
                    df.to_csv(master_file, index=False, encoding="utf-8-sig")
            except Exception as e:
                pass

# 🌟 新規追加：データエディタ（履歴表）での直接編集を保存する関数
def update_history_from_editor():
    edited_rows = st.session_state.get("history_editor", {}).get("edited_rows", {})
    if not edited_rows:
        return
    
    master_file = "scan_master_history.csv"
    
    for idx, changes in edited_rows.items():
        if "処置" in changes:
            new_action = changes["処置"]
            # セッション上のデータを更新
            st.session_state.scan_history[idx]["処置"] = new_action
            
            # CSVの該当行も更新
            target_log = st.session_state.scan_history[idx]
            if os.path.exists(master_file):
                try:
                    df = pd.read_csv(master_file, encoding="utf-8-sig")
                    # グループIDと時刻の両方が一致する行を特定して上書き
                    match_idx = df[(df["グループID"] == target_log["グループID"]) & (df["時刻"] == target_log["時刻"])].index
                    if not match_idx.empty:
                        df.loc[match_idx, "処置"] = new_action
                        df.to_csv(master_file, index=False, encoding="utf-8-sig")
                except Exception as e:
                    pass

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

# 💡 目標個数もセッションで管理（デフォルトを30に変更）
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
    if "ng_action_input" in st.session_state:
        st.session_state.ng_action_input = "選択してください"

# 修正：過去のCSVに「処置」列が無くてもエラーにならないように結合処理を追加
def save_to_master_csv(log_entry):
    df_new = pd.DataFrame([log_entry])
    if not os.path.exists(master_file):
        df_new.to_csv(master_file, index=False, encoding="utf-8-sig")
    else:
        try:
            df_old = pd.read_csv(master_file, encoding="utf-8-sig")
            # 既存のCSVと新しいログを結合（旧CSVに処置列がなくても自動で作成される）
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
            if "処置" not in df_combined.columns:
                df_combined["処置"] = ""
            df_combined["処置"] = df_combined["処置"].fillna("")
            df_combined.to_csv(master_file, index=False, encoding="utf-8-sig")
        except Exception:
            # 万が一結合に失敗した場合は追記モードで退避
            df_new.to_csv(master_file, mode='a', header=False, index=False, encoding="utf-8-sig")

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
            "時刻": time_str,
            "処置": "" 
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
            "時刻": time_str,
            "処置": "" 
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
    st.markdown(
        f"""
        <div style="display: flex; flex-wrap: wrap; gap: 30px; margin-bottom:30px; width: 100%;">
            <div style="flex: 1; min-width: 350px; background-color:#e6f7ff; border:4px solid #1890ff; padding:30px; border-radius:15px; text-align:center; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <p style="margin:0; font-size:24px; color:#0050b3; font-weight:bold;">🎯 現在の参照先（チューブマーク）</p>
                <p style="margin:10px 0; font-size:80px; font-weight:900; color:#002c8c; letter-spacing: 4px; line-height: 1.2;">{st.session_state.reference_code}</p>
                <p style="margin:0; font-size:56px; font-weight:900; color:#d9363e; line-height: 1.2;">【 {mark_text} 】</p>
            </div>
            <div style="flex: 1; min-width: 350px; background-color:#f6ffed; border:4px solid #52c41a; padding:30px; border-radius:15px; text-align:center; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <p style="margin:0; font-size:24px; color:#389e0d; font-weight:bold;">📊 現在の進捗（OK数 / 目標数）</p>
                <div style="margin:15px 0 0 0; font-weight:900; color:#237804; display: flex; align-items: baseline; justify-content: center; gap: 10px;">
                    <span style="font-size:120px; color:#52c41a; line-height:0.8;">{st.session_state.scanned_count}</span> 
                    <span style="font-size:56px;">/ {st.session_state.target_count}</span>
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
                <p style="margin:0; font-size:48px; font-weight:900; color:#856404;">⚠️ 照合完了（※要確認） ⚠️</p>
                <p style="margin-top:15px; font-size:28px; color:#856404; font-weight:bold;">作業中に不一致が発生しました。表から履歴を確認してください。</p>
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
                <p style="margin:0; font-size:48px; font-weight:900; color:#155724;">✨ 照合完了（OK） ✨</p>
            </div>
            """, unsafe_allow_html=True
        )

    if st.button("次のセットへ進む", type="primary", use_container_width=True, disabled=needs_download):
        reset_cycle()
        st.rerun()

# --- 通常の読み込み待ち状態の場合 ---
else:
    if is_working:
        if st.session_state.last_scan_ng:
            st.markdown(f"""
            <div style="background-color:#ff4b4b; color:white; padding:30px; border-radius:15px; text-align:center; margin-bottom:15px; box-shadow: 0 8px 16px rgba(255,75,75,0.4);">
                <h2 style="font-size: 80px; margin: 0; font-weight: 900; line-height: 1.2;">❌ NG! 不一致</h2>
                <p style="font-size: 36px; margin: 15px 0; font-weight: bold;">読込内容: <span style="background-color: white; color: #ff4b4b; padding: 5px 20px; border-radius: 8px;">{st.session_state.ng_text}</span></p>
                <p style="font-size: 28px; margin: 0; font-weight: bold;">読み込み内容を確認してください</p>
            </div>
            """, unsafe_allow_html=True)
            if st.session_state.play_voice:
                play_error_wav_file()
                st.session_state.play_voice = False
                
            # プルダウン式の処置入力
            st.markdown("<p style='font-size:32px; font-weight:bold; color:#d9363e; margin-bottom:15px;'>📝 処置内容を選択してください</p>", unsafe_allow_html=True)
            
            st.selectbox(
                "処置", 
                options=ACTION_OPTIONS, 
                key="ng_action_input", 
                on_change=save_ng_action, 
                label_visibility="collapsed"
            )
            
            # 重なり防止：入力BOXの下に十分な余白を強制的に追加
            st.markdown("<div style='margin-bottom: 50px;'></div>", unsafe_allow_html=True)
            
            # 処置が保存されたら「保存しました」という表示を出す
            if st.session_state.scan_history:
                current_action = st.session_state.scan_history[0].get("処置", "")
                if current_action and current_action != "選択してください":
                    st.success(f"✅ 処置を記録しました: {current_action}")
                
        elif st.session_state.last_scan_ok:
            st.markdown(f"""
            <div style="background-color:#52c41a; color:white; padding:30px; border-radius:15px; text-align:center; margin-bottom:25px; box-shadow: 0 8px 16px rgba(82,196,26,0.4);">
                <h2 style="font-size: 80px; margin: 0; font-weight: 900; line-height: 1.2;">⭕ OK! 一致</h2>
                <p style="font-size: 36px; margin: 15px 0; font-weight: bold;">読込内容: <span style="background-color: white; color: #52c41a; padding: 5px 20px; border-radius: 8px;">{st.session_state.ok_text}</span></p>
            </div>
            """, unsafe_allow_html=True)

    # ====================================================
    # ★ 入力エリア ＆ ステップガイドの統合
    # ====================================================
    # 🌟 重なり防止：上の要素との間に大きな余白を取って全体を下へ押し下げる
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:10px 0 30px 0;'>", unsafe_allow_html=True)
    
    col_input1, col_input2 = st.columns([1, 3])
    
    with col_input1:
        if needs_download:
            label_1 = "🔒 ロック中"
            color_1 = "#ff4b4b"
        elif not is_working:
            label_1 = "🔰 STEP 1：積載個数を確認"
            color_1 = "#0050b3"
        else:
            label_1 = "🎯 積載個数（ロック中）"
            color_1 = "#666666"

        st.markdown(f"<p style='font-size:20px; font-weight:bold; color:{color_1}; margin-bottom:5px;'>{label_1}</p>", unsafe_allow_html=True)
        
        def update_target():
            st.session_state.target_count = st.session_state.target_count_widget
            
        st.number_input(
            "", 
            min_value=1, 
            max_value=30, 
            value=st.session_state.target_count, 
            key="target_count_widget", 
            on_change=update_target,
            disabled=(needs_download or is_working), 
            label_visibility="collapsed"
        )
        
    with col_input2:
        if needs_download:
            label_2 = "🔒 データをダウンロードするまで読み込みできません"
            color_2 = "#ff4b4b"
        elif not is_working:
            label_2 = "🔰 STEP 2：最初のバーコード(基準)をスキャン ▼"
            color_2 = "#0050b3"
        else:
            label_2 = f"🔰 STEP 3：次の照合用バーコードをスキャン（{st.session_state.scanned_count + 1}個目）▼"
            color_2 = "#237804"
            
        st.markdown(f"<p style='font-size:20px; font-weight:bold; color:{color_2}; margin-bottom:5px;'>{label_2}</p>", unsafe_allow_html=True)
        
        st.text_input("", key="scan_input", on_change=process_scan, disabled=needs_download, label_visibility="collapsed")
    
    if not needs_download:
        # 🌟 修正：常に「バーコードスキャンの枠（一番下）」にフォーカスを戻す
        components.html(
            """
            <script>
            try {
                const doc = window.parent.document;
                let attempts = 0;
                const focusInterval = setInterval(function() {
                    var inputs = doc.querySelectorAll('input[type="text"]');
                    // 確実にバーコードスキャンの入力枠（一番最後）を取得する
                    var targetInput = inputs[inputs.length - 1];
                    if (targetInput && !targetInput.disabled) {
                        targetInput.focus();
                        clearInterval(focusInterval);
                        return;
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
    st.markdown("<p style='font-size:16px; color:#666;'>※ 「処置」の列をクリックすると、表から直接プルダウンで内容を編集できます。</p>", unsafe_allow_html=True)
    
    df_history = pd.DataFrame(st.session_state.scan_history)
    
    # 🌟 修正：表示専用の dataframe を、編集可能な data_editor に変更！
    st.data_editor(
        df_history,
        use_container_width=True,
        key="history_editor",
        on_change=update_history_from_editor, # 表が書き換えられたら自動保存関数を呼び出す
        disabled=["グループID", "目標数", "判定", "参照先", "読込内容", "時刻"], # 「処置」以外は編集できないようにロック
        column_config={
            "処置": st.column_config.SelectboxColumn(
                "処置 (ここをクリックして編集)", 
                help="処置内容を変更できます",
                options=ACTION_OPTIONS, # プルダウンの選択肢をセット
                required=False
            )
        }
    )

# ====================================================
# ★ 途中でやり直す（リセット）ボタンを1つに統合
# ====================================================
st.write("---")
if st.button("🔄 最初からやり直す", disabled=needs_download, use_container_width=True):
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
        label="📦 【履歴データ】をダウンロードして消去",
        data=csv_master_all,
        file_name=f"All_History_Export_{jst_now.strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
        on_click=handle_download_all,
        args=(master_file,)
    )
else:
    st.info("まだ保存されたマスターデータがありません。（バーコードを読み込むと生成されます）")
