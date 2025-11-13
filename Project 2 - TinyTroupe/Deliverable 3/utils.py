import re

def extract_python_code(text: str) -> str | None:
    """Extracts Python code from a Markdown code block."""
    match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None