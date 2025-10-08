import os
import uuid
import time
import streamlit as st
from google.protobuf.json_format import MessageToDict
from utils.dialogflow_helper import detect_intent_with_payload
from dotenv import load_dotenv
# --------------------------------------------------------------------------------
# Page Configuration & Setup
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title="KCE College Enquiry Chatbot",
    page_icon="🎓",
    layout="centered"
)

# Constants & Environment Setup
load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
PROJECT_ID = os.getenv("PROJECT_ID")

# Check for credentials
if not os.path.exists(SERVICE_ACCOUNT_FILE):
    st.error(f"Credentials file '{SERVICE_ACCOUNT_FILE}' not found.")
    st.stop()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE

# Check for credentials and set environment variable
if not os.path.exists(SERVICE_ACCOUNT_FILE):
    st.error(f"Credentials file '{SERVICE_ACCOUNT_FILE}' not found.")
    st.stop()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE

# --------------------------------------------------------------------------------
# Session State Initialization
# --------------------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = [] # Will store all chat messages

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
    """
    Calls Dialogflow and returns the bot's text and any quick replies.
    This function no longer modifies session state directly.
    """
    if not user_input.strip():
        return "", []

    try:
        df_response = detect_intent_with_payload(PROJECT_ID, st.session_state.session_id, user_input)
        if df_response is None:
            return "⚠️ Sorry, I'm having connection issues.", []
            
        response_dict = MessageToDict(df_response.query_result._pb)
        bot_text = response_dict.get('fulfillmentText', "I'm not sure how to respond to that.")
        
        # Safely extract quick replies
        quick_replies = []
        try:
            payload = response_dict.get('fulfillmentMessages', [])[1]['payload']['richContent'][0][0]['options']
            quick_replies = [item['text'] for item in payload]
        except (KeyError, IndexError, TypeError):
            pass # It's okay if there are no quick replies
            
        return bot_text, quick_replies
        
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return "⚠️ An error occurred while processing your request.", []

# --------------------------------------------------------------------------------
# Main Chat Interface
# --------------------------------------------------------------------------------
st.title("🎓 KCE College Enquiry Chatbot")

# Display previous chat messages from history
for message in st.session_state.messages:
    avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        # Display quick replies if they were part of this bot message
        if message.get("quick_replies"):
            cols = st.columns(len(message["quick_replies"]))
            for i, option in enumerate(message["quick_replies"]):
                if cols[i].button(option, key=f"quick_{message['content']}_{i}", use_container_width=True):
                    # When a quick reply is clicked, it becomes the new user input
                    st.session_state.user_input = option
                    st.rerun()

# This is the main input handler
if prompt := st.chat_input("What would you like to ask?"):
    st.session_state.user_input = prompt

# This block executes when st.session_state.user_input is set (either by chat_input or a quick reply button)
if "user_input" in st.session_state and st.session_state.user_input:
    # Get the user input and clear it to prevent re-triggering
    user_input = st.session_state.user_input
    del st.session_state.user_input

    # Add user message to state and display it
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    # Show "Thinking..." spinner, then get the bot's response
    with st.spinner("Thinking..."):
        bot_text, quick_replies = process_and_get_response(user_input)

    # Display the bot's response with the typing effect
    with st.chat_message("assistant", avatar="🤖"):
        stream_response(bot_text)

    # Store the complete bot message with its quick replies in session state
    bot_message = {"role": "assistant", "content": bot_text}
    if quick_replies:
        bot_message["quick_replies"] = quick_replies
    st.session_state.messages.append(bot_message)

    st.rerun()

# Initial welcome message logic
if not st.session_state.messages:
    st.session_state.user_input = "Hi"
    st.rerun()