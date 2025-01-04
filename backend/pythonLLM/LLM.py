import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment variable
api_key = os.getenv("HUGGINGFACE_API")

# Initialize the InferenceClient with the API key
client = InferenceClient(api_key=api_key)

def get_response(messages):
    completion = client.chat.completions.create(
        model="Qwen/Qwen2.5-Coder-32B-Instruct", 
        messages=messages, 
        max_tokens=500
    )
    return completion.choices[0].message['content']