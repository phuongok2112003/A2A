from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException

class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.headers.get("content-length"):
            size = int(request.headers["content-length"])
            if size > 10 * 1024 * 1024:
                raise HTTPException(413, "File too large")

        return await call_next(request)
