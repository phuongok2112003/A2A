from langchain_core.tools import tool
import unicodedata

def normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text)\
        .encode("ascii", "ignore")\
        .decode("utf-8")\
        .lower()

@tool
def get_weather(city: str) -> dict:
    """
    Lấy thời tiết hiện tại của một thành phố
    """
    c = normalize(city)

    if c in ["ha noi", "hanoi","Hà Nội"]:
        return {"city": "Hà Nội", "temp": 30, "condition": "nắng", "status_call_tool": "success"}

    if c in ["sai gon", "saigon"]:
        return {"city": "TP.HCM", "temp": 33, "condition": "nóng", "status_call_tool": "success"}

    return {"error": "not_found", "city": city, "status_call_tool": "success"}

@tool
def get_news(topic: str) -> list[dict]:
    """
    Lấy danh sách tin tức mới nhất về một chủ đề
    """
    return [
        {"title": f"Tin tức 1 về {topic}", "url": "http://example.com/news1"},
        {"title": f"Tin tức 2 về {topic}", "url": "http://example.com/news2"},
        {"title": f"Tin tức 3 về {topic}", "url": "http://example.com/news3"},
    ]

tools = [get_weather, get_news]