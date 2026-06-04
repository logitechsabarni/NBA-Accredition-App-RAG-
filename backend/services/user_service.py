from typing import Dict, Optional
from backend.core.security.jwt import JWTHandler


class UserService:
    """
    Handles authentication-related business logic.
    """

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        # MOCK AUTH (replace with DB later)
        if username == "admin" and password == "admin":
            return JWTHandler.create_token({"user": username})

        return None

    def get_user_from_token(self, token: str) -> Optional[Dict]:
        return JWTHandler.decode_token(token)
