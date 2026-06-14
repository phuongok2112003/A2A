from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

client = NVIDIAEmbeddings(
  model="nvidia/nv-embedcode-7b-v1", 
  api_key="lkjf", 
  truncate="NONE", 
  )

embedding = client.embed_query("What is the capital of France?")
print(embedding)
