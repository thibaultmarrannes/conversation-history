
import os
import openai
from dotenv import load_dotenv

def call_openai(prompt: str) -> str:
    load_dotenv()
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def get_embedding(text: str) -> list:
    """
    Generate an embedding vector for the given text using OpenAI's embedding API.
    Returns a list of floats (the embedding vector).
    """
    load_dotenv()
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding
