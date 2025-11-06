# ==========================================================
# IMPORTS
# ==========================================================
import json
import os
import textwrap
import re
from pprint import pprint

# --- TinyTroupe Imports ---
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.factory import TinyPersonFactory

# --- API Key Import ---
# We import the key from our separate, secret config.py file
try:
    from config import OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = ""

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def print_wrap(role, text):
    """Helper function to format and print chat text nicely."""
    wrapped_text = textwrap.fill(text, width=90, replace_whitespace=False)
    print(f"\n[{role}]:\n{wrapped_text}\n")

def extract_python_code(text: str) -> str | None:
    """Extracts Python code from a Markdown code block."""
    match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def save_to_file(filename: str, code: str):
    """Saves the given code to a file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
        print_wrap("System", f"✅ Success! Python code extracted and saved to '{filename}'.")
    except Exception as e:
        print_wrap("System", f"🚨 Error: Could not save file. {e}")

# ==========================================================
# AGENT PERSONA DEFINITIONS
# ==========================================================

greeter_persona = {
    "type": "TinyPerson",
    "persona": {
        "name": "Greeter",
        "occupation": {
            "title": "Expert in TinyTroupe",
            "description": "You are knowledgeable about the TinyTroupe package and agent creation. Your role is to ask the user 1-2 questions to understand their needs and then generate a JSON config for the next agent."
        },
        "personality": {
            "traits": ["Helpful", "Concise", "Friendly", "Collaborative"]
        }
    }
}

specialist_persona = {
    "type": "TinyPerson",
    "persona": {
        "name": "Specialist",
        "occupation": {
            "title": "Creative Problem Solver",
            "description": "You are an expert in brainstorming and agentic design. You are called in to help a 'Solver' agent. Your goal is to collaborate with the Solver to find a creative solution for the user's problem. You provide guidance and new perspectives."
        },
        "personality": {
            "traits": ["Creative", "Analytical", "Collaborative", "Insightful"]
        }
    }
}

# ==========================================================
# MAIN PROTOTYPE FUNCTION
# ==========================================================

def run_prototype():
    """
    Runs the main 3-layer agent chat prototype.
    """
    # Clear existing agents for clean re-runs
    TinyPerson.all_agents = {}

    # --- Check for API Key ---
    if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_API_KEY_HERE":
        print("🚨 ERROR: API Key not found.")
        print("Please create a 'config.py' file and add your OpenAI API Key to it.")
        print("Example: OPENAI_API_KEY = 'sk-...'")
        return
    
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    print("✅ OpenAI API Key has been set from config.py.")

    # --- LAYER 1: The Greeter ---
    print_wrap("System", "Layer 1 Initialized. Connecting to Greeter...")
    greeter_agent = TinyPerson(name=greeter_persona["persona"]["name"])

    print_wrap(greeter_agent.name, "Hello! I'm an expert in TinyTroupe. To help you, I just need to ask 1-2 questions. What are you hoping to accomplish today?")

    user_input = input("You > ")
    print_wrap("You", user_input)

    print_wrap("System", "Bypassing Greeter JSON generation and creating a Data Science Solver.")

    # --- ENHANCED: Code generation instructions with model suggestions ---
    code_generation_instructions = """
    You are an expert data scientist and Python programmer. Your goal is to help the user solve data analysis problems.

    **A key part of your role is to proactively suggest and build simple models to help the user understand their data.** This includes, but is not limited to:
    * **Linear Regression:** To find trends and relationships (e.g., "Does ad spend predict sales?").
    * **Decision Trees / Random Forest:** For classification or regression to visualize decision rules.
    * **Logistic Regression:** For classification problems (e.g., "Will this customer churn? Yes/No").
    * **K-Means Clustering:** To find natural groups in the data (e.g., "What are my customer segments?").

    When the user provides a problem, you should consider if one of these models can provide insight and suggest it.

    When the user asks you to write a script or create a file, you MUST respond with a brief explanation followed by the complete Python code.

    **You MUST format the code using standard Markdown, like this:**

    ```python
    # Your Python code starts here
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    
    def analyze_data(file_path):
        # ... rest of the code ...
        pass

    if __name__ == "__main__":
        analyze_data("data.csv")
    ```

    **Do not write any text after the final ``` code fence.**
    This is a critical instruction. If you are just chatting, you do not need to use this format.
    """

    # --- Configure the Solver Agent ---
    solver_config = {
        "type": "TinyPerson",
        "persona": {
            "name": "DataScience_Solver",
            "occupation": {
                "title": "Expert Data Scientist and Python Coder",
                "description": f"You are an assistant configured based on the user's request: '{user_input}'. Your base instructions are: {code_generation_instructions}"
            },
            "personality": {
                "traits": ["Analytical", "Precise", "Collaborative", "Helpful", "Code-oriented"]
            }
        }
    }
    print_wrap("System", f"Solver config generated:\n{json.dumps(solver_config, indent=2)}")

    # --- LAYER 2: The Solver ---
    print_wrap("System", "Layer 2 Initialized. Creating Solver agent...")
    factory = TinyPersonFactory(context="A technical support session for a Data Science student.")

    solver_agent = factory.generate_person(f"Create a solver agent with this spec: {solver_config}")

    if solver_agent is None:
        print_wrap("System", "Failed to create Solver agent using TinyPersonFactory.")
        return

    print_wrap(solver_agent.name, "Hello. I've been configured as a Data Science assistant. How can I help you proceed with your data analysis problem?")

    # --- Continuous conversation loop ---
    while True:
        user_input = input("You > ")
        print_wrap("You", user_input)

        if user_input.lower() in ["stop", "quit", "end"]:
            print_wrap("System", "Ending session.")
            break

        # --- Check for Escalation Trigger ---
        if "brainstorm" in user_input.lower():
            print_wrap(solver_agent.name, "That's an excellent idea. This requires a deeper, more creative approach. I'll bring in a specialist to help us brainstorm.")

            # --- LAYER 3: The Brainstorming ---
            print_wrap("System", "Layer 3 Initialized. Creating Specialist and Brainstorming World...")
            specialist_agent = TinyPerson(name=specialist_persona["persona"]["name"])
            brainstorm_world = TinyWorld(name="Brainstorm-Room", agents=[solver_agent, specialist_agent])

            topic = f"The user needs help with '{user_input}'. Let's brainstorm a creative and robust solution. {solver_agent.name}, you can provide the context, and {specialist_agent.name}, please provide the expert insight."
            print_wrap("System", f"Giving agents the topic: {topic}")

            brainstorm_world.broadcast(topic)
            print("\n--- 🧠 Agents are brainstorming... (This may take a moment) ---")
            brainstorm_world.run(4)
            print("--- ✅ Brainstorm Complete. Here is the transcript: ---\n")

            history = brainstorm_world.get_conversation_history()
            for message in history:
                if message["sender_name"] != "WORLD":
                    print_wrap(message['sender_name'], message['content'])

            print_wrap("System", "Returning to the main conversation with the Solver.")
        else:
            # --- Handle regular response and check for code ---
            solver_response = solver_agent.listen_and_act(user_input)
            if solver_response:
                print_wrap(solver_agent.name, solver_response)
                code_block = extract_python_code(solver_response)
                if code_block:
                    save_to_file("generated_solution.py", code_block)
            else:
                print_wrap("System", f"{solver_agent.name} did not provide a response.")

    print_wrap("System", "Session complete.")

# ==========================================================
# RUN THE SCRIPT
# ==========================================================
if __name__ == "__main__":
    run_prototype()