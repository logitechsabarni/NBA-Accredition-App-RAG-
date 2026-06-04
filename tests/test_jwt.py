from backend.core.security.jwt import JWTHandler


def test_jwt_creation_and_decode():
    token = JWTHandler.create_token({"user": "test"})
    decoded = JWTHandler.decode_token(token)

    assert decoded["user"] == "test"
