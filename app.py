import streamlit as st
import streamlit.components.v1 as components

st.title("バーコード照合アプリ")

# 1. 初期状態の準備
if 'reference_code' not in st.session_state:
    st.session_state.reference_code = ""
if 'scanned_count' not in st.session_state:
    st.session_state.scanned_count = 0
if 'last_scan_ng' not in st.session_state: # ストップではなく「直前がNGだったか」を記録するフラグ
    st.session_state.last_scan_ng = False
if 'ng_text' not in st.session_state: # 間違えて読み込んだ文字を記録
    st.session_state.ng_text = ""
if 'play_voice' not in st.session_state:
    st.session_state.play_voice = False
if 'scan_input' not in st.session_state:
    st.session_state.scan_input = ""

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
        st.session_state.last_scan_ng = False # 成功したらNG状態をリセット
    else:
        st.session_state.last_scan_ng = True  # NG状態にする（※ストップはしない）
        st.session_state.play_voice = True
        st.session_state.ng_text = scanned_text # 何を間違えて読み込んだか記録しておく
        
    st.session_state.scan_input = "" # 次の読み込みのために空に戻す

# 4. 画面の表示部分
max_count = st.number_input("照合する個数を設定してください（最大30）", min_value=1, max_value=30, value=5)
st.write("---")

# 目標達成した場合
if st.session_state.reference_code and st.session_state.scanned_count >= max_count:
    st.success("✨ 目標個数の照合がすべて完了しました！")
    if st.button("すべてリセットして最初から"):
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
        
        # ★追加：NGだった場合の警告表示（ストップせず、再入力を促す）
        if st.session_state.last_scan_ng:
            st.error(f"❌ NG! 一致しませんでした。（読込: {st.session_state.ng_text}）\n\nもう一度、正しいバーコードを読み込んでください。")
            if st.session_state.play_voice:
                play_error_voice()
                st.session_state.play_voice = False # 1回だけ喋らせる
        else:
            st.info(f"💡 【2】 {st.session_state.scanned_count + 1}個目の照合先を読み込んでください")

    # 入力欄（NGのときも常に表示し続けることで、すぐ再読み込み可能にする）
    st.text_input(
        "▼ ここにカーソルがある状態で読み込んでください", 
        key="scan_input", 
        on_change=process_scan
    )
    
    # 強力な自動フォーカス機能（カーソルを維持）
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
    
    # 途中リセットボタン
    st.write("---")
    if st.button("リセットして最初から"):
        st.session_state.reference_code = ""
        st.session_state.scanned_count = 0
        st.session_state.last_scan_ng = False
        st.session_state.play_voice = False
        st.rerun()
