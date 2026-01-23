from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints and FastAPI docs
        public_paths = [
            '/', 
            '/health', 
            '/ready',
            '/baselines',  # Public: just lists available baselines (metadata)
            '/docs',
            '/openapi.json',
            '/redoc',
            '/favicon.ico'
        ]
        
        if request.url.path in public_paths:
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        valid_keys_str = os.getenv("API_KEYS", "")
        
        # Handle empty API_KEYS (development mode)
        if not valid_keys_str:
            # Allow requests if no API keys configured (development)
            return await call_next(request)
        
        valid_keys = [key.strip() for key in valid_keys_str.split(",") if key.strip()]

        if not api_key or api_key not in valid_keys:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or missing API key", "detail": "Invalid or missing API key"}
            )
        
        return await call_next(request)
    