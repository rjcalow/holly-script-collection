'''

ChagptGPT API Handler


'''

import openai
import sys
import os

# Get the absolute path to the directory containing holly.py
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
common_dir = os.path.join(base_dir, "common")
home_dir = os.path.expanduser("~")

# --- Secrets ---
from _secrets import chatgpt_key


openai.api_key = chatgpt_key # Replace or use os.getenv()

# Conversation memory per user (stores structured message format)
conversation_memory = {}

def ai_with_memory(user_id, query, model="gpt-4"):
    """
    Handles conversation with memory for a specific user/session using OpenAI API.
    """
    if user_id not in conversation_memory:
        conversation_memory[user_id] = []

    # Add user's message to memory
    conversation_memory[user_id].append({"role": "user", "content": query})

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=conversation_memory[user_id],
            temperature=0.7,
        )
        ai_reply = response.choices[0].message["content"].strip()

        # Add assistant's response to memory
        conversation_memory[user_id].append({"role": "assistant", "content": ai_reply})

        return ai_reply

    except Exception as e:
        print(f"Error querying OpenAI: {e}")
        return None

def ai_simple_task(prompt, model="gpt-4"):
    """
    Handles one-off tasks or summarization without maintaining conversation history.
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message["content"].strip()

    except Exception as e:
        print(f"Error querying OpenAI: {e}")
        return None
