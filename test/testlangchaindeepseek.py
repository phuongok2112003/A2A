import asyncio
import os

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

async def main():
    # model = ChatOpenAI(
    #     model="o3",
    #     base_url="http://localhost:6011/v1",
    #     api_key="sk-local-phuong-001"
    # )
    # model = ChatOpenAI(
    #     model="nemotron-3-super:cloud",
    #     temperature=0.2,
    #     api_key=os.environ["OLLAMA_KEY"],
    #     base_url="https://ollama.com/v1"
    # )

    model = ChatOllama(
        model="nemotron-3-super:cloud",
        base_url="https://ollama.com/v1",
        client_kwargs={
            "headers": {
                "Authorization": f"Bearer {os.environ['OLLAMA_KEY']}"
            },
            "timeout": 120,
        },
        temperature=0,
    )
    messages = [HumanMessage(content="Giải thích định luật vạn vật hấp dẫn.")]
    
    # Ở đây chúng ta dùng astream để xem từng phần. 
    # Nhưng vì API của bạn trả về reasoning_content trong cùng 1 message object (không phải dạng block chuẩn),
    # việc dùng astream truyền thống có thể không cho thấy reasoning_content "đang chạy" nếu server không stream trường đó.
    
    # CÁCH LẤY DỮ LIỆU TỪ SERVER CỦA BẠN:
    response = await model.ainvoke(messages)
    
    # Kiểm tra trong additional_kwargs (nơi LangChain lưu các trường lạ từ API)
    # hoặc kiểm tra trực tiếp thuộc tính tùy chỉnh nếu thư viện hỗ trợ
    reasoning = response.additional_kwargs.get("reasoning_content")
    
    if reasoning:
        print(f"[thinking] {reasoning}")
    
    print(f"[text] {response.content}")

if __name__ == "__main__":
    asyncio.run(main())
