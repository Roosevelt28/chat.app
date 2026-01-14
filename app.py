import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from streamlit_mic_recorder import mic_recorder
import hashlib
import uuid
from PIL import Image
import io

# გვერდის კონფიგურაცია
st.set_page_config(page_title="Compact Pro Chat", page_icon="💬", layout="centered")

# --- გლობალური მონაცემების შენახვა ---
@st.cache_resource
def get_global_data():
    return {"messages": [], "online_users": set()}

data = get_global_data()

# ავტომატური განახლება ყოველ 3 წამში
st_autorefresh(interval=3000, key="datarefresh")

if "username" not in st.session_state:
    st.session_state.username = None
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

# --- რეგისტრაცია ---
if st.session_state.username is None:
    st.title("ჩატში შესვლა 💬")
    with st.form("login"):
        name = st.text_input("შეიყვანეთ თქვენი სახელი:")
        if st.form_submit_button("შესვლა") and name:
            st.session_state.username = name
            data["online_users"].add(name)
            st.rerun()
else:
    # --- ზედა პანელი ---
    st.markdown(f"### 💬 ჩატი: {st.session_state.username}")
    
    col_stat1, col_stat2 = st.columns([2, 1])
    col_stat1.write(f"🟢 ონლაინ: **{len(data['online_users'])}**")
    if col_stat2.button("🧹 გასუფთავება"):
        data["messages"] = []
        st.rerun()

    # --- შეტყობინებების ჩვენება ---
    chat_container = st.container()
    with chat_container:
        for idx, msg in enumerate(data["messages"]):
            # უსაფრთხოების შემოწმება ძველი მესიჯებისთვის
            if "reactions" not in msg:
                msg["reactions"] = {"❤️": [], "😂": [], "👍": [], "🔥": []}
            if "id" not in msg:
                msg["id"] = str(uuid.uuid4())

            with st.chat_message(msg["user"]):
                # მთავარი კონტენტი
                if msg["type"] == "text":
                    st.write(msg["content"])
                elif msg["type"] == "audio":
                    st.audio(msg["content"], format="audio/wav")
                elif msg["type"] == "image":
                    st.image(msg["content"], use_container_width=True)
                
                # ქვედა პანელი: დრო, რეაქციების მაჩვენებელი და მენიუ
                footer_col1, footer_col2 = st.columns([4, 1])
                
                with footer_col1:
                    # ნაჩვენები რეაქციები (მხოლოდ თუ ვინმემ დააჭირა)
                    active_reactions = [f"{k} {len(v)}" for k, v in msg["reactions"].items() if v]
                    reaction_summary = "  ".join(active_reactions)
                    st.caption(f"`{msg['time']}`  {reaction_summary}")

                with footer_col2:
                    # რეაქციების და წაშლის დამალული მენიუ
                    with st.popover("⚙️"):
                        st.write("რეაქცია:")
                        re_cols = st.columns(4)
                        emojis = ["❤️", "😂", "👍", "🔥"]
                        for i, emoji in enumerate(emojis):
                            if re_cols[i].button(emoji, key=f"re_{emoji}_{msg['id']}"):
                                if st.session_state.username in msg["reactions"][emoji]:
                                    msg["reactions"][emoji].remove(st.session_state.username)
                                else:
                                    msg["reactions"][emoji].append(st.session_state.username)
                                st.rerun()
                        
                        st.divider()
                        if msg["user"] == st.session_state.username:
                            if st.button("🗑️ წაშლა", key=f"del_{msg['id']}", use_container_width=True):
                                data["messages"].pop(idx)
                                st.rerun()

    st.divider()

    # --- შეტყობინების გაგზავნა ---
    
    # ფოტოს ატვირთვა
    uploaded_file = st.sidebar.file_uploader("🖼️ ფოტო", type=['png', 'jpg', 'jpeg'])
    if uploaded_file:
        img = Image.open(uploaded_file)
        img.thumbnail((500, 500))
        data["messages"].append({
            "id": str(uuid.uuid4()),
            "user": st.session_state.username,
            "type": "image",
            "content": img,
            "time": datetime.now().strftime("%H:%M"),
            "reactions": {"❤️": [], "😂": [], "👍": [], "🔥": []}
        })
        st.rerun()

    # ხმოვანი
    st.sidebar.write("🎤 ხმა:")
    audio = mic_recorder(start_prompt="ჩაწერა", stop_prompt="გაგზავნა", key='recorder')
    if audio and 'bytes' in audio:
        current_audio_hash = hashlib.md5(audio['bytes']).hexdigest()
