from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from config.settings import settings


import unicodedata

def normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text)\
        .encode("ascii", "ignore")\
        .decode("utf-8")\
        .lower()

@tool
def get_weather(city: str) -> dict:
    """
    Lấy thời tiết hiện tại của một thành phố
    """
    c = normalize(city)

    if c in ["ha noi", "hanoi"]:
        return {"city": "Hà Nội", "temp": 30, "condition": "nắng"}

    if c in ["sai gon", "saigon"]:
        return {"city": "TP.HCM", "temp": 33, "condition": "nóng"}

    return {"error": "not_found", "city": city}



# ===============================
# 1. System Prompt
# ===============================

SYSTEM_PROMPT = """
Bạn là một trợ lý hữu ích và thông minh.
Bạn có khả năng trả lời các câu hỏi trực tiếp.
Bạn cũng có thể sử dụng các công cụ để hỗ trợ trả lời.
"""
system_prompt = SystemMessage(content=SYSTEM_PROMPT)

# ===============================
# 2. Agent Factory
# ===============================

def gen_agent(tools=None):
    if tools is None:
        tools = [get_weather]

    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        temperature=0.2,
        google_api_key=settings.GOOGLE_A2A_API_KEY,
    )

    # Memory cho mỗi thread (mỗi context_id)
    checkpointer = MemorySaver()

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        name="gemini-agent",
        debug=True
    )

    return agent
class AgentCustom:
    def __init__(self):
        self.agent = gen_agent()

    def run(self, user_input: str, context_id: str):
        """
        context_id = conversation_id
        """

        result = self.agent.invoke(
            {
                "messages": [
                    HumanMessage(content=user_input)
                ]
            },
            config={
                "configurable": {
                    "thread_id": context_id   # LangGraph memory key
                }
            }
        )

        # result["messages"] là toàn bộ lịch sử
        return result["messages"][-1].content
