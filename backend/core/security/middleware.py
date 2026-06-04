from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.security.jwt import JWTHandler


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate JWT for protected routes.
    """

    async def dispatch(self, request: Request, call_next):
        public_paths = ["/docs", "/openapi.json", "/auth/login"]

        if request.url.path in public_paths:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")

        if not auth_header or "Bearer " not in auth_header:
            raise HTTPException(status_code=401, detail="Missing token")

        token = auth_header.split(" ")[1]
        decoded = JWTHandler.decode_token(token)

        if not decoded:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        request.state.user = decoded
        return await call_next(request)
