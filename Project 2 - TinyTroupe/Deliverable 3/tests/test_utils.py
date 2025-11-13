import sys
import os

# This magic line adds your main app folder to the Python path
# so we can import 'utils' from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import extract_python_code

def test_code_extractor_basic():
    """Tests that the extractor can pull a simple code block."""
    text = """
    Hello, here is some code:
    ```python
    print("Hello")
    ```
    And some more text.
    """
    expected = 'print("Hello")'
    assert extract_python_code(text) == expected

def test_code_extractor_no_code():
    """Tests that it returns None if no code is found."""
    text = "This is just text. No code here."
    assert extract_python_code(text) is None

def test_code_extractor_multiple_lines():
    """Tests a multi-line code block."""
    code = """
import pandas as pd

df = pd.read_csv("data.csv")
"""
    text = f"Here is data analysis:\n```python\n{code}\n```"
    assert extract_python_code(text) == code.strip()