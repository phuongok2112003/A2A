import httpx


async def download_image(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=40) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content
