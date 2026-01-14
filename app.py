import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from streamlit_mic_recorder import mic_recorder
import hashlib
import uuid
from PIL import Image
import io

# გვერდის კონფიგურაცია
st.set_page_config(page_title="Pro Chat & Media", page_icon="📸", layout="centered")

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
    # --- ჩატის ინტერფეისი ---
    st.markdown(f"### 💬 საერთო ოთახი")
    
    col_stat1, col_stat2 = st.columns([2, 1])
    col_stat1.write(f"🟢 ონლაინ: **{len(data['online_users'])}**")
    if col_stat2.button("🧹 ჩატის გასუფთავება"):
        data["messages"] = []
        st.rerun()

    # შეტყობინებების ჩვენება
    chat_container = st.container()
    with chat_container:
        for idx, msg in enumerate(data["messages"]):
            # KeyError-ის პრევენცია: თუ ძველი მესიჯია, ვამატებთ ცარიელ რეაქციებს
            if "reactions" not in msg:
                msg["reactions"] = {"❤️": [], "😂": [], "👍": [], "🔥": []}
            if "id" not in msg:
                msg["id"] = str(uuid.uuid4())

            with st.chat_message(msg["user"]):
                col_text, col_action = st.columns([4, 1])
                
                with col_text:
                    st.write(f"**{msg['user']}** | `{msg['time']}`")
                    
                    # შეტყობინების ტიპის მიხედვით ჩვენება
                    if msg["type"] == "text":
                        st.write(msg["content"])
                    elif msg["type"] == "audio":
                        st.audio(msg["content"], format="audio/wav")
                    elif msg["type"] == "image":
                        st.image(msg["content"], use_container_width=True)
                    
                    # რეაქციების ჩვენება
                    reaction_list = [f"{k} {len(v)}" for k, v in msg["reactions"].items() if v]
                    if reaction_list:
                        st.caption("  ".join(reaction_list))

                with col_action:
                    if msg["user"] == st.session_state.username:
                        if st.button("🗑️", key=f"del_{msg['id']}"):
                            data["messages"].pop(idx)
                            st.rerun()
                
                # რეაქციების ღილაკები
                re_cols = st.columns(5)
                for i, emoji in enumerate(["❤️", "😂", "👍", "🔥"]):
                    if re_cols[i].button(emoji, key=f"re_{emoji}_{msg['id']}"):
                        if st.session_state.username in msg["reactions"][emoji]:
                            msg["reactions"][emoji].remove(st.session_state.username)
                        else:
                            msg["reactions"][emoji].append(st.session_state.username)
                        st.rerun()

    st.divider()

    # --- მულტიმედია გაგზავნა ---
    
    # 1. ფოტოს ატვირთვა
    uploaded_file = st.sidebar.file_uploader("🖼️ გაგზავნე ფოტო", type=['png', 'jpg', 'jpeg'])
    if uploaded_file:
        img = Image.open(uploaded_file)
        # ფოტოს ოპტიმიზაცია (რომ სერვერი არ გაჭედოს)
        img.thumbnail((500, 500))
        data["messages"].append({
            "id": str(uuid.uuid4()),
            "user": st.session_state.username,
            "type": "image",
            "content": img,
            "time": datetime.now().strftime("%H:%M"),
            "reactions": {"❤️": [], "😂": [], "👍": [], "🔥": []}
        })
        st.sidebar.success("ფოტო გაიგზავნა!")
        st.rerun()

    # 2. ხმოვანი
    st.sidebar.write("🎤 ხმის ჩაწერა:")
    audio = mic_recorder(start_prompt="ჩაწერა 🎙️", stop_prompt="გაგზავნა ✅", key='recorder')
    if audio and 'bytes' in audio:
        current_audio_hash = hashlib.md5(audio['bytes']).hexdigest()
        if st.session_state.last_audio_hash != current_audio_hash:
            data["messages"].append({
                "id": str(uuid.uuid4()),
                "user": st.session_state.username,
                "type": "audio",
                "content": audio['bytes'],
                "time": datetime.now().strftime("%H:%M"),
                "reactions": {"❤️": [], "😂": [], "👍": [], "🔥": []}
            })
            st.session_state.last_audio_hash = current_audio_hash
            st.rerun()

    # 3. ტექსტი
    if prompt := st.chat_input("დაწერე შეტყობინება..."):
        data["messages"].append({
            "id": str(uuid.uuid4()),
            "user": st.session_state.username,
            "type": "text",
            "content": prompt,
            "time": datetime.now().strftime("%H:%M"),
            "reactions": {"❤️": [], "😂": [], "👍": [], "🔥": []}
        })
        st.rerun()

    if st.sidebar.button("გამოსვლა"):
        data["online_users"].discard(st.session_state.username)
        st.session_state.username = None
        st.rerun()
