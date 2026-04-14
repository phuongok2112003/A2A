import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent
from config.settings import settings
from langchain_google_genai import ChatGoogleGenerativeAI

tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)

def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
# System prompt to steer the agent to be an expert researcher
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""
llm_gemini = ChatGoogleGenerativeAI(
    model="models/gemini-2.0-flash",
    temperature=0.2,
    google_api_key=settings.GOOGLE_A2A_API_KEY,
)
agent = create_deep_agent(
    model = llm_gemini,
    tools=[internet_search],
    system_prompt=research_instructions,
    debug=True
)

result = agent.invoke({"messages": [{"role": "user", "content": "What is langgraph?"}]})

# Print the agent's response
print(result["messages"][-1].content)