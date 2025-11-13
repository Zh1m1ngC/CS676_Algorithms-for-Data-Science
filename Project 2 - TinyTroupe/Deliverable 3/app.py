# ==========================================================
# IMPORTS
# ==========================================================
import streamlit as st
import json
import os
import re
from pprint import pprint

# --- TinyTroupe Imports ---
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.factory import TinyPersonFactory

# --- Local Imports ---
from utils import extract_python_code
from agent_config import greeter_persona, specialist_persona, code_generation_instructions

# --- API Key Import ---
# We import the key from our separate, secret config.py file
try:
    from config import OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = ""

# ==========================================================
# STREAMLIT APP LOGIC
# ==========================================================

# --- Page Setup ---
st.set_page_config(page_title="Data Science Agent", layout="wide")
st.title("🤖 Data Science Agent Prototype")

# --- API Key Check ---
if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-YOUR_API_KEY_GOES_HERE":
    st.error("🚨 API Key not found.")
    st.error("Please create a 'config.py' file and add your OpenAI API Key to it.")
    st.info("After adding the key, you may need to restart the app.")
    st.stop()
else:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# --- Agent Initialization in Session State ---
# This ensures agents persist across Streamlit script reruns
if "greeter_agent" not in st.session_state:
    TinyPerson.all_agents = {} # Clear class-level agents
    st.session_state.greeter_agent = TinyPerson(name=greeter_persona["persona"]["name"])
if "solver_agent" not in st.session_state:
    st.session_state.solver_agent = None
if "specialist_agent" not in st.session_state:
    st.session_state.specialist_agent = None

# --- Chat History Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.layer = "greeter" # Start with the greeter
    # Add the greeter's first message
    st.session_state.messages.append({
        "role": "assistant", 
        "name": "Greeter", 
        "content": "Hello! I'm an expert in TinyTroupe. To help you, I just need to ask 1-2 questions. What are you hoping to accomplish today?"
    })

# --- Display Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
        st.markdown(f"**{msg.get('name', msg['role'].title())}**")
        st.markdown(msg["content"])

# --- Handle User Input ---
if prompt := st.chat_input("What would you like to do?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "name": "You", "content": prompt})
    st.chat_message("user", avatar="🧑‍💻").markdown("**You**").markdown(prompt)

    # === LAYER 1: GREETER LOGIC ===
    if st.session_state.layer == "greeter":
        # The user's prompt is the answer to the greeter
        # Now, we configure and introduce the Solver
        st.session_state.layer = "solver"
        
        with st.spinner("Configuring Data Science Solver..."):
            solver_config = {
                "type": "TinyPerson",
                "persona": {
                    "name": "DataScience_Solver",
                    "occupation": {
                        "title": "Expert Data Scientist and Python Coder",
                        "description": f"You are an assistant configured based on the user's request: '{prompt}'. Your base instructions are: {code_generation_instructions}"
                    },
                    "personality": {
                        "traits": ["Analytical", "Precise", "Collaborative", "Helpful", "Code-oriented"]
                    }
                }
            }
            
            factory = TinyPersonFactory(context="A technical support session for a Data Science student.")
            st.session_state.solver_agent = factory.generate_person(f"Create a solver agent with this spec: {solver_config}")
        
        # Add solver's intro message
        solver_intro = "Hello. I've been configured as a Data Science assistant based on your goal. How can I help you proceed with your data analysis problem?"
        st.session_state.messages.append({"role": "assistant", "name": "DataScience_Solver", "content": solver_intro})
        st.chat_message("assistant", avatar="🤖").markdown("**DataScience_Solver**").markdown(solver_intro)
        st.rerun() # Rerun to show the new message and wait for next input

    # === LAYER 2: SOLVER LOGIC ===
    elif st.session_state.layer == "solver":
        
        # --- Check for Brainstorm Trigger ---
        if "brainstorm" in prompt.lower():
            st.session_state.layer = "brainstorm" # Change state
            
            # Add solver's handoff message
            solver_handoff = "That's an excellent idea. This requires a deeper, more creative approach. I'll bring in a specialist to help us brainstorm."
            st.session_state.messages.append({"role": "assistant", "name": "DataScience_Solver", "content": solver_handoff})
            
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown("**DataScience_Solver**")
                st.markdown(solver_handoff)

            # --- Run Brainstorm ---
            with st.spinner("🧠 Agents are brainstorming... (This may take a moment)"):
                if st.session_state.specialist_agent is None:
                    st.session_state.specialist_agent = TinyPerson(name=specialist_persona["persona"]["name"])
                
                brainstorm_world = TinyWorld(
                    name="Brainstorm-Room",
                    agents=[st.session_state.solver_agent, st.session_state.specialist_agent]
                )

                topic = f"The user needs help with '{prompt}'. Let's brainstorm a creative and robust solution."
                brainstorm_world.broadcast(topic)
                brainstorm_world.run(4) # Run 4 turns
                
                history = brainstorm_world.get_conversation_history()
                
                # Add brainstorm transcript to chat
                st.session_state.messages.append({"role": "assistant", "name": "System", "content": "--- ✅ Brainstorm Complete. Transcript: ---"})
                st.chat_message("assistant", avatar="🤖").markdown("**System**").markdown("--- ✅ Brainstorm Complete. Transcript: ---")
                
                for msg in history:
                    if msg["sender_name"] != "WORLD":
                        b_msg = f"**{msg['sender_name']}**: {msg['content']}"
                        st.session_state.messages.append({"role": "assistant", "name": msg['sender_name'], "content": msg['content']})
                        st.chat_message("assistant", avatar="🤖").markdown(f"**{msg['sender_name']}**").markdown(msg['content'])

            # Return to solver
            st.session_state.layer = "solver"
            st.session_state.messages.append({"role": "assistant", "name": "System", "content": "--- Returning to conversation. ---"})
            st.chat_message("assistant", avatar="🤖").markdown("**System**").markdown("--- Returning to conversation. ---")
            st.rerun()

        # --- Regular Solver Response ---
        else:
            with st.spinner("DataScience_Solver is thinking..."):
                solver_response = st.session_state.solver_agent.listen_and_act(prompt)
                
                if solver_response:
                    # Add full text response
                    st.session_state.messages.append({"role": "assistant", "name": "DataScience_Solver", "content": solver_response})
                    
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown("**DataScience_Solver**")
                        st.markdown(solver_response)
                        
                        # --- Handle Code Blocks ---
                        code_block = extract_python_code(solver_response)
                        if code_block:
                            st.info("💡 Agent provided a code snippet:")
                            st.code(code_block, language="python")
                else:
                    solver_response = "I'm not sure how to respond to that."
                    st.session_state.messages.append({"role": "assistant", "name": "DataScience_Solver", "content": solver_response})
                    st.chat_message("assistant", avatar="🤖").markdown("**DataScience_Solver**").markdown(solver_response)