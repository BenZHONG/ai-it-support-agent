from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(timeout=30.0)

response = client.responses.create(
    model="gpt-6-luna",
    instructions="You are a helpful IT support assistant.",
    input="What is a Wi-Fi adapter?",
    store=False,
)

print(response.output_text)
