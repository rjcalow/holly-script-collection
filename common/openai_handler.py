"""

ChatGPT API Handler
Devoid, but left here for future?
Using local ai handler for now.
16/5/2025

"""

import os
import sys
import logging
from openai import OpenAI

# --- Set up paths ---
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
home_dir = os.path.expanduser("~")

# Add base and home to sys.path for module resolution
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
if home_dir not in sys.path:
    sys.path.insert(0, home_dir)

# --- Logging ---
log_file = "/home/holly/errorlog.txt"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Secrets ---
try:
    from _secrets import chatgpt_key
except Exception as e:
    logging.error(f"Failed to import secrets: {e}")
    raise

# --- Initialize OpenAI client ---
client = OpenAI(api_key=chatgpt_key)

# In-memory conversation store per user
conversation_memory = {}

def ai_with_memory(user_id, query, model="gpt-3.5-turbo"):
    """
    Handles conversation with memory for a specific user/session using OpenAI SDK v1+.
    """
    if user_id not in conversation_memory:
        conversation_memory[user_id] = [
            {"role": "system", "content": "You are a helpful and concise AI assistant."}
        ]

    conversation_memory[user_id].append({"role": "user", "content": query})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=conversation_memory[user_id],
            temperature=0.7,
        )
        ai_reply = response.choices[0].message.content.strip()
        conversation_memory[user_id].append({"role": "assistant", "content": ai_reply})
        logging.info(f"Response to user {user_id}: {ai_reply}")
        return ai_reply

    except Exception as e:
        logging.error(f"Error querying OpenAI for user {user_id}: {e}")
        return None


def ai_simple_task(prompt, model="gpt-3.5-turbo"):
    """
    Handles one-off tasks or summarization using OpenAI SDK v1+.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        ai_reply = response.choices[0].message.content.strip()
        logging.info(f"Simple task response: {ai_reply}")
        return ai_reply

    except Exception as e:
        logging.error(f"Error querying OpenAI (simple task): {e}")
        return None


if __name__ == "__main__":
    print(ai_simple_task("What is the capital of France?"))
