
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
