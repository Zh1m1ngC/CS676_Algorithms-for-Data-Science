# openai_handler.py

from openai import OpenAI

def get_openai_response(messages, openai_client):
    """
    Handles conversational queries using the OpenAI model's internal knowledge.
    """
    # Make a simple API call without any tools
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    
    # Return the text content of the response
    return response.choices[0].message.content