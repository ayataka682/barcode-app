import streamlit as st
import streamlit.components.v1 as components
import datetime
import pandas as pd
import time
import base64
import os

st.title("バーコード照合アプリ")

# 1. 初期状態の準備
if 'reference_code' not in st.session_state:
    st.session_state.reference_code = ""
if 'scanned_count' not in st.session_state:
    st.session_state.scanned_count = 0
if 'last_scan_ng' not in st.session_state:
    st.session_state.last_scan_ng = False
if 'ng_text' not in st.session_state:
    st.session_state.ng_text = ""
if 'last_scan_ok' not in st.session_state:
    st.session_state.last_scan_ok = False
if 'ok_text' not in st.session_state:
    st.session_state.ok_text = ""
if 'play_voice' not in st.session_state:
    st.session_state.play_voice = False
if 'scan_input' not in st.session_state:
    st.session_state.scan_input = ""
if 'scan_history' not in st.session_state:
    st.session_state.scan_history = []
if 'cycle_has_ng' not in st.session_state:
    st.session_state.cycle_has_ng = False
if 'play_completion_warning' not in st.session_state:
    st.session_state.play_completion_warning = False

# リセット時に状態を綺麗にする関数
def reset_cycle():
    st.session_state.scan_history = [log for log in st.session_state.scan_history if log["判定"] == "❌ NG"]
    st.session_state.reference_code = ""
    st.session_state.scanned_count = 0
    st.session_state.last_scan_ng = False
    st.session_state.last_scan_ok = False
    st.session_state.play_voice = False
    st.session_state.cycle_has_ng = False 
    st.session_state.play_completion_warning = False

# 2. 音声ファイルを読み込んで再生する仕組み
# ① NG用の音声（ng_voice.wav.wav）
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

# ② 【変更】完了時の警告用の音声（warning_voice.wav）
def play_completion_warning_wav_file():
    WAV_FILE = "warning_voice.wav" # ここで新しいファイルを指定
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

# 3. 読み込まれた瞬間に動く自動処理
max_count = st.number_input("照合する個数を設定してください（最大30）", min_value=1, max_value=30, value=5)

def process_scan():
    scanned_text = st.session_state.scan_input
    if not scanned_text:
        return

    now = datetime.datetime.now()
    jst_now = now + datetime.timedelta(hours=9) 
    time_str = jst_now.strftime("%Y-%m-%d %H:%M:%S") 

    if not st.session_state.reference_code:
        st.session_state.reference_code = scanned_text
        st.session_state.scan_input = ""
        st.session_state.last_scan_ng = False
        st.session_state.last_scan_ok = False
        return

    if scanned_text == st.session_state.reference_code:
        st.session_state.scanned_count += 1
        st.session_state.last_scan_ng = False
        st.session_state.last_scan_ok = True
        st.session_state.ok_text = scanned_text
        
        st.session_state.scan_history.insert(0, {
            "判定": "⭕ OK", 
            "参照先": st.session_state.reference_code,
            "読込内容": scanned_text,
            "時刻": time_str
        })
        
        if st.session_state.scanned_count >= max_count and st.session_state.cycle_has_ng:
            st.session_state.play_completion_warning = True

    else:
        st.session_state.last_scan_ng = True
        st.session_state.last_scan_ok = False
        st.session_state.play_voice = True
        st.session_state.ng_text = scanned_text
        st.session_state.cycle_has_ng = True 
        
        st.session_state.scan_history.insert(0, {
            "判定": "❌ NG", 
            "参照先": st.session_state.reference_code,
            "読込内容": scanned_text,
            "時刻": time_str
        })
        
    st.session_state.scan_input = ""

# 4. 画面の表示部分
st.write("---")

if st.session_state.reference_code:
    st.markdown(
        f"""
        <div style="background-color:#e6f7ff; border:2px solid #1890ff; padding:20px; border-radius:10px; text-align:center; margin-bottom:20px;">
            <p style="margin:0; font-size:18px; color:#0050b3; font-weight:bold;">🎯 現在の参照先バーコード</p>
            <p style="margin:0; font-size:48px; font-weight:bold; color:#002c8c; letter-spacing: 2px;">{st.session_state.reference_code}</p>
        </div>
        """, unsafe_allow_html=True
    )

