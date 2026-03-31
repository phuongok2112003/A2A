import asyncio
import os
from pprint import pprint
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.backends.utils import create_file_data
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import settings  # Giả sử settings.GOOGLE_A2A_API_KEY
from common.export_models_llm import ModelsLLM
from common.tool_common import run_shell
async def main():
   
    # Checkpointer bắt buộc
    checkpointer = MemorySaver()

    # System prompt tối ưu cho skills + browser tasks
    system_prompt = """
    You are an expert web researcher. Khi user đưa URL, dùng skills trong /skills/agent-browser/:
  

    **Browser skills tự động hướng dẫn cách thao tác với browser.**
    """

    # FilesystemBackend + skills path của bạn
    agent = create_deep_agent(
        model=ModelsLLM.llm_ollama_nemotron,
        skills=["./skills/agent-browser/"],  # ← Skills folder của bạn (browser skills)
        backend=FilesystemBackend(root_dir="./doc"),  # Workspace lưu files
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        debug=True,
        tools=[run_shell],
        interrupt_on={
            "write_file": True,  # HITL approve/edit files
            "edit_file": True,
        }
    )

    # User message với URL IBM
    user_message = (
        "Truy cập link này và tóm tắt nội dung: "
        "https://www.ibm.com/think/topics/latent-space. "
        "Sử dụng skills browser trong /skills/ để scrape và analyze. "
        "Viết summary ngắn gọn + key points."
    )

    # Stream
    async for chunk in agent.astream(
        {"messages": [{"role": "user", "content": user_message}]},
        stream_mode=["values", "updates", "messages"],
        config={"configurable": {"thread_id": "browser-task-1"}}
    ):
        pprint(chunk)


if __name__ == "__main__":
    asyncio.run(main())