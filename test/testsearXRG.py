import httpx

BASE_URL = "http://localhost:8888"

params = {
    "q": "AI hackathon Vietnam 2026",
    "format": "json",
}

response = httpx.post(
    f"{BASE_URL}/search",
    params=params,
    timeout=30,
)

response.raise_for_status()

data = response.json()

for item in data["results"][:5]:
    print(item["title"])
    print(item["url"])
    print(item.get("content"))
    print("-" * 50)