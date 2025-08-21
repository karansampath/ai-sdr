# In your terminal, first run:
# pip install xai-sdk

import os
from dotenv import load_dotenv

from xai_sdk import Client
from xai_sdk.chat import user, system

# Load environment variables from .env file
load_dotenv()
client = Client(
    api_key=os.getenv("XAI_API_KEY"),
    timeout=3600,  # Override default timeout with longer timeout for reasoning models
)

chat = client.chat.create(model="grok-4")
chat.append(system("You are Grok, a highly intelligent, helpful AI assistant."))
chat.append(user("What is the meaning of life, the universe, and everything?"))

response = chat.sample()
print(response.content)