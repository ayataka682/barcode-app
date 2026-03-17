import streamlit as st

st.title("バーコード照合アプリ")

# 状態（データ）を保持するための設定
if 'reference_code' not in st.session_state:
    st.session_state.reference_code = ""
if 'scanned_count' not in st.session_state:
    st.session_state.scanned_count = 0
if 'is_stopped' not in st.session_state:
    st.session_state.is_stopped = False

# 1. 照合個数の設定
max_count = st.number_input("照合する個数を設定してください（最大30）", min_value=1, max_value=30, value=5)

# 2. 参照先バーコードの登録
ref_input = st.text_input("【1】参照先のバーコードを読み込んでください", key="ref_input_ui")
if st.button("参照先を登録"):
    st.session_state.reference_code = ref_input
    st.session_state.scanned_count = 0
    st.session_state.is_stopped = False
    st.success(f"参照先を「{ref_input}」に設定しました！")

# 3. 照合処理
if st.session_state.reference_code:
    st.write("---")
    st.write(f"**現在の目標:** {st.session_state.scanned_count} / {max_count} 個完了")
    
    # NGが出た場合、または目標達成した場合はストップ
    if st.session_state.is_stopped:
        st.error("❌ NGが検出されました！処理をストップしています。最初からやり直してください。")
    elif st.session_state.scanned_count >= max_count:
        st.success("✨ 目標個数の照合がすべて完了しました！")
    else:
        # 照合用バーコードの読み込み
        check_input = st.text_input("【2】照合先のバーコードを読み込んでください（Enterで判定）", key=f"check_{st.session_state.scanned_count}")
        
        if check_input:
            if check_input == st.session_state.reference_code:
                st.session_state.scanned_count += 1
                st.success("⭕ OK! 一致しました。")
                st.rerun() # 画面を更新して次の入力へ
            else:
                st.session_state.is_stopped = True
                st.error(f"❌ NG! 一致しません。（読込: {check_input}）")
                st.rerun()

# リセットボタン
if st.button("すべてリセットして最初から"):
    st.session_state.reference_code = ""
    st.session_state.scanned_count = 0
    st.session_state.is_stopped = False
    st.rerun()
