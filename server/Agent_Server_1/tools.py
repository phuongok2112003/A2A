from langchain_core.tools import tool
from langchain_community.tools import TavilySearchResults
from config.settings import settings
import unicodedata
from datetime import datetime, timedelta
from typing import Literal


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text)\
        .encode("ascii", "ignore")\
        .decode("utf-8")\
        .lower()


# ================================
# Weather Tool
# ================================

@tool
def get_weather(city: str) -> dict:
    """
    Lấy thời tiết hiện tại của một thành phố

    Args:
        city: Tên thành phố (tiếng Việt hoặc tiếng Anh)

    Returns:
        dict với thông tin thời tiết: city, temp, condition
    """
    c = normalize(city)

    if c in ["ha noi", "hanoi"]:
        return {"city": "Hà Nội", "temp": 30, "condition": "nắng", "status_call_tool": "success"}

    if c in ["sai gon", "saigon", "ho chi minh"]:
        return {"city": "TP.HCM", "temp": 33, "condition": "nóng", "status_call_tool": "success"}

    if c in ["da nang", "danang"]:
        return {"city": "Đà Nẵng", "temp": 28, "condition": "mây", "status_call_tool": "success"}

    return {"error": "not_found", "city": city, "status_call_tool": "success"}


# ================================
# News Tools
# ================================

@tool
def get_news(topic: str, limit: int = 5) -> list[dict]:
    """
    Lấy danh sách tin tức mới nhất về một chủ đề
    Dùng khi người dùng muốn tìm tin tức về một chủ đề cụ thể

    Args:
        topic: Chủ đề cần tìm tin (technology, ai, programming, etc.)
        limit: Số lượng tin tức cần lấy (mặc định 5)

    Returns:
        List các tin tức với title, url, description
    """
    # Stub data - có thể thay bằng API thực
    return [
        {"title": f"Tin tức 1 về {topic}", "url": f"http://example.com/news1-{topic}", "description": f"Mô tả tin tức về {topic}"},
        {"title": f"Tin tức 2 về {topic}", "url": f"http://example.com/news2-{topic}", "description": f"Mô tả tin tức về {topic}"},
        {"title": f"Tin tức 3 về {topic}", "url": f"http://example.com/news3-{topic}", "description": f"Mô tả tin tức về {topic}"},
    ]


# ================================
# Internet Search Tool (Tavily)
# ================================

@tool
def search_internet(query: str, search_depth: Literal["basic", "advanced"] = "advanced") -> str:
    """
    Tìm kiếm thông tin mới nhất trên internet bằng Tavily API.
    Rất hữu ích để lấy thông tin công nghệ, tin tức, tài liệu mới nhất.

    Args:
        query: Câu hỏi hoặc từ khóa tìm kiếm
        search_depth: Độ sâu tìm kiếm - 'basic' nhanh hơn, 'advanced' chi tiết hơn

    Returns:
        Dưới dạng markdown với thông tin tìm được
    """
    if not settings.TAVILY_API_KEY:
        return "Error: Tavily API key not configured. Please contact administrator."

    try:
        client = TavilySearchResults(
            api_key=settings.TAVILY_API_KEY,
            max_results=5,
            search_depth=search_depth,
            include_answer=True,
            include_raw_content=True,
        )

        results = client.invoke(query)

        if not results:
            return "Không tìm thấy kết quả nào."

        output = []
        for i, result in enumerate(results, 1):
            output.append(f"### Kết quả {i}: {result.get('title', 'No title')}")
            output.append(f"URL: {result.get('url', 'No URL')}")
            output.append(f"**Tóm tắt**: {result.get('content', 'No content')}")
            output.append("")

        return "\n".join(output)

    except Exception as e:
        return f"Lỗi khi tìm kiếm: {str(e)}"


@tool
def get_today_tech_news(topic: str = "technology", days: int = 1) -> list[dict]:
    """
    Lấy tin tức công nghệ trong ngày hoặc trong vài ngày gần đây.
    Tự động lọc các tin tức mới nhất từ hôm nay.

    Args:
        topic: Chủ đề công nghệ (technology, ai, programming, software, hardware)
        days: Số ngày gần đây cần lấy tin (1 = hôm nay, 2-3 = vài ngày gần đây)

    Returns:
        List tin tức công nghệ với tiêu đề, URL, ngày đăng
    """
    from tavily import TavilyClient

    if not settings.TAVILY_API_KEY:
        return [{"error": "Tavily API key not configured"}]

    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)

        # Calculate date range
        today = datetime.now()
        from_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")

        # Build query with date filter
        query = f"{topic} technology news {today.strftime('%Y-%m-%d')}"

        response = client.search(
            query=query,
            max_results=10,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False,
        )

        results = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "summary": item.get("content", ""),
                "published_date": item.get("published_date", ""),
                "score": item.get("score", 0),
            })

        return results

    except Exception as e:
        return [{"error": str(e)}]


@tool
def get_latest_ai_news() -> list[dict]:
    """
    Lấy tin tức AI mới nhất từ hôm nay.

    Returns:
        List tin tức AI với tiêu đề, URL, tóm tắt
    """
    return get_today_tech_news.topic("ai", days=1)


@tool
def get_latest_programming_news() -> list[dict]:
    """
    Lấy tin tức lập trình mới nhất từ hôm nay.

    Returns:
        List tin tức lập trình với tiêu đề, URL, tóm tắt
    """
    return get_today_tech_news.topic("programming", days=1)


tools = [get_weather, get_news, search_internet, get_today_tech_news, get_latest_ai_news, get_latest_programming_news]