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

    async for chunk in llm.astream("Tôi muốn tìm hiểu về LangChain"):
        if chunk.content:
            print(chunk.content, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
