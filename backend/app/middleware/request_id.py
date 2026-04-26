"""Request ID middleware for tracking."""
import uuid
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from app.config import settings


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to every request/response."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(settings.REQUEST_ID_HEADER)
        if not request_id:
            request_id = str(uuid.uuid4())
        
        response = await call_next(request)
        response.headers[settings.REQUEST_ID_HEADER] = request_id
        return response