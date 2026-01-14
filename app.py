import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from streamlit_mic_recorder import mic_recorder
import hashlib

# გვერდის კონფიგურაცია
st.set_page_config(page_title="Real-Time Voice Chat", page_icon="🎤", layout="centered")

# --- გლობალური მონაცემების შენახვა (ყველა მომხმარებლისთვის) ---
@st.cache_resource
def get_global_data():
    return {"messages": [], "online_users": set()}

data = get_global_data()

# ავტომატური განახლება ყოველ 3 წამში
st_autorefresh(interval=3000, key="datarefresh")

# --- სესიის მართვა (ლოკალური მომხმარებლისთვის) ---
if "username" not in st.session_state:
    st.session_state.username = None
# აქ ვინახავთ ბოლო გაგზავნილი აუდიოს "თითის ანაბეჭდს" (ჰეშს)
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
    st.markdown(f"### 💬 ოთახი")
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
    
    # 1. ტექსტური შეტყობინება
    if prompt := st.chat_input("დაწერე შეტყობინება..."):
        data["messages"].append({
            "user": st.session_state.username,
            "type": "text",
            "content": prompt,
            "time": datetime.now().strftime("%H:%M")
        })
        st.rerun()

    # 2. ხმოვანი შეტყობინება
    st.sidebar.write("🎤 ჩაწერე ხმა:")
    audio = mic_recorder(
        start_prompt="ჩაწერა 🎙️",
        stop_prompt="გაგზავნა ✅",
        key='recorder'
    )

    if audio and 'bytes' in audio:
        # ვქმნით აუდიოს უნიკალურ ID-ს (ჰეშს)
        current_audio_hash = hashlib.md5(audio['bytes']).hexdigest()
        
        # ვამოწმებთ, ეს აუდიო უკვე გავგზავნეთ თუ არა ამ სესიაში
        if st.session_state.last_audio_hash != current_audio_hash:
            data["messages"].append({
                "user": st.session_state.username,
                "type": "audio",
                "content": audio['bytes'],
                "time": datetime.now().strftime("%H:%M")
            })
            # ვიმახსოვრებთ, რომ ეს აუდიო უკვე გაიგზავნა
            st.session_state.last_audio_hash = current_audio_hash
            st.rerun()

    # გასვლა
    if st.sidebar.button("გამოსვლა"):
        data["online_users"].discard(st.session_state.username)
        st.session_state.username = None
        st.rerun()
