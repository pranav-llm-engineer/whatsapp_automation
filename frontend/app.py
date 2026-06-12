import streamlit as st
import httpx
import time

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Cowork Assistant", page_icon="🏢")

def login_user(phone, password):
    try:
        response = httpx.post(f"{API_URL}/auth/login", json={"phone": phone, "password": password})
        if response.status_code == 200:
            st.session_state["session_token"] = response.json()["access_token"]
            st.session_state["user_id"] = response.json()["user_id"]
            st.success("Logged in successfully!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error(response.json().get("detail", "Login failed"))
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

def register_user(phone, password):
    try:
        response = httpx.post(f"{API_URL}/auth/register", json={"phone": phone, "password": password})
        if response.status_code == 200:
            st.success("Registered successfully! Please log in.")
        else:
            st.error(response.json().get("detail", "Registration failed"))
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

def get_profile():
    if "session_token" not in st.session_state:
        return None
    try:
        response = httpx.get(f"{API_URL}/auth/me?session_id={st.session_state['session_token']}")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def fetch_history():
    try:
        response = httpx.get(f"{API_URL}/chat/history?session_id={st.session_state['session_token']}")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

def send_message(msg):
    try:
        with st.spinner("Khushi is typing..."):
            res = httpx.post(f"{API_URL}/chat/", json={
                "session_id": st.session_state["session_token"],
                "message": msg
            }, timeout=60)
            if res.status_code == 200:
                data = res.json()
                st.session_state["last_context"] = data.get("context", "")
                st.rerun()
            else:
                st.error("Failed to send message")
    except Exception as e:
        st.error(f"Network error: {e}")

if "session_token" not in st.session_state:
    st.title("🏢 Cowork Assistant Login")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        login_phone = st.text_input("Phone Number", key="login_phone")
        login_password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            login_user(login_phone, login_password)
            
    with tab2:
        st.subheader("Register")
        reg_phone = st.text_input("Phone Number", key="reg_phone")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        if st.button("Register"):
            register_user(reg_phone, reg_password)
            
else:
    profile = get_profile()
    st.sidebar.title("🏢 CoworkBot")
    if st.sidebar.button("Logout"):
        del st.session_state["session_token"]
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.subheader("🛠️ Database Viewer")
    show_db = st.sidebar.checkbox("Show Database Explorer")
    if show_db:
        import sqlite3
        try:
            conn = sqlite3.connect("backend/db/cowork.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall() if not t[0].startswith("sqlite_")]
            
            selected_table = st.sidebar.selectbox("Select Table", tables)
            if selected_table:
                cursor.execute(f"PRAGMA table_info({selected_table});")
                columns = [col[1] for col in cursor.fetchall()]
                cursor.execute(f"SELECT * FROM {selected_table};")
                rows = cursor.fetchall()
                
                st.sidebar.write(f"Total Rows: {len(rows)}")
                
                # Show in main page if selected
                st.markdown(f"### 🗄️ Database Table: `{selected_table}`")
                if rows:
                    data = [dict(zip(columns, row)) for row in rows]
                    st.dataframe(data, use_container_width=True)
                else:
                    st.info(f"Table `{selected_table}` is currently empty.")
            conn.close()
        except Exception as e:
            st.sidebar.error(f"Error loading database: {e}")
        
    if profile:
        st.title("Chat with Khushi")
        if profile.get("onboarding_complete"):
            st.success("✅ Lead details successfully captured!")
            st.markdown("### Ready to Submit to CRM")
            
            payload = {
                "customerName": profile.get("full_name"),
                "mobileNumber": profile.get("phone"),
                "source": "organic_website",
                "spaceType": profile.get("spaceType"),
                "seatRangeMin": profile.get("seatRangeMin"),
                "seatRangeMax": profile.get("seatRangeMax"),
                "urgency": profile.get("urgency"),
                "location": profile.get("location"),
                "spaceId": 1
            }
            
            with st.expander("View JSON Payload for /public/leads API", expanded=True):
                st.json(payload)
                
            st.info("🔄 Your lead details are automatically synced to our CRM!")
        elif profile.get("onboarding_active"):
            st.info(f"Onboarding Mode Active | Next field: {profile.get('onboarding_step')}")
            
            # Simple progress approximation
            fields = ["full_name", "spaceType", "seatRange", "location"]
            try:
                idx = fields.index(profile.get("onboarding_step"))
                progress = (idx / len(fields))
                st.progress(progress)
            except:
                pass
        else:
            st.success("General Chat Mode Active")
            
        history = fetch_history()
        for msg in history:
            with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                st.markdown(msg["content"])
                
        if "last_context" in st.session_state and st.session_state["last_context"]:
            with st.expander("🔍 View Retrieved Knowledge Base Context"):
                st.markdown(st.session_state["last_context"])
                
        # Audio input for voice notes
        audio_val = st.audio_input("Record a voice message")
        if audio_val:
            import hashlib
            audio_hash = hashlib.md5(audio_val.getvalue()).hexdigest()
            
            # Only process if we haven't already processed this exact audio snippet
            if st.session_state.get("last_audio_hash") != audio_hash:
                with st.chat_message("user"):
                    st.audio(audio_val)
                    st.markdown("*(Voice Note)*")
                
                with st.spinner("Transcribing..."):
                    res = httpx.post(
                        f"{API_URL}/chat/transcribe/", 
                        files={"file": ("audio.wav", audio_val, "audio/wav")}
                    )
                    if res.status_code == 200:
                        transcript = res.json().get("transcript", "")
                        if transcript:
                            st.info(f"You said: {transcript}")
                            # Mark as processed BEFORE sending message to avoid loop on rerun
                            st.session_state["last_audio_hash"] = audio_hash
                            send_message(transcript)
                        else:
                            st.error("Could not transcribe audio.")
                    else:
                        st.error("Transcription failed.")

        if user_input := st.chat_input("Type a message..."):
            with st.chat_message("user"):
                st.markdown(user_input)
            send_message(user_input)
            
    else:
        st.error("Failed to load profile. Please login again.")
        if st.button("Logout"):
            del st.session_state["session_token"]
            st.rerun()
