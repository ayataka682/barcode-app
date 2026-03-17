import streamlit as st
import streamlit.components.v1 as components

st.title("バーコード照合アプリ")

# 1. 初期状態の準備
if 'reference_code' not in st.session_state:
    st.session_state.reference_code = ""
if 'scanned_count' not in st.session_state:
    st.session_state.scanned_count = 0
if 'is_stopped' not in st.session_state:
    st.session_state.is_stopped = False
if 'play_voice' not in st.session_state:
    st.session_state.play_voice = False
if 'scan_input' not in st.session_state: # 常設する入力欄用のデータ
    st.session_state.scan_input = ""

# 2. 女性の声（自動音声）の仕組み（クラウドでも鳴りやすい書き方に修正）
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

# 3. 【重要】読み込まれた瞬間に動く「魔法の自動処理」
def process_scan():
    # 入力された文字を取得
    scanned_text = st.session_state.scan_input
    
    if not scanned_text:
        return # 空打ちの場合は何もしない

    # A. 参照先がまだ登録されていない場合
    if not st.session_state.reference_code:
        st.session_state.reference_code = scanned_text
        st.session_state.scan_input = "" # 入力欄を空に戻す（カーソルは維持される）
        return

    # B. 照合先を読み込んだ場合
    if scanned_text == st.session_state.reference_code:
        st.session_state.scanned_count += 1
    else:
        st.session_state.is_stopped = True
        st.session_state.play_voice = True
        
    st.session_state.scan_input = "" # 次の読み込みのために空に戻す

# 4. 画面の表示部分
max_count = st.number_input("照合する個数を設定してください（最大30）", min_value=1, max_value=30, value=5)
st.write("---")

# NGストップ状態の場合
if st.session_state.is_stopped:
    st.error("❌ NGが検出されました！処理をストップしています。")
    if st.session_state.play_voice:
        play_error_voice()
        st.session_state.play_voice = False # 1回だけ鳴らす
    
    if st.button("すべてリセットして最初から"):
        st.session_state.reference_code = ""
        st.session_state.scanned_count = 0
        st.session_state.is_stopped = False
        st.rerun()

# 目標達成した場合
elif st.session_state.reference_code and st.session_state.scanned_count >= max_count:
    st.success("✨ 目標個数の照合がすべて完了しました！")
    if st.button("すべてリセットして最初から"):
        st.session_state.reference_code = ""
        st.session_state.scanned_count = 0
        st.session_state.is_stopped = False
        st.rerun()

# 通常の読み込み待ち状態の場合
else:
    if not st.session_state.reference_code:
        st.info("💡 【1】最初のバーコード（参照先）を読み込んでください")
    else:
        st.success(f"🎯 参照先: 【 {st.session_state.reference_code} 】")
        st.write(f"**現在の目標:** {st.session_state.scanned_count} / {max_count} 個完了")
        st.info(f"💡 【2】 {st.session_state.scanned_count + 1}個目の照合先を読み込んでください")

    # ★最大の改良ポイント：常に同じ入力欄を置き続ける
    st.text_input(
        "▼ ここにカーソルがある状態で読み込んでください", 
        key="scan_input", 
        on_change=process_scan # 読み込んだ（Enterが押された）瞬間に上の処理を実行
    )
    
    # さらに念押し！強力な自動フォーカス機能（エラー対策版）
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
                if (attempts > 20) clearInterval(focusInterval); // 2秒で見つからなければ諦める
            }, 100);
        } catch (e) {
            // クラウド環境のセキュリティでブロックされた場合は無視する
        }
        </script>
        """,
        height=0,
    )
