import ollama

# Example usage:
remote_ollama_ip = "127.0.0.1"  # Replace with your remote server's IP.
model = "gemma3:4b"  # Replace with the model you want to use.

def setup_remote_ollama(remote_host):
    """
    Initializes a connection to the remote Ollama server once and returns a client object.
    """
    try:
        client = ollama.Client(host=f'http://{remote_host}:11434')
        return client
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return None

# Initialize the connection once:
ollama_client = setup_remote_ollama(remote_ollama_ip)

def query_remote_ollama(client, model_name, prompt):
    """
    Queries the remote Ollama server using the provided client object.
    """
    if client is None:
        return None  # Client object not initialized

    try:
        response = client.generate(model=model_name, prompt=prompt)
        return response['response']
    except Exception as e:
        print(f"Error querying Ollama: {e}")
        return None

# Conversation memory storage
conversation_memory = {}

def ai_with_memory(user_id, query):
    """
    Handles conversation with memory for a specific user/session.
    """
    if user_id not in conversation_memory:
        conversation_memory[user_id] = []

    # Append the user's query to the conversation history
    conversation_memory[user_id].append(f"User: {query}")

    # Generate a prompt with the conversation history
    conversation_history = "\n".join(conversation_memory[user_id])
    prompt = f"{conversation_history}\nAI:"

    # Query the AI
    response = query_remote_ollama(ollama_client, model, prompt)

    if response:
        # Append the AI's response to the conversation history
        conversation_memory[user_id].append(f"AI: {response}")

    return response

def ai_simple_task(prompt):
    """
    Handles one-off tasks or summarization without maintaining conversation history.
    """
    return query_remote_ollama(ollama_client, model, prompt)

# Example usage:
# For conversation with memory:
# response = ai_with_memory(user_id="user123", query="Hello, how are you?")
# For simple tasks:
# summary = ai_simple_task(prompt="Summarize this text: ...")