from pinecone import Pinecone
from config.settings import settings
pc = Pinecone(api_key=settings.PINECONE_KEY)

# Create a dense index with integrated inference
index_name = "llama-text-embed-v2"
if not pc.has_index(index_name):
    pc.create_index_for_model(
        name=index_name,
        cloud="aws",
        region="us-east-1",
        embed={
            "model": "llama-text-embed-v2",
            "field_map": {
                "text": "text"  # Map the record field to be embedded
            }
        }
    )

index = pc.Index(index_name)

data = [
    {"id": "vec1", "text": "Apple is a popular fruit known for its sweetness and crisp texture."},
    {"id": "vec2", "text": "The tech company Microsoft is known for its innovative products like the Window."},
    {"id": "vec3", "text": "Many people enjoy eating apples as a healthy snack."},
    {"id": "vec4", "text": "Apple Inc. has revolutionized the tech industry with its sleek designs and user-friendly interfaces."},
    {"id": "vec5", "text": "An apple a day keeps the doctor away, as the saying goes."},
    {"id": "vec6", "text": "Apple Computer Company was founded on April 1, 1976, by Steve Jobs, Steve Wozniak, and Ronald Wayne as a partnership."}
]

index.upsert_records(
    namespace="example-namespace",
    records=data
)
query_payload = {
    "inputs": {
        "text": "Tell me about the tech company known as Meta Facebook."
    },
    "top_k": 3
}

results = index.search(
    namespace="example-namespace",
    query=query_payload
)

print(results)