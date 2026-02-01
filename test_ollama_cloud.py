# import os
# from ollama import Client

# client = Client(
#     host="https://ollama.com",
#     headers={'Authorization': 'Bearer ' + "1e2fa8fdacc84de7b504741e0a2a2a7b.-Ar-eKGHM4pnbwwHZ5vSc1xv"}
# )

# messages = [
#   {
#     'role': 'user',
#     'content': 'Why is the sky blue?',
#   },
# ]

# for part in client.chat('gpt-oss:120b', messages=messages, stream=True):
#   print(part['message']['content'], end='', flush=True)


import asyncio
from langchain_ollama import ChatOllama
from config.settings import settings
from langchain_core.messages import HumanMessage

import base64

with open("images/remmina_10.0.1.205_10.0.1.205_20250929-022529.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

msg = HumanMessage(
    content=[
        {"type": "text", "text": "Ảnh này có gì?"},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{b64}"
            },
        },
    ]
)

async def main():
    llm = ChatOllama(
        model="gpt-oss:120b-cloud",
        base_url="https://ollama.com",
        client_kwargs={
            "headers": {
                "Authorization": f"Bearer {settings.OLLAMA_KEY}"
            },
            "timeout": 120,
        },
        temperature=0,
       
    )
    
    llm_ollama_kimi = ChatOllama(
    model="kimi-k2.5:cloud",
    base_url="https://ollama.com",
    client_kwargs={
        "headers": {
            "Authorization": f"Bearer {settings.OLLAMA_KEY}"
        },
        "timeout": 120,
    },
    temperature=0,

)
        

    async for chunk in llm_ollama_kimi.astream([msg]):
        if chunk.content:
            print(chunk.content, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
