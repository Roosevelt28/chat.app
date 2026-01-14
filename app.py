import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from streamlit_mic_recorder import mic_recorder
import hashlib
import uuid
from PIL import Image

# 1. გვერდის კონფიგურაცია
st.set_page_config(page_title="Pro Chat", page_icon="💬", layout="centered")

# 2. გლობალური მონაცემების შენახვა
@st.cache_resource
def get_global_data():
    return {"messages": [], "online_users": set()}

data = get_global_data()

# ავტომატური განახლება ყოველ 3 წამში
st_autorefresh(interval=3000, key="datarefresh")

# სესიის ცვლადების ინიციალიზაცია
if "username" not in st.session_state:
    st.session_state.username = None
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None
# ფოტოს დუბლირების თავიდან ასაცილებლად
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())

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
    # --- მთავარი ინტერფეისი ---
    st.markdown(f"### 💬 ჩატი: {st.session_state.username}")
    
    col_top1, col_top2 = st.columns([2, 1])
    col_top1.write(f"🟢 ონლაინ: **{len(data['online_users'])}**")
    if col_top2.button("🧹 ჩატის გასუფთავება"):
        data["messages"] = []
        st.rerun()

    # --- შეტყობინებების ჩვენება ---
    chat_container = st.container()
    with chat_container:
        for idx, msg in enumerate(data["messages"]):
            if "reactions" not in msg:
                msg["reactions"] = {"❤️": [], "😂": [], "👍": [], "🔥": []}
            if "id" not in msg:
                msg["id"] = str(uuid.uuid4())

            with st.chat_message(msg["user"]):
                if msg["type"] == "text":
                    st.write(msg["content"])
                elif msg["type"] == "audio":
                    st.audio(msg["content"], format="audio/wav")
                elif msg["type"] == "image":
                    st.image(msg["content"], use_container_width=True)
                
                active_re = [f"{k} {len(v)}" for k, v in msg["reactions"].items() if v]
                st.caption(f"`{msg['time']}`  {' '.join(active_re)}")

                col_f1, col_f2 = st.columns([5, 1])
                with col_f1:
                    with st.popover("😊"):
                        re_cols = st.columns(4)
                        emojis = ["❤️", "😂", "👍", "🔥"]
                        for i, emoji in enumerate(emojis):
                            if re_cols[i].button(emoji, key=f"re_{emoji}_{msg['id']}"):
                                if st.session_state.username in msg["reactions"][emoji]:
                                    msg["reactions"][emoji].remove(st.session_state.username)
                                else:
                                    msg["reactions"][emoji].append(st.session_state.username)
                                st.rerun()
                with col_f2:
                    if msg["user"] == st.session_state.username:
                        if st.button("🗑️", key=f"del_{msg['id']}"):
                            data["messages"].pop(idx)
                            st.rerun()

    st.divider()

    # --- მედია ფუნქციები ---
    st.write("📷 გაგზავნე მედია:")
    col_voice, col_photo = st.columns(2)
    
    with col_voice:
        audio = mic_recorder(start_prompt="🎤 ხმა", stop_prompt="✅ გაგზავნა", key='recorder')
    
    with col_photo:
        # ვიყენებთ დინამიურ uploader_key-ს
        uploaded_file = st.file_uploader(
            "🖼️ ფოტო", 
            type=['png', 'jpg', 'jpeg'], 
            label_visibility="collapsed",
            key=st.session_state.uploader_key
        )

    # ხმის დამუშავება
    if audio and 'bytes' in audio:
        current_hash = hashlib.md5(audio['bytes']).hexdigest()
        if st.session_state.last_audio_hash != current_hash:
            data["messages"].append({
                "id": str(uuid.uuid4()),
                "user": st.session_state.username,
                "type": "audio",
                "content": audio['bytes'],
                "time": datetime.now().strftime("%H:%M"),
                "reactions": {"❤️": [], "😂": [], "👍": [], "🔥": []}
            })
            st.session_state.last_audio_hash = current_hash
            if len(data["messages"]) > 30: data["messages"].pop(0)
            st.rerun()

    # ფოტოს დამუშავება (გასწორებული ლოგიკა)
    if uploaded_file:
        img = Image.open(uploaded_file)
        img.thumbnail((400, 400))
        data["messages"].append({
            "id": str(uuid.uuid4()),
            "user": st.session_state.username,
            "type": "image",
            "content": img,
            "time": datetime.now().strftime("%H:%M"),
            "reactions": {"❤️": [], "😂": [], "👍": [], "🔥": []}
        })
        if len(data["messages"]) > 30: data["messages"].pop(0)
        
        # ფოტოს გაგზავნის შემდეგ ვცვლით key-ს, რაც აცარიელებს uploader-ს
        st.session_state.uploader_key = str(uuid.uuid4())
        st.rerun()

    # ტექსტური შეტყობინება
    if prompt := st.chat_input("დაწერე შეტყობინება..."):
        data["messages"].append({
            "id": str(uuid.uuid4()),
            "user": st.session_state.username,
            "type": "text",
            "content": prompt,
            "time": datetime.now().strftime("%H:%M"),
            "reactions": {"❤️": [], "😂": [], "👍": [], "🔥": []}
        })
        if len(data["messages"]) > 30: data["messages"].pop(0)
        st.rerun()

    if st.sidebar.button("🚪 ჩატიდან გასვლა"):
        data["online_users"].discard(st.session_state.username)
        st.session_state.username = None
        st.rerun()
