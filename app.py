import os
import uuid
import time
import json
import streamlit as st
from google.protobuf.json_format import MessageToDict
from utils.dialogflow_helper import detect_intent_with_payload
from dotenv import load_dotenv

# --------------------------------------------------------------------------------
# Page Configuration
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title="KCE College Enquiry Chatbot",
    page_icon="🎓",
    layout="centered"
)

# --------------------------------------------------------------------------------
# Universal Credentials and Project ID Setup (Robust Version)
# --------------------------------------------------------------------------------
try:
    # This block will run on Streamlit Community Cloud
    if 'gcp_creds' in st.secrets:
        PROJECT_ID = st.secrets.gcp_creds.project_id
        creds_json = dict(st.secrets.gcp_creds)
        creds_json["private_key"] = creds_json["private_key"].replace('\\n', '\n')
        
        with open("temp_creds.json", "w") as f:
            json.dump(creds_json, f)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "temp_creds.json"
    else:
        # This block will run locally if secrets.toml doesn't exist or is empty
        load_dotenv()
        PROJECT_ID = os.getenv("PROJECT_ID")
        SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not SERVICE_ACCOUNT_FILE or not os.path.exists(SERVICE_ACCOUNT_FILE):
            st.error("Local credentials not found. Check your .env file.")
            st.stop()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE

except st.errors.StreamlitAPIException as e:
    # This block handles the case where the app is run locally without a secrets.toml
    if "No secrets found" in str(e):
        load_dotenv()
        PROJECT_ID = os.getenv("PROJECT_ID")
        SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not SERVICE_ACCOUNT_FILE or not os.path.exists(SERVICE_ACCOUNT_FILE):
            st.error("Local credentials not found. Check your .env file.")
            st.stop()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
    else:
        raise e

# --------------------------------------------------------------------------------
# Session State Initialization
# --------------------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []

# (The rest of your code is perfect, no changes needed below this line)
# --------------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------------
def stream_response(text: str, delay: float = 0.02):
    """Displays text with a typing animation."""
    placeholder = st.empty()
    output = ""
    for char in text:
        output += char
        placeholder.markdown(output + "▌")
        time.sleep(delay)
    placeholder.markdown(output)
    return output

def process_and_get_response(user_input: str) -> tuple[str, list]:
    """Calls Dialogflow and returns the bot's text and any quick replies."""
    if not user_input.strip():
        return "", []

    try:
        df_response = detect_intent_with_payload(PROJECT_ID, st.session_state.session_id, user_input)
        if df_response is None:
            return "⚠️ Sorry, I'm having connection issues.", []
            
        response_dict = MessageToDict(df_response.query_result._pb)
        bot_text = response_dict.get('fulfillmentText', "I'm not sure how to respond to that.")
        
        quick_replies = []
        try:
            payload = response_dict.get('fulfillmentMessages', [])[1]['payload']['richContent'][0][0]['options']
            quick_replies = [item['text'] for item in payload]
        except (KeyError, IndexError, TypeError):
            pass
            
        return bot_text, quick_replies
        
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return f"⚠️ An error occurred while processing your request: {e}", []

# --------------------------------------------------------------------------------
# Main Chat Interface
# --------------------------------------------------------------------------------
st.title("🎓 KCE College Enquiry Chatbot")

# Display previous chat messages
for message in st.session_state.messages:
    avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message.get("quick_replies"):
            cols = st.columns(len(message["quick_replies"]))
            for i, option in enumerate(message["quick_replies"]):
                if cols[i].button(option, key=f"quick_{message['content']}_{i}", use_container_width=True):
                    st.session_state.user_input = option
                    st.rerun()

# Main input handler
if prompt := st.chat_input("What would you like to ask?"):
    st.session_state.user_input = prompt

# Execution block for new input
if "user_input" in st.session_state and st.session_state.user_input:
    user_input = st.session_state.user_input
    del st.session_state.user_input

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    with st.spinner("Thinking..."):
        bot_text, quick_replies = process_and_get_response(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        stream_response(bot_text)

    bot_message = {"role": "assistant", "content": bot_text}
    if quick_replies:
        bot_message["quick_replies"] = quick_replies
    st.session_state.messages.append(bot_message)
    st.rerun()

# Initial welcome message
if not st.session_state.messages:
    st.session_state.user_input = "Hi"
    st.rerun()