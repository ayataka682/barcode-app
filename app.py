import streamlit as st
import streamlit.components.v1 as components
import time

st.title("バーコード照合アプリ")

# 状態保持
if 'reference_code' not in st.session_state:
    st.session_state.reference_code = ""
if 'scanned_count' not in st.session_state:
    st.session_state.scanned_count = 0
if 'is_stopped' not in st.session_state:
    st.session_state.is_stopped = False
if 'play_voice' not in st.session_state:
    st.session_state.play_voice = False

# --- 改良機能1：NG時に女性の声（自動音声）で知らせる ---
def play_error_voice():
    components.html(
        """
        <script>
        // ブラウザの音声合成機能を使用
        var msg = new SpeechSynthesisUtterance("間違ってるよ！");
        msg.lang = "ja-JP"; // 日本語
        msg.pitch = 1.6;    // 高めの声（女性風）
        msg.rate = 1.2;     // 少し早口にしてテンポ良く
        window.parent.speechSynthesis.speak(msg);
        </script>
        """,
        height=0,
    )

# --- 改良機能2：空の入力欄に確実＆自動でカーソルを合わせる ---
def auto_focus():
    components.html(
        """
        <script>
        // 画面の描画が終わるのを0.3秒だけ待ってからカーソルを合わせる（確実性を上げるため）
        setTimeout(function() {
            var inputs = window.parent.document.querySelectorAll('input[type="text"]');
            for (var i = 0; i < inputs.length; i++) {
                // 無効化されておらず、かつ「中身が空っぽ」の入力欄を狙ってフォーカス
                if (!inputs[i].disabled && inputs[i].value === "") {
                    inputs[i].focus();
                    break;
                }
            }
        }, 300); 
        </script>
        """,
        height=0,
    )

# 1. 照合個数の設定
max_count = st.number_input("照合する個数を設定してください（最大30）", min_value=1, max_value=30, value=5)
st.write("---")

# 2. 参照先バーコードの登録
if not st.session_state.reference_code:
    st.info("💡 最初のバーコードを読み込んでください")
    ref_input = st.text_input("【1】参照先のバーコード", key="ref_input_ui")
    auto_focus() # カーソルを合わせる
    
    # 読み込まれたら（文字が入ったら）、ボタンを押さなくても即座に登録！
    if ref_input:
        st.session_state.reference_code = ref_input
        st.session_state.scanned_count = 0
        st.session_state.is_stopped = False
        st.session_state.play_voice = False
        st.rerun()

# 3. 照合処理（参照先が登録されている場合）
else:
    st.success(f"🎯 参照先: 【 {st.session_state.reference_code} 】")
    st.write(f"**現在の目標:** {st.session_state.scanned_count} / {max_count} 個完了")
    
    # NGが出た場合
    if st.session_state.is_stopped:
        st.error("❌ NGが検出されました！処理をストップしています。")
        if st.session_state.play_voice:
            play_error_voice() # 「間違ってるよ！」と喋る
            st.session_state.play_voice = False
            
    # 目標達成した場合
    elif st.session_state.scanned_count >= max_count:
        st.success("照合がすべて完了しました！")
        
    # 通常の読み込み画面
    else:
        check_input = st.text_input(f"【2】 {st.session_state.scanned_count + 1}個目の照合先を読み込んでください", key=f"check_{st.session_state.scanned_count}")
        auto_focus() # カーソルを合わせる
        
        if check_input:
            if check_input == st.session_state.reference_code:
                st.session_state.scanned_count += 1
                st.success("⭕ OK! 一致しました。")
                time.sleep(0.3) # 成功したことが一瞬見えるように0.3秒待つ
                st.rerun() 
            else:
                st.session_state.is_stopped = True
                st.session_state.play_voice = True
                st.rerun()

    # リセットボタン（エラー時や完了時に表示）
    st.write("---")
    if st.button("すべてリセットして最初から"):
        st.session_state.reference_code = ""
        st.session_state.scanned_count = 0
        st.session_state.is_stopped = False
        st.session_state.play_voice = False
        st.rerun()
