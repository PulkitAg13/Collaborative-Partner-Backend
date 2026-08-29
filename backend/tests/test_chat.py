"""Tests for the /api/v1/chat endpoint."""


def _create_conversation(client, user_id: str = "chat-user") -> str:
    resp = client.post("/api/v1/conversations", json={"user_id": user_id})
    assert resp.status_code == 201
    return resp.json()["conversation_id"]


def test_chat_basic(client):
    conv_id = _create_conversation(client)
    resp = client.post(
        "/api/v1/chat",
        json={"conversation_id": conv_id, "message": "Hello, I need help."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["conversation_id"] == conv_id
    assert "message_id" in data
    assert "response" in data
    assert "response_type" in data
    assert len(data["response"]) > 0


def test_chat_invalid_conversation(client):
    resp = client.post(
        "/api/v1/chat",
        json={"conversation_id": "does-not-exist", "message": "Hi"},
    )
    assert resp.status_code == 404


def test_chat_empty_message(client):
    conv_id = _create_conversation(client)
    resp = client.post(
        "/api/v1/chat",
        json={"conversation_id": conv_id, "message": ""},
    )
    assert resp.status_code == 422


def test_chat_missing_conversation_id(client):
    resp = client.post("/api/v1/chat", json={"message": "Hello"})
    assert resp.status_code == 422


def test_chat_builds_history(client):
    """Each subsequent message should be added to the conversation history."""
    conv_id = _create_conversation(client)

    client.post("/api/v1/chat", json={"conversation_id": conv_id, "message": "First message"})
    client.post("/api/v1/chat", json={"conversation_id": conv_id, "message": "Second message"})

    history = client.get(f"/api/v1/conversations/{conv_id}").json()
    # 2 user messages + 2 assistant responses = 4 total
    assert len(history["messages"]) == 4


def test_chat_response_includes_preferences_when_set(client, db_session):
    """After feedback sets a preference, the mock agent's response should mention it."""
    conv_id = _create_conversation(client)

    # Send first message and get a message ID
    chat_resp = client.post(
        "/api/v1/chat",
        json={"conversation_id": conv_id, "message": "Help me prepare for an interview"},
    )
    msg_id = chat_resp.json()["message_id"]

    # Submit feedback with a preference-bearing text
    client.post(
        "/api/v1/feedback",
        json={
            "conversation_id": conv_id,
            "message_id": msg_id,
            "rating": 3,
            "feedback_text": "Give me more practical coding examples.",
        },
    )

    # Next chat response from the mock agent should mention preferences
    chat_resp2 = client.post(
        "/api/v1/chat",
        json={"conversation_id": conv_id, "message": "What should I study?"},
    )
    assert chat_resp2.status_code == 200
    response_text = chat_resp2.json()["response"]
    # The FixedMockAgent appends "(adapted to preferences)" when prefs exist
    assert "adapted to preferences" in response_text
