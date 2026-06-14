from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from config.settings import settings
from common.chat_customs import ChatCustoms


class ModelsLLM():
    
    llm_gemini = ChatGoogleGenerativeAI(
        model="models/gemini-2.0-flash",
        temperature=0.2,
        google_api_key=settings.GOOGLE_A2A_API_KEY,
    )
    llm_gemini = ChatCustoms(
        model="gemma4:e2b",
        base_url="https://agent.pgcluster.asia",
        temperature=0.7,
        enable_thinking=True,
    )
    llm_openai = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.2,
        openai_api_key=settings.OPENAI_A2A_API_KEY,
    )
 
    llm_ollama_gpt = ChatOllama(
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
    
    llm_ollama_nemotron = ChatOllama(
        model="nemotron-3-super:cloud",
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
    llm_customs = ChatCustoms(
        model="nemotron-3-super:cloud",
        base_url="https://ollama.com",
        temperature=0.7,
        enable_thinking=True,
        headers={
            "Authorization": f"Bearer {settings.OLLAMA_KEY}"
        },)
    
