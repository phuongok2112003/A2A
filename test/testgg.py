from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover - optional dependency
    sync_playwright = None


DEFAULT_SEARXNG_BASE_URL = os.getenv("SEARXNG_BASE_URL", "http://localhost:8888")
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_TIMEOUT_SECONDS = float(os.getenv("WEB_SEARCH_TIMEOUT_SECONDS", "30"))
DEFAULT_FETCH_TEXT_LIMIT = int(os.getenv("WEB_FETCH_TEXT_LIMIT", "12000"))

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
}


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""


@dataclass
class PageContent:
    url: str
    title: str
    content: str


def clean_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    clean_query = {
        key: value
        for key, value in query.items()
        if key not in TRACKING_PARAMS
    }
    query_string = "&".join(
        f"{key}={value[0]}"
        for key, value in clean_query.items()
        if value
    )
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            query_string,
            "",
        )
    )


def truncate_text(value: str, limit: int = DEFAULT_FETCH_TEXT_LIMIT) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n...[truncated]"


def extract_content_from_html(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    main = soup.find("article") or soup.find("main") or soup.find("body")
    if not main:
        return title, ""

    text = main.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return title, "\n".join(lines)


def normalize_search_results(payload: Any, max_results: int = 5) -> list[dict[str, str]]:
    if isinstance(payload, dict):
        raw_results = payload.get("results", [])
    elif isinstance(payload, list):
        raw_results = payload
    else:
        raw_results = []

    items: list[dict[str, str]] = []
    seen: set[str] = set()

    for item in raw_results:
        if not isinstance(item, dict):
            continue

        url = item.get("url") or item.get("link") or item.get("href")
        title = item.get("title") or item.get("name") or item.get("headline")
        snippet = item.get("content") or item.get("snippet") or item.get("description") or ""

        if not url or not title:
            continue

        cleaned_url = clean_url(str(url))
        if cleaned_url in seen:
            continue
        seen.add(cleaned_url)

        items.append(
            asdict(
                SearchResult(
                    title=str(title).strip(),
                    url=cleaned_url,
                    snippet=str(snippet).strip(),
                )
            )
        )
        if len(items) >= max_results:
            break

    return items


def normalize_fetch_result(payload: Any, url: str) -> dict[str, str]:
    if isinstance(payload, dict):
        title = payload.get("title") or payload.get("name") or ""
        content = (
            payload.get("content")
            or payload.get("text")
            or payload.get("body")
            or payload.get("markdown")
            or ""
        )
        resolved_url = payload.get("url") or payload.get("link") or url
    else:
        title = ""
        content = str(payload or "")
        resolved_url = url

    return asdict(
        PageContent(
            url=clean_url(str(resolved_url)),
            title=str(title).strip(),
            content=truncate_text(str(content)),
        )
    )


def searxng_search(
    keyword: str,
    limit: int = 15,
    base_url: str = DEFAULT_SEARXNG_BASE_URL,
) -> list[dict[str, str]]:
    with httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS, follow_redirects=True) as client:
        response = client.get(
            f"{base_url}/search",
            params={"q": keyword, "format": "json"},
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        response.raise_for_status()
        return normalize_search_results(response.json(), max_results=limit)


def fetch_page_via_http(url: str) -> dict[str, str]:
    with httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS, follow_redirects=True) as client:
        response = client.get(
            url,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        response.raise_for_status()
        title, content = extract_content_from_html(response.text)
        if not content:
            content = response.text
        return asdict(
            PageContent(
                url=clean_url(str(response.url)),
                title=title,
                content=truncate_text(content),
            )
        )


def fetch_page_via_playwright(url: str) -> dict[str, str]:
    if sync_playwright is None:
        raise RuntimeError("playwright is not installed")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        try:
            page = browser.new_page(
                user_agent=DEFAULT_USER_AGENT,
                viewport={"width": 1366, "height": 768},
            )
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(1500)
            html = page.content()
            title, content = extract_content_from_html(html)
            if len(content) < 200:
                try:
                    content = page.locator("body").inner_text(timeout=10_000)
                except Exception:
                    pass
            return asdict(
                PageContent(
                    url=clean_url(page.url),
                    title=title,
                    content=truncate_text(content),
                )
            )
        finally:
            browser.close()


def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """
    Search the web through the local SearXNG instance and return normalized results.

    Args:
        query: Search keyword or natural-language query.
        max_results: Maximum number of unique results to return.
    """
    return searxng_search(keyword=query, limit=max_results)


def fetch_webpage_text(url: str) -> dict[str, Any]:
    """
    Fetch and extract readable text from a web page.

    Never raise exception to the agent layer.
    Return structured error instead.
    """

    try:
        return {
            "success": True,
            "data": fetch_page_via_http(url),
        }

    except Exception as http_error:
        if sync_playwright is None:
            return {
                "success": False,
                "url": url,
                "error": f"HTTP fetch failed: {str(http_error)}",
            }

    try:
        return {
            "success": True,
            "data": fetch_page_via_playwright(url),
        }

    except Exception as playwright_error:
        return {
            "success": False,
            "url": url,
            "error": f"Playwright fetch failed: {str(playwright_error)}",
        }


from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
import asyncio
async def main():
    

    system_prompt =  (
        "Bạn là một web research agent chuyên tìm kiếm, đọc, đối chiếu và tóm tắt thông tin trên internet. "
        "Bạn có đúng 2 tool để làm việc: `search_web(query, max_results)` dùng để tìm danh sách kết quả, "
        "và `fetch_webpage_text(url)` dùng để đọc nội dung một URL cụ thể. "
        "Không được bịa nguồn, không được kết luận chỉ từ ký ức nội bộ khi task yêu cầu thông tin trên web.\n\n"
        "Quy trình bắt buộc:\n"
        "1. Phân tích yêu cầu để xác định rõ: chủ đề, mốc thời gian, địa lý, loại thông tin cần lấy, và tiêu chí loại bỏ.\n"
        "2. Luôn bắt đầu bằng `search_web`. Nếu query gốc mơ hồ, hãy tự tạo 2-4 truy vấn search ngắn, chính xác và bám sát mục tiêu.\n"
        "3. Từ kết quả search, chỉ chọn các URL có vẻ trực tiếp, liên quan và đáng tin hơn. Ưu tiên nguồn gốc như trang chính thức, thông báo sự kiện, tài liệu gốc, bài viết có ngày rõ ràng. Không fetch tràn lan.\n"
        "4. Dùng `fetch_webpage_text` để đọc từng URL đã chọn. Khi đọc, hãy kiểm tra xem nguồn có thật sự nhắc đến đúng chủ đề, đúng thời gian, đúng địa lý và đúng thực thể mà người dùng yêu cầu hay không.\n"
        "4a. Nếu `fetch_webpage_text` bị lỗi hoặc trả về nội dung rỗng, hãy bỏ qua URL đó và tiếp tục với URL khác; không được coi đó là lỗi toàn bộ task.\n"
        "5. Loại bỏ các kết quả sai ngữ cảnh, sai năm, sai quốc gia/thành phố, trang tổng hợp mơ hồ, nội dung SEO, hoặc nguồn chỉ lặp lại nguồn khác.\n"
        "6. Nếu nhiều nguồn mâu thuẫn, nêu rõ điểm mâu thuẫn và ưu tiên nguồn trực tiếp hơn nguồn gián tiếp.\n"
        "7. Chỉ kết luận những gì được hỗ trợ bởi nội dung bạn đã tìm thấy. Nếu dữ liệu chưa đủ, phải nói rõ là chưa xác nhận được.\n"
        "8. Trong lúc dùng tool, hãy tận dụng các kết quả trả về để quyết định bước tiếp theo thay vì gọi tool ngẫu nhiên.\n\n"
        "Quy tắc trả lời:\n"
        "- Trả lời bằng tiếng Việt rõ ràng, ngắn gọn nhưng đủ ý.\n"
        "- Phải bám đúng `output_instruction` nếu có.\n"
        "- Tuyệt đối không trả về JSON array, JSON object, Python dict, hay dump raw payload của tool trong câu trả lời cuối.\n"
        "- Không chép nguyên danh sách kết quả search thô. Bạn phải tổng hợp lại thành báo cáo dễ đọc cho con người.\n"
        "- Không nêu chain-of-thought dài dòng; chỉ đưa kết luận đã kiểm chứng và caveat cần thiết.\n"
        "- Phần `## Sources` phải chứa URL trực tiếp, mỗi dòng một URL.\n"
        "- Nếu không tìm được nguồn đủ tin cậy, phải nói rõ điều đó trong `## Summary`.\n\n"
        "Định dạng cuối cùng bắt buộc:\n"
        "## Summary\n"
        "- Tóm tắt kết quả đã lọc\n"
        "- Nêu điều kiện, giới hạn, hoặc điểm chưa chắc chắn nếu có\n\n"
        "## Sources\n"
        "- https://...\n"
        "- https://...\n"
    )
    # ---------- Tạo Agent ----------
    model = ChatOpenAI(
    model="nemotron-3-super:cloud",
    temperature=0.2,
    api_key=os.environ["OLLAMA_KEY"],
    base_url="https://ollama.com/v1"
)
    agent = create_deep_agent(
        model,
        [search_web, fetch_webpage_text],
        system_prompt=system_prompt,
    )


    # ---------- Tin nhắn từ người dùng (đã sửa để tránh lỗi encoding) ----------
    user_message = "Tôi muốn bạn tìm cho tôi những cuộc thi hackathon về AI sắp diễn ra trong năm 2026, hôm nay là ngày 20/5/2026, loại bỏ những cuộc thi đã diễn ra và đang diễn ra. Thống kê cho tôi những cuộc thi ở miền Bắc Việt Nam thôi"



    try:
        async for event, data in agent.astream(
            {"messages": [{"role": "user", "content": user_message}]},
            stream_mode=["values", "updates", "messages"],
            config={"configurable": {"thread_id": "browser-research-001"}}
        ):
            # In ra messages mới nhất
            if isinstance(data, dict) and "messages" in data:
                data["messages"][-1].pretty_print()
            elif hasattr(data, 'content'):
                # BaseMessage trực tiếp
                data.pretty_print()
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")



if __name__ == "__main__":
    asyncio.run(main())
