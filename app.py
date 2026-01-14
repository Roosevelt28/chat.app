import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from streamlit_mic_recorder import mic_recorder
import hashlib
import uuid

# გვერდის კონფიგურაცია
st.set_page_config(page_title="Real-Time Pro Chat", page_icon="💬", layout="centered")

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
    st.write(f"🟢 ონლაინ: **{len(data['online_users'])}**")

    # შეტყობინებების ჩვენება
    chat_container = st.container()
    with chat_container:
        # ვიყენებთ enumerate-ს ინდექსისთვის, რომ წაშლა გაგვიადვილდეს
        for idx, msg in enumerate(data["messages"]):
            with st.chat_message(msg["user"]):
                col_text, col_action = st.columns([4, 1])
                
                with col_text:
                    st.write(f"**{msg['user']}** | `{msg['time']}`")
                    if msg["type"] == "text":
                        st.write(msg["content"])
                    else:
                        st.audio(msg["content"], format="audio/wav")
                    
                    # რეაქციების ჩვენება
                    if msg["reactions"]:
                        reaction_text = ""
                        for emoji, users in msg["reactions"].items():
                            if users:
                                reaction_text += f"{emoji} {len(users)}  "
                        if reaction_text:
                            st.caption(reaction_text)

                with col_action:
                    # წაშლის ღილაკი (მხოლოდ ავტორისთვის)
                    if msg["user"] == st.session_state.username:
                        if st.button("🗑️", key=f"del_{msg['id']}"):
                            data["messages"].pop(idx)
                            st.rerun()
                
                # რეაქციების ღილაკები
                re_col1, re_col2, re_col3, re_col4 = st.columns([1,1,1,7])
                emojis = ["❤️", "😂", "👍", "🔥"]
                cols = [re_col1, re_col2, re_col3, re_col4]
                
                for i, emoji in enumerate(emojis):
                    with cols[i]:
                        if st.button(emoji, key=f"re_{emoji}_{msg['id']}"):
                            # თუ მომხმარებელს უკვე აქვს რეაქცია, ვაცილებთ, თუ არა - ვამატებთ
                            if st.session_state.username in msg["reactions"][emoji]:
                                msg["reactions"][emoji].remove(st.session_state.username)
                            else:
                                msg["reactions"][emoji].append(st.session_state.username)
                            st.rerun()

    st.divider()

    # --- შეტყობინების გაგზავნა ---
    
    # 1. ტექსტური
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

    # 2. ხმოვანი
    st.sidebar.write("🎤 ჩაწერე ხმა:")
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

    if st.sidebar.button("გამოსვლა"):
        data["online_users"].discard(st.session_state.username)
        st.session_state.username = None
        st.rerun()
