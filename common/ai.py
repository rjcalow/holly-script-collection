import ollama
# Example usage:
remote_ollama_ip = "100.105.81.22"  # Replace with your remote server's IP.
model = "gemma3:1b"  # Replace with the model you want to use.



def setup_remote_ollama(remote_host):
    """
    Initializes a connection to the remote Ollama server once and returns a client object.

    Args:
        remote_host (str): The IP address or hostname of the remote Ollama server.

    Returns:
        ollama.Client: An Ollama client object, or None if connection fails.
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

    Args:
        client (ollama.Client): The Ollama client object.
        model_name (str): The name of the model to use.
        prompt (str): The prompt to send to the model.

    Returns:
        str: The generated response, or None if an error occurred.
    """
    if client is None:
        return None  # Client object not initialized

    try:
        response = client.generate(model=model_name, prompt=prompt)
        return response['response']
    except Exception as e:
        print(f"Error querying Ollama: {e}")
        return None



def ai_on_pi(q):
    return str(query_remote_ollama(ollama_client, model, q))
    