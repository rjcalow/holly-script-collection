'''

ChagptGPT API Handler


'''

from openai import OpenAI
import sys
import os

# Get the absolute path to the directory containing holly.py
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
common_dir = os.path.join(base_dir, "common")
home_dir = os.path.expanduser("~")

# --- Secrets ---
from _secrets import chatgpt_key


# Initialize OpenAI client with API key from environment
client = OpenAI(api_key=chatgpt_key)

# In-memory conversation store per user
conversation_memory = {}

def ai_with_memory(user_id, query, model="gpt-4"):
    """
    Handles conversation with memory for a specific user/session using OpenAI SDK v1+.
    """
    if user_id not in conversation_memory:
        # You can customize the assistant's persona using a system prompt
        conversation_memory[user_id] = [
            {"role": "system", "content": "You are a helpful and concise AI assistant."}
        ]

    # Add the user's message
    conversation_memory[user_id].append({"role": "user", "content": query})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=conversation_memory[user_id],
            temperature=0.7,
        )
        ai_reply = response.choices[0].message.content.strip()

        # Add AI's response to the conversation memory
        conversation_memory[user_id].append({"role": "assistant", "content": ai_reply})

        return ai_reply

    except Exception as e:
        print(f"Error querying OpenAI: {e}")
        return None


def ai_simple_task(prompt, model="gpt-4"):
    """
    Handles one-off tasks or summarization using OpenAI SDK v1+.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error querying OpenAI: {e}")
        return None


