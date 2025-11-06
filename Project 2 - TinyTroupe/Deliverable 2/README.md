Data Science Agent Prototype

This project uses the TinyTroupe package to create a multi-layer AI agent system for data science and analysis. You can chat with a "DataScience_Solver" agent that can answer questions, suggest analytical models (like linear regression or decision trees), and write complete Python scripts to help you.

Project Structure

.
├── .gitignore        # Tells Git to ignore config.py (to keep your key secret)
├── config.py         # <-- YOU MUST CREATE THIS FILE for your API key
├── main.py           # The main application code
├── README.md         # This file
└── requirements.txt  # List of Python dependencies


🛠️ Setup and Installation

1. Clone the Repository

Clone this project to your local machine:

git clone <your-repo-url>
cd <your-repo-directory>


2. Create a Virtual Environment (Recommended)

This keeps your project's dependencies separate from your system.

# For macOS / Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate


3. Install Dependencies

Install all the required Python packages from requirements.txt:

pip install -r requirements.txt


4. Set Your API Key (CRITICAL STEP)

This project requires an OpenAI API key.

Create a new file in the project folder named config.py.

Open this file and add the following line, pasting your secret key inside the quotes:

OPENAI_API_KEY = "sk-YOUR_SECRET_API_KEY_GOES_HERE"


Save the file. The .gitignore file is already set up to prevent this file from ever being committed to GitHub.

🚀 How to Run

With your virtual environment active and your API key set in config.py, simply run the main script from your terminal:

python main.py


💡 How to Use

The script will start and ask you what you want to accomplish.

You can ask the "DataScience_Solver" agent for help.

Example Prompt: "I have a CSV file called housing.csv. It has square_footage and sale_price. Can you help me find out if I can predict the price based on the size?"

The agent will respond and, if you ask it to write code, will provide a complete script.

Any code the agent writes will be automatically saved to a file named generated_solution.py in the same folder.

Type brainstorm if you want the agent to think more creatively with a "Specialist" agent.

Type stop or quit to end the session.