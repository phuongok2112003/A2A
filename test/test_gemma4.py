from langchain_ollama import ChatOllama
import asyncio
import base64
from pathlib import Path
import sys
from langchain_core.messages import HumanMessage
# Thêm project root vào sys.path để import absolute hoạt động
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from config.settings import settings
def encode_audio(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

audio_base64 = encode_audio("/home/x-phuong/Downloads/dung.mp3")
    

llm_ollama_gemma4 = ChatOllama(
    model="gemma4:31b-cloud",
    base_url="https://ollama.com",
    client_kwargs={
        "headers": {
            "Authorization": f"Bearer {settings.OLLAMA_KEY}"
        },
        "timeout": 120,
    },
    temperature=0,

)
async def main():
    response = await llm_ollama_gemma4.ainvoke(
    [
            HumanMessage(
                content="Tìm tôi thông tin về Jen husung CEO của NVIDIA."
            )
        ]

)
    print(response)

if __name__ == "__main__":
    asyncio.run(main())