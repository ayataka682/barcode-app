import streamlit as st
import streamlit.components.v1 as components
import datetime # 日時を取得するためのツールを追加

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
if 'play_voice' not in st.session_state:
    st.session_state.play_voice = False
if 'scan_input' not in st.session_state:
    st.session_state.scan_input = ""
# ★追加：NGの履歴を保存するリスト
if 'ng_logs' not in st.session_state:
    st.session_state.ng_logs = []

# 2. 女性の声（自動音声）の仕組み
def play_error_voice():
    components.html(
        """
        <script>
        var msg = new SpeechSynthesisUtterance("間違ってるよ！");
        msg.lang = "ja-JP";
        msg.pitch = 1.6;
        msg.rate = 1.2;
        window.speechSynthesis.speak(msg);
        </script>
        """,
        height=0,
    )

# 3. 読み込まれた瞬間に動く自動処理
def process_scan():
    scanned_text = st.session_state.scan_input
    
    if not scanned_text:
        return

    # A. 参照先がまだ登録されていない場合
    if not st.session_state.reference_code:
        st.session_state.reference_code = scanned_text
        st.session_state.scan_input = ""
        st.session_state.last_scan_ng = False
        return

    # B. 照合先を読み込んだ場合
    if scanned_text == st.session_state.reference_code:
        st.session_state.scanned_count += 1
        st.session_state.last_scan_ng = False
    else:
        st.session_state.last_scan_ng = True
        st.session_state.play_voice = True
        st.session_state.ng_text = scanned_text
        
        # ★追加：NGのログを作成してリストに追加
        now = datetime.datetime.now()
        # 日本時間に合わせる（サーバーの時間がずれていることがあるため+9時間）
        jst_now = now + datetime.timedelta(hours=9) 
        time_str = jst_now.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{time_str}] 参照先: {st.session_state.reference_code} / 誤読込: {scanned_text}"
        st.session_state.ng_logs.append(log_entry)
        
    st.session_state.scan_input = ""

# 4. 画面の表示部分
max_count = st.number_input("照合する個数を設定してください（最大30）", min_value=1, max_value=30, value=5)
st.write("---")

# 目標達成した場合
if st.session_state.reference_code and st.session_state.scanned_count >= max_count:
    st.success("✨ 目標個数の照合がすべて完了しました！")
    if st.button("リセットして次へ"):
        st.session_state.reference_code = ""
        st.session_state.scanned_count = 0
        st.session_state.last_scan_ng = False
        st.session_state.play_voice = False
        st.rerun()

# 通常の読み込み・再読み込み待ち状態の場合
else:
    if not st.session_state.reference_code:
        st.info("💡 【1】最初のバーコード（参照先）を読み込んでください")
    else:
        st.success(f"🎯 参照先: 【 {st.session_state.reference_code} 】")
        st.write(f"**現在の目標:** {st.session_state.scanned_count} / {max_count} 個完了")
        
        # NGだった場合の警告表示
        if st.session_state.last_scan_ng:
            st.error(f"❌ NG! 一致しませんでした。（読込: {st.session_state.ng_text}）\n\nもう一度、正しいバーコードを読み込んでください。")
            if st.session_state.play_voice:
                play_error_voice()
                st.session_state.play_voice = False
        else:
            st.info(f"💡 【2】 {st.session_state.scanned_count + 1}個目の照合先を読み込んでください")

    # 入力欄
    st.text_input(
        "▼ ここにカーソルがある状態で読み込んでください", 
        key="scan_input", 
        on_change=process_scan
    )
    
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
        """,
        height=0,
    )

# --- ログの表示とダウンロード機能 ---
st.write("---")
st.write("### 📋 NGログ（記録）")

# ログがある場合だけダウンロードボタンを表示
if st.session_state.ng_logs:
    # リストになっているログを改行でつないで1つのテキストにする
    log_text = "\n".join(st.session_state.ng_logs)
    
    # ダウンロードボタン
    st.download_button(
        label="📥 NGログをテキストでダウンロード",
        data=log_text,
        file_name="NG_log.txt",
        mime="text/plain"
    )
    
    # 画面上でも最近のログを少し見えるようにする
    with st.expander("ログの中身を見る"):
        st.text(log_text)
else:
    st.write("現在、NGの記録はありません。")

# 強制リセットボタン
st.write("---")
if st.button("すべて初期化（※ログも消えます）"):
    st.session_state.reference_code = ""
    st.session_state.scanned_count = 0
    st.session_state.last_scan_ng = False
    st.session_state.play_voice = False
    st.session_state.ng_logs = [] # ログも消去
    st.rerun()
