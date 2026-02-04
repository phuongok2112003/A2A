# from pinecone import Pinecone
# from config.settings import settings
# import json

# pc = Pinecone(api_key=settings.PINECONE_KEY)
# index_name = "llama-text-embed-v2"

# if not pc.has_index(index_name):
#     pc.create_index_for_model(
#         name=index_name,
#         cloud="aws",
#         region="us-east-1",
#         embed={
#             "model": "llama-text-embed-v2",
#             "field_map": {
#                 "text": "text"  # Map the record field to be embedded
#             }
#         }
#     )

# index = pc.Index(index_name)

# # data = [
# #     {"id": "vec1", "text": "Apple is a popular fruit known for its sweetness and crisp texture."},
# #     {"id": "vec2", "text": "The tech company Microsoft is known for its innovative products like the Window."},
# #     {"id": "vec3", "text": "Many people enjoy eating apples as a healthy snack."},
# #     {"id": "vec4", "text": "Apple Inc. has revolutionized the tech industry with its sleek designs and user-friendly interfaces."},
# #     {"id": "vec5", "text": "An apple a day keeps the doctor away, as the saying goes."},
# #     {"id": "vec6", "text": "Apple Computer Company was founded on April 1, 1976, by Steve Jobs, Steve Wozniak, and Ronald Wayne as a partnership."}
# # ]

# # index.upsert_records(
# #     namespace="example-namespace",
# #     records=data
# # )

# # # Method 1: Pass the query as a dict (recommended)
# # query_payload = {
# #     "inputs": {"text": "Tôi muốn tìm hiểu về công ty Microsoft"},
# #     "top_k": 3
# # }

# # results = index.search(
# #     namespace="example-namespace",
# #     query=query_payload  # ← Pass dict directly, not bytes
# # )

# # print(results["result"]["hits"])

# # # Alternative: If you need to pass just the text string
# # # results = index.search(
# # #     namespace="example-namespace",
# # #     query="Tôi muốn tìm hiểu về công ty Microsoft"
# # # )
# # # print(results["result"]["hits"])


# from langchain_pinecone import PineconeEmbeddings
# from langchain_pinecone import PineconeVectorStore


# embeddings = PineconeEmbeddings(model="llama-text-embed-v2", pinecone_api_key=settings.PINECONE_KEY)
# vector_store = PineconeVectorStore(index=index, embedding=embeddings)
# docs = [
#     "Apple is a popular fruit known for its sweetness and crisp texture.",
#     "The tech company Apple is known for its innovative products like the iPhone.",
#     "Many people enjoy eating apples as a healthy snack.",
#     "Apple Inc. has revolutionized the tech industry with its sleek designs and user-friendly interfaces.",
#     "An apple a day keeps the doctor away, as the saying goes.",
# ]
# doc_embeds = embeddings.embed_documents(docs)
# # print(doc_embeds)



# query = "Tell me about the tech company known as Apple"
# query_embed = embeddings.embed_query("Tôi muốn tìm hiểu về công ty Microsoft")


# from uuid import uuid4

# from langchain_core.documents import Document

# document_1 = Document(
#     page_content="I had chocolate chip pancakes and scrambled eggs for breakfast this morning.",
#     metadata={"source": "tweet"},
# )

# document_2 = Document(
#     page_content="The weather forecast for tomorrow is cloudy and overcast, with a high of 62 degrees.",
#     metadata={"source": "news"},
# )

# document_3 = Document(
#     page_content="Building an exciting new project with LangChain - come check it out!",
#     metadata={"source": "tweet"},
# )

# document_4 = Document(
#     page_content="Robbers broke into the city bank and stole $1 million in cash.",
#     metadata={"source": "news"},
# )

# document_5 = Document(
#     page_content="Wow! That was an amazing movie. I can't wait to see it again.",
#     metadata={"source": "tweet"},
# )

# document_6 = Document(
#     page_content="Is the new iPhone worth the price? Read this review to find out.",
#     metadata={"source": "website"},
# )

# document_7 = Document(
#     page_content="The top 10 soccer players in the world right now.",
#     metadata={"source": "website"},
# )

# document_8 = Document(
#     page_content="LangGraph is the best framework for building stateful, agentic applications!",
#     metadata={"source": "tweet"},
# )

# document_9 = Document(
#     page_content="The stock market is down 500 points today due to fears of a recession.",
#     metadata={"source": "news"},
# )

# document_10 = Document(
#     page_content="I have a bad feeling I am going to get deleted :(",
#     metadata={"source": "tweet"},
# )

# documents = [
#     document_1,
#     document_2,
#     document_3,
#     document_4,
#     document_5,
#     document_6,
#     document_7,
#     document_8,
#     document_9,
#     document_10,
# ]
# uuids = [str(uuid4()) for _ in range(len(documents))]
# vector_store.add_documents(documents=documents, ids=uuids)


# results = vector_store.similarity_search(
#     "LangChain provides abstractions to make working with LLMs easy",
#     k=2,
#     filter={"source": "tweet"},
# )
# for res in results:
#     print(f"* {res.page_content} [{res.metadata}]")



from  memory.memory_store import PineconeMemoryStore
from config.settings import settings
from langgraph.store.base import BaseStore, GetOp, PutOp, SearchOp, ListNamespacesOp, Result, Item, SearchItem, Op

store = PineconeMemoryStore(api_key=settings.PINECONE_KEY)
store.put(namespace=("test",), key="test", value={"name": "Phượng"})
item = store.get(namespace=("test",), key="test")

result = store.search(('user_124',), filter=None, limit=100, offset=0, query=None, refresh_ttl=True)
print(result)

filepaht= "/user_124/profile.txt"
sp = filepaht.split('/')
print(sp)

