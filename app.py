import streamlit as st
import streamlit.components.v1 as components

st.title("バーコード照合アプリ")

# 状態（データ）を保持するための設定
if 'reference_code' not in st.session_state:
    st.session_state.reference_code = ""
if 'scanned_count' not in st.session_state:
    st.session_state.scanned_count = 0
if 'is_stopped' not in st.session_state:
    st.session_state.is_stopped = False
if 'play_buzzer' not in st.session_state:
    st.session_state.play_buzzer = False

# --- 追加機能1：NG時にブザー音を鳴らす仕組み ---
def play_error_buzzer():
    components.html(
        """
        <script>
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        oscillator.type = 'sawtooth'; // ビーッという警告音のような音色
        oscillator.frequency.setValueAtTime(800, audioCtx.currentTime); // 音の高さ
        gainNode.gain.setValueAtTime(0.5, audioCtx.currentTime); // 音量
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 1.0); // 1秒間鳴らす
        </script>
        """,
        height=0,
    )

# --- 追加機能2：入力欄に自動でカーソルを合わせる仕組み ---
def auto_focus():
    components.html(
        """
        <script>
        // 画面が更新されたら、入力できるテキストボックスを探して自動で選択する
        setTimeout(function() {
            var inputs = window.parent.document.querySelectorAll('input[type="text"]');
            for (var i = 0; i < inputs.length; i++) {
                if (!inputs[i].disabled) {
                    inputs[i].focus();
                    break;
                }
            }
        }, 100);
        </script>
        """,
        height=0,
    )

# 1. 照合個数の設定
max_count = st.number_input("照合する個数を設定してください（最大30）", min_value=1, max_value=30, value=5)

# 2. 参照先バーコードの登録
ref_input = st.text_input("【1】参照先のバーコードを読み込んでください", key="ref_input_ui")
auto_focus() # 起動時はここにカーソルを合わせる

if st.button("参照先を登録"):
    st.session_state.reference_code = ref_input
    st.session_state.scanned_count = 0
    st.session_state.is_stopped = False
    st.session_state.play_buzzer = False
    st.success(f"参照先を「{ref_input}」に設定しました！")
    st.rerun()

# 3. 照合処理
if st.session_state.reference_code:
    st.write("---")
    st.write(f"**現在の目標:** {st.session_state.scanned_count} / {max_count} 個完了")
    
    # NGが出た場合、または目標達成した場合はストップ
    if st.session_state.is_stopped:
        st.error("❌ NGが検出されました！処理をストップしています。")
        # ブザーを鳴らす処理（1回だけ鳴らす）
        if st.session_state.play_buzzer:
            play_error_buzzer()
            st.session_state.play_buzzer = False
            
    elif st.session_state.scanned_count >= max_count:
        st.success("照合がすべて完了しました！")
    else:
        # 照合用バーコードの読み込み
        check_input = st.text_input(f"【2】 {st.session_state.scanned_count + 1}個目の照合先を読み込んでください", key=f"check_{st.session_state.scanned_count}")
        
        if check_input:
            if check_input == st.session_state.reference_code:
                st.session_state.scanned_count += 1
                st.success("⭕ OK! 一致しました。")
                st.rerun() # 画面を更新して次の入力へ
            else:
                st.session_state.is_stopped = True
                st.session_state.play_buzzer = True # NGフラグを立ててブザー準備
                st.error(f"❌ NG! 一致しません。（読込: {check_input}）")
                st.rerun()

# リセットボタン
if st.button("リセットして最初から"):
    st.session_state.reference_code = ""
    st.session_state.scanned_count = 0
    st.session_state.is_stopped = False
    st.session_state.play_buzzer = False
    st.rerun()
