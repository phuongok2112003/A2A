from langfuse import get_client, Langfuse
from langfuse.langchain import CallbackHandler

# import os


# # Get keys for your project from the project settings page: https://cloud.langfuse.com
# os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-e4f8d98a-852c-4a14-96cd-90e5f5d9abbe" 
# os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-0243fca3-8c39-4883-816e-0c01a73220df" 
# os.environ["LANGFUSE_BASE_URL"] = "http://localhost:3000" # 🇪🇺 EU region
# langfuse = get_client( )  # You can also set the public key via the LANGFUSE_PUBLIC_KEY environment variable

langfuse = Langfuse(
    public_key="pk-lf-e4f8d98a-852c-4a14-96cd-90e5f5d9abbe",
    secret_key="sk-lf-0243fca3-8c39-4883-816e-0c01a73220df",
    base_url="http://localhost:3000"
)




from operator import itemgetter
from langchain_ollama import ChatOllama


langfuse_handler = CallbackHandler()


llm_ollama_nemotron = ChatOllama(
    model="nemotron-3-super:cloud",
    base_url="https://ollama.com",
    client_kwargs={
        "headers": {
            "Authorization": f"Bearer api_key"
        },
        "timeout": 120,
    },
    temperature=0,

)
response = llm_ollama_nemotron.invoke("What is the capital of France?", config={"callbacks": [langfuse_handler]})

print(response)