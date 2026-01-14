import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from streamlit_mic_recorder import mic_recorder

# გვერდის კონფიგურაცია მობილურისთვის
st.set_page_config(
    page_title="Real-Time Voice Chat", 
    page_icon="🎤", 
    layout="centered"
)

# --- გლობალური მონაცემების შენახვა (Shared State) ---
@st.cache_resource
def get_global_data():
    # ეს მონაცემები საერთოა ყველა მომხმარებლისთვის
    return {
        "messages": [],
        "online_users": set()
    }

data = get_global_data()

# ავტომატური განახლება ყოველ 3 წამში (რომ ჩატი ცოცხალი იყოს)
st_autorefresh(interval=3000, key="datarefresh")

# სესიის მართვა (ლოკალური მომხმარებელი)
if "username" not in st.session_state:
    st.session_state.username = None

# --- რეგისტრაციის ფორმა ---
if st.session_state.username is None:
    st.title("ჩატში შესვლა 💬")
    with st.form("login_form"):
        name = st.text_input("შეიყვანეთ თქვენი სახელი:", placeholder="მაგ: გიორგი")
        submit = st.form_submit_button("შესვლა")
        
        if submit and name:
            st.session_state.username = name
            data["online_users"].add(name)
            st.rerun()
        elif submit and not name:
            st.error("გთხოვთ, ჩაწეროთ სახელი.")
else:
    # --- ჩატის მთავარი ინტერფეისი ---
    
    # ზედა პანელი სტატისტიკით
    st.markdown(f"### 💬 საერთო ოთახი")
    st.write(f"🟢 ონლაინ: **{len(data['online_users'])}**")
    
    with st.expander("ნახე ვინ არის აქ"):
        st.write(", ".join(data["online_users"]))

    st.divider()

    # შეტყობინებების ჩვენების არე
    chat_container = st.container()

    with chat_container:
        for msg in data["messages"]:
            with st.chat_message(msg["user"]):
                st.write(f"**{msg['user']}** | `{msg['time']}`")
                if msg["type"] == "text":
                    st.write(msg["content"])
                elif msg["type"] == "audio":
                    st.audio(msg["content"], format="audio/wav")

    # --- შეტყობინების გაგზავნის სექცია ---
    
    # 1. ტექსტური ინპუტი
    if prompt := st.chat_input("დაწერე შეტყობინება..."):
        data["messages"].append({
            "user": st.session_state.username,
            "type": "text",
            "content": prompt,
            "time": datetime.now().strftime("%H:%M")
        })
        st.rerun()

    # 2. ხმოვანი შეტყობინება (მოთავსებულია Sidebar-ში ან ბოლოში)
    st.sidebar.markdown("### 🎤 ხმოვანი ჩანაწერი")
    audio = mic_recorder(
        start_prompt="ჩაწერა 🎙️",
        stop_prompt="გაგზავნა ✅",
        key='recorder',
        use_recorder=True
    )

    if audio:
        audio_bytes = audio['bytes']
        # ვამოწმებთ, რომ ბოლო შეტყობინება იგივე აუდიო არ იყოს (დუბლირების თავიდან ასაცილებლად)
        if not data["messages"] or data["messages"][-1].get("content") != audio_bytes:
            data["messages"].append({
                "user": st.session_state.username,
                "type": "audio",
                "content": audio_bytes,
                "time": datetime.now().strftime("%H:%M")
            })
            st.rerun()

    # გასვლის ღილაკი
    if st.sidebar.button("ჩატიდან გასვლა"):
        if st.session_state.username in data["online_users"]:
            data["online_users"].remove(st.session_state.username)
        st.session_state.username = None
        st.rerun()
