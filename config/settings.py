import os
from pydantic_settings import BaseSettings
import dotenv
dotenv.load_dotenv()

class Settings(BaseSettings):
    GOOGLE_A2A_API_KEY: str = os.getenv("GOOGLE_A2A_API_KEY", "your_default_api_key")
    AGENT_1_PATH: str = os.getenv("PATH_AGENT_1", "/a2a/agent11")
    AGENT_2_PATH: str = os.getenv("PATH_AGENT_2", "/a2a/agent2")
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:10000")
    ELASTICSEARCH_URL: str = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    OPENAI_A2A_API_KEY: str = os.getenv("OPENAI_A2A_API_KEY", "your_openai_api_key")
    PINECONE_KEY: str = os.getenv("PINECONE_KEY","your_pinecone_api_key")
    MODEL_EMBEDING:str = os.getenv("MODEL_EMBEDING","llama-text-embed-v2")
    TAVILY_API_KEY:str = os.getenv("TAVILY_API_KEY","")
    BOOT_ZALO_TOKEN:str = os.getenv("BOOT_ZALO_TOkEN","")
    SECRET_TOKEN_WEBHOOK_ZALO:str = os.getenv("SECRET_TOKEN_WEBHOOK_ZALO","")
    NGROK_API:str = os.getenv("NGROK_API","http://127.0.0.1:4040/api/tunnels")
    APP_NAME: str = "A2A_Application"

settings = Settings()