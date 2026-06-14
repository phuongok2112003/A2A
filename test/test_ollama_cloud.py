# import os
# from ollama import Client

# client = Client(
#     host="https://ollama.com",
#     headers={'Authorization': 'Bearer ' + os.environ["OLLAMA_KEY"]}
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
from langchain_openai import ChatOpenAI
from config.settings import settings
from langchain_core.messages import HumanMessage

import base64

with open("images/remmina_10.0.1.205_10.0.1.205_20250929-022529.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

msg = HumanMessage(
    content=[
        {"type": "text", "text": "Tai sao troi xanh?"},
        # {
        #     "type": "image_url",
        #     "image_url": {
        #         "url": f"data:image/png;base64,{b64}"
        #     },
        # },
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
    llm_openai = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.2,
        openai_api_key=settings.OPENAI_A2A_API_KEY,
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
        

    async for chunk in llm_openai.astream([msg]):
        if chunk.content:
            print(chunk.content, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
