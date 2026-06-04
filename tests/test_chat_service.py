from backend.services.chat_service import ChatService


def test_chat_response():
    service = ChatService()
    response = service.get_response("Who is LeBron James?")
    assert isinstance(response, str)