# --- 目標達成した場合の特大表示 ---
if st.session_state.reference_code and st.session_state.scanned_count >= max_count:
    
    # パターンA：途中でNGがあった場合
    if st.session_state.cycle_has_ng:
        st.markdown(
            """
            <div style="background-color:#fff3cd; border:4px solid #ffc107; padding:30px; border-radius:15px; text-align:center; margin-bottom:20px;">
                <p style="margin:0; font-size:40px; font-weight:bold; color:#856404;">⚠️ 照合完了（※要確認） ⚠️</p>
                <p style="margin-top:10px; font-size:22px; color:#856404; font-weight:bold;">作業中にNGが発生しました。履歴を確認してください。</p>
            </div>
            """, unsafe_allow_html=True
        )
        if st.session_state.play_completion_warning:
            # ★ここを変更：新しいWAV再生関数を呼び出す
            play_completion_warning_wav_file()
            st.session_state.play_completion_warning = False

    # パターンB：ノーミスだった場合
    else:
        st.markdown(
            """
            <div style="background-color:#d4edda; border:4px solid #28a745; padding:30px; border-radius:15px; text-align:center; margin-bottom:20px;">
                <p style="margin:0; font-size:40px; font-weight:bold; color:#155724;">✨ 照合完了（完全一致） ✨</p>
            </div>
            """, unsafe_allow_html=True
        )

    if st.button("リセットして次へ", type="primary", use_container_width=True):
        reset_cycle()
        st.rerun()

# --- 通常の読み込み待ち状態の場合 ---
else:
    if not st.session_state.reference_code:
        st.info("💡 【1】最初のバーコード（参照先）を読み込んでください")
    else:
        st.write(f"**現在の目標:** {st.session_state.scanned_count} / {max_count} 個完了")
        
        # 直前がNGだった場合
        if st.session_state.last_scan_ng:
            st.error(f"❌ NG! 一致しませんでした。（読込: {st.session_state.ng_text}）\n\nもう一度、正しいバーコードを読み込んでください。")
            if st.session_state.play_voice:
                play_error_wav_file()
                st.session_state.play_voice = False
                
        # 直前がOKだった場合
        elif st.session_state.last_scan_ok:
            st.success(f"⭕ OK! 一致しました。（読込: {st.session_state.ok_text}）")
            st.info(f"💡 【2】 {st.session_state.scanned_count + 1}個目の照合先を読み込んでください")
            
        else:
            st.info(f"💡 【2】 {st.session_state.scanned_count + 1}個目の照合先を読み込んでください")

    # 入力欄
    st.text_input("▼ ここにカーソルがある状態で読み込んでください", key="scan_input", on_change=process_scan)
    
    # 強力な自動フォーカス機能
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
    st.write("### 📋 照合履歴（最新が一番上）")
    
    df_history = pd.DataFrame(st.session_state.scan_history)
    st.dataframe(df_history, use_container_width=True)
    
    df_ng_only = df_history[df_history["判定"] == "❌ NG"]
    if not df_ng_only.empty:
        csv = df_ng_only.to_csv(index=False).encode('utf-8-sig') 
        st.download_button(
            label="📥 NG履歴のみをCSV（Excel用）でダウンロード",
            data=csv,
            file_name="ng_history.csv",
            mime="text/csv",
        )

# --- 強制リセットボタン ---
st.write("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("途中でリセット（※OK履歴のみ消去）"):
        reset_cycle()
        st.rerun()
with col2:
    if st.button("完全初期化（※NG履歴もすべて消去）"):
        st.session_state.reference_code = ""
        st.session_state.scanned_count = 0
        st.session_state.last_scan_ng = False
        st.session_state.last_scan_ok = False
        st.session_state.play_voice = False
        st.session_state.cycle_has_ng = False
        st.session_state.play_completion_warning = False
        st.session_state.scan_history = [] 
        st.rerun()
