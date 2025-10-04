# main.py

import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI

# Import logic from other modules
from credibility_analyzer import analyze_credibility
from openai_handler import get_openai_response

# --- Initialization ---
# Load environment variables from .env file
load_dotenv()

# Initialize ONLY the OpenAI client
try:
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # Test if the key is valid by making a simple call. This prevents errors later.
    if not openai_client.api_key:
        raise ValueError("OpenAI API key is missing.")
except (ValueError, TypeError) as e:
    st.error(f"OpenAI API key not found or invalid. Please create a `.env` file and add your OPENAI_API_KEY. Error: {e}", icon="🚨")
    st.stop()

# --- Streamlit UI ---
st.set_page_config(page_title="Credibility Analyzer Bot", page_icon="🤖")
st.title("🤖 Credibility & Conversation Bot")

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! Paste a URL or article text for credibility analysis, or ask me anything else!"
    }]

for message in st.session_state.messages:
    # This check is simpler now but kept for consistency
    if message["role"] in ["user", "assistant"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("URL, text (>50 words for analysis), or a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking... 🤔"):
            # --- Router Logic ---
            is_url = prompt.strip().startswith(('http://', 'https://'))
            is_long_text = len(prompt.strip().split()) > 50

            if is_url or is_long_text:
                response = analyze_credibility(prompt)
            else:
                conversation_history = [msg for msg in st.session_state.messages if msg["role"] in ["user", "assistant"]]
                response = get_openai_response(conversation_history, openai_client)

        
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})