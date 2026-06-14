import os

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from langchain.tools import tool


@tool
def ask_user(question: str) -> str:
    """Sử dụng khi cần hỏi người dùng thêm thông tin."""
    return "Placeholder"


llm = ChatOpenAI(
    model="nemotron-3-super:cloud",
    temperature=0.2,
    api_key=os.environ["OLLAMA_KEY"],
    base_url="https://ollama.com/v1",
)

agent = create_agent(
    model=llm,
    tools=[ask_user],
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={"ask_user": True}
        )
    ],
    checkpointer=InMemorySaver(),
)

config = {"configurable": {"thread_id": "test_1"}}

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Hãy xây dựng một website màu đẹp cho tôi.",
            }
        ]
    },
    config=config,
    version="v2",
)

while result.interrupts:
    interrupt_data = result.interrupts[0].value

    action_requests = interrupt_data.get("action_requests", [])
    if not action_requests:
        raise RuntimeError("Không tìm thấy action_requests trong interrupt data.")

    action = action_requests[0]
    args = action.get("args") or action.get("arguments") or {}
    question = args.get("question", "Agent cần thêm thông tin.")

    print("\n--- AGENT ĐANG TẠM DỪNG ---")
    print(f"Agent hỏi: {question}")

    user_input = input("Nhập câu trả lời của bạn: ")

    result = agent.invoke(
        Command(
            resume={
                "decisions": [
                    {
                        "type": "respond",
                        "message": user_input,
                    }
                ]
            }
        ),
        config=config,
        version="v2",
    )

print("\n--- FINAL RESULT ---")
print(result)
