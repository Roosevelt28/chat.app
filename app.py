import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from streamlit_mic_recorder import mic_recorder

# გვერდის კონფიგურაცია
st.set_page_config(page_title="Real-Time Voice Chat", page_icon="🎤", layout="centered")

# --- გლობალური მონაცემების შენახვა ---
@st.cache_resource
def get_global_data():
    return {"messages": [], "online_users": set()}

data = get_global_data()

# ავტომატური განახლება ყოველ 3 წამში
st_autorefresh(interval=3000, key="datarefresh")

if "username" not in st.session_state:
    st.session_state.username = None

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
    st.markdown(f"### 💬 ოთახი: {st.session_state.username}")
    st.write(f"🟢 ონლაინ: **{len(data['online_users'])}**")

    # შეტყობინებების ჩვენება
    chat_container = st.container()
    with chat_container:
        for msg in data["messages"]:
            with st.chat_message(msg["user"]):
                st.write(f"**{msg['user']}** | `{msg['time']}`")
                if msg["type"] == "text":
                    st.write(msg["content"])
                else:
                    st.audio(msg["content"], format="audio/wav")

    st.divider()

    # --- შეტყობინების გაგზავნა ---
    
    # ტექსტი
    if prompt := st.chat_input("დაწერე შეტყობინება..."):
        data["messages"].append({
            "user": st.session_state.username,
            "type": "text",
            "content": prompt,
            "time": datetime.now().strftime("%H:%M")
        })
        st.rerun()

    # ხმა (გამოსწორებული ფუნქცია)
    st.sidebar.write("🎤 ხმის ჩაწერა:")
    # წავშალეთ use_recorder=True, რადგან ის ხშირად იწვევს შეცდომას
    audio = mic_recorder(
        start_prompt="ჩაწერა 🎙️",
        stop_prompt="გაგზავნა ✅",
        key='recorder'
    )

    if audio and 'bytes' in audio:
        audio_bytes = audio['bytes']
        
        # ვამოწმებთ, რომ ეს კონკრეტული აუდიო უკვე არ არის ბოლო შეტყობინება
        # ვიყენებთ ჰეშს ან ზომას მარტივი შედარებისთვის
        is_duplicate = False
        if data["messages"]:
            last_msg = data["messages"][-1]
            if last_msg["type"] == "audio" and len(last_msg["content"]) == len(audio_bytes):
                is_duplicate = True
        
        if not is_duplicate:
            data["messages"].append({
                "user": st.session_state.username,
                "type": "audio",
                "content": audio_bytes,
                "time": datetime.now().strftime("%H:%M")
            })
            st.rerun()

    if st.sidebar.button("გამოსვლა"):
        data["online_users"].discard(st.session_state.username)
        st.session_state.username = None
        st.rerun()
