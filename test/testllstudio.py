# import lmstudio as lms
# # lms.configure_default_client(api_token="sk-lm-9SHkk7ni:P1AH3GaGa5e1xkxnt0FK")
# with lms.Client() as client:
#     model = client.llm.model("google/gemma-4-e2b")
#     result = model.respond("Who are you, and what can you do?")
#     print(result)


from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="google/gemma-4-e2b", temperature=0.2, openai_api_base="http://localhost:1234/v1")
result = model.invoke("Who are you, and what can you do?")
print(result)

# import requests

# res = requests.post(
#     "http://localhost:1234/v1/chat/completions",
#     json={
#         "model": "google/gemma-4-e2b",
#         "messages": [{"role": "user", "content": "Hello"}]
#     }
# )

# print(res.json())