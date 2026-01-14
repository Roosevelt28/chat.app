import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# გვერდის კონფიგურაცია მობილურისთვის
st.set_page_config(page_title="Real-Time Chat", page_icon="💬", layout="centered")

# --- გლობალური მონაცემების შენახვა ---
@st.cache_resource
def get_global_data():
    return {"messages": [], "online_users": set()}

data = get_global_data()

# ავტომატური განახლება ყოველ 2 წამში
st_autorefresh(interval=2000, key="datarefresh")

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
    st.write(f"🟢 ონლაინ: **{len(data['online_users'])}**")
    
    with st.expander("ვინ არის ონლაინ?"):
        st.write(", ".join(data["online_users"]))

    # შეტყობინებები
    for msg in data["messages"]:
        with st.chat_message(msg["user"]):
            st.write(f"**{msg['user']}** `{msg['time']}`")
            st.write(msg["text"])

    # შეტყობინების გაგზავნა
    if prompt := st.chat_input("დაწერე შეტყობინება..."):
        new_msg = {
            "user": st.session_state.username,
            "text": prompt,
            "time": datetime.now().strftime("%H:%M")
        }
        data["messages"].append(new_msg)
        if len(data["messages"]) > 50: data["messages"].pop(0)
        st.rerun()