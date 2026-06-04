import os
import jwt
import datetime
from typing import Dict, Any, Optional

SECRET_KEY = os.getenv("JWT_SECRET", "dev_secret_key")
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 60 * 24  # 24 hours


class JWTHandler:
    """
    Handles JWT encoding and decoding for authentication.
    """

    @staticmethod
    def create_token(data: Dict[str, Any]) -> str:
        payload = data.copy()
        payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=EXPIRATION_MINUTES
        )
        payload["iat"] = datetime.datetime.utcnow()

        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return decoded
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
