from openai import OpenAI
from langchain_openai import ChatOpenAI
import asyncio
from langchain_core.messages import HumanMessage
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent

# client = OpenAI(
#     base_url="http://127.0.0.1:6011/v1",
#     api_key="sk-local-phuong-001",
# )

# stream = client.chat.completions.create(
#     model="deepseek-v4-pro-search",
#     messages=[
#         {
#             "role": "user",
#             "content": "Tôi muốn bạn liệt kê cho tôi các cuộc thi hackathon AI ở Việt Nam trong năm nay, kèm theo thông tin về thời gian, địa điểm, giải thưởng và cách thức đăng ký tham gia."
#         }
#     ],
#     stream=True,
# )

# thinking_started = False
# answer_started = False

# for chunk in stream:
#     delta = chunk.choices[0].delta

#     reasoning = getattr(delta, "reasoning_content", None)

#     if reasoning:
#         if not thinking_started:
#             print("\n========== THINKING ==========\n")
#             thinking_started = True

#         print(reasoning, end="", flush=True)

#     content = delta.content

#     if content:
#         if not answer_started:
#             print("\n\n========== ANSWER ==========\n")
#             answer_started = True

#         print(content, end="", flush=True)


msg = HumanMessage(
    content=[
        {"type": "text", "text": "Solve the equation x^2 - 5x + 6 = 0 step-by-step"},
        # {
        #     "type": "image_url",
        #     "image_url": {
        #         "url": f"data:image/png;base64,{b64}"
        #     },
        # },
    ]
)

async def main() -> None:
    chat = ChatOpenAI(
        model="deepseek-v4-pro-search",
        temperature=0.2,
        openai_api_key="sk-local-phuong-001",
        base_url="http://127.0.0.1:6011/v1",
        reasoning={
        "effort": "medium",  # Can be "low", "medium", or "high"
        "summary": "auto",  # Can be "auto", "concise", or "detailed"
    },
    
    )

    agent = create_agent(
        model=chat,
        tools=[],
    )

    async for chunk in agent.astream(
        {"messages": [msg]},
        stream_mode="messages",
    ):
        if chunk["type"] == "messages":
            token, metadata = chunk["data"]
            
            # Lọc các khối nội dung suy luận
            reasoning = [b for b in token.content_blocks if b["type"] == "reasoning"]
            text = [b for b in token.content_blocks if b["type"] == "text"]
        
        if reasoning:
            print(f"[thinking] {reasoning[0]['reasoning']}", end="")
        if text:
            print(text[0]["text"], end="")


if __name__ == "__main__":
    asyncio.run(main())
