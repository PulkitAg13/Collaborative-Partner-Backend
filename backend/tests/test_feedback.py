"""Tests for the /api/v1/feedback endpoint."""


def _create_and_chat(client, user_id: str = "fb-user") -> tuple[str, str]:
    """Helper: create a conversation and send one message. Returns (conv_id, msg_id)."""
    conv_resp = client.post("/api/v1/conversations", json={"user_id": user_id})
    conv_id = conv_resp.json()["conversation_id"]

    chat_resp = client.post(
        "/api/v1/chat",
        json={"conversation_id": conv_id, "message": "Help me."},
    )
    msg_id = chat_resp.json()["message_id"]
    return conv_id, msg_id


def test_submit_feedback_success(client):
    conv_id, msg_id = _create_and_chat(client)
    resp = client.post(
        "/api/v1/feedback",
        json={
            "conversation_id": conv_id,
            "message_id": msg_id,
            "rating": 5,
            "feedback_text": "Excellent, very practical!",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert "feedback_id" in data


def test_submit_feedback_without_text(client):
    conv_id, msg_id = _create_and_chat(client)
    resp = client.post(
        "/api/v1/feedback",
        json={
            "conversation_id": conv_id,
            "message_id": msg_id,
            "rating": 3,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["success"] is True


def test_feedback_invalid_rating_too_low(client):
    conv_id, msg_id = _create_and_chat(client)
    resp = client.post(
        "/api/v1/feedback",
        json={"conversation_id": conv_id, "message_id": msg_id, "rating": 0},
    )
    assert resp.status_code == 422


def test_feedback_invalid_rating_too_high(client):
    conv_id, msg_id = _create_and_chat(client)
    resp = client.post(
        "/api/v1/feedback",
        json={"conversation_id": conv_id, "message_id": msg_id, "rating": 6},
    )
    assert resp.status_code == 422


def test_feedback_nonexistent_conversation(client):
    resp = client.post(
        "/api/v1/feedback",
        json={
            "conversation_id": "nonexistent",
            "message_id": "nonexistent",
            "rating": 4,
        },
    )
    assert resp.status_code == 404


def test_feedback_wrong_conversation(client):
    """Message ID from a different conversation should be rejected."""
    conv1_id, msg_id = _create_and_chat(client, "user1")
    conv2_resp = client.post("/api/v1/conversations", json={"user_id": "user2"})
    conv2_id = conv2_resp.json()["conversation_id"]

    resp = client.post(
        "/api/v1/feedback",
        json={
            "conversation_id": conv2_id,
            "message_id": msg_id,  # belongs to conv1
            "rating": 4,
        },
    )
    assert resp.status_code == 404


def test_full_demo_scenario(client):
    """Integration test: create → chat → feedback → chat → preferences applied."""
    # Step 1: Create conversation
    conv_resp = client.post("/api/v1/conversations", json={"user_id": "demo-user"})
    assert conv_resp.status_code == 201
    conv_id = conv_resp.json()["conversation_id"]

    # Step 2: Send initial message
    chat1 = client.post(
        "/api/v1/chat",
        json={
            "conversation_id": conv_id,
            "message": "I want to prepare for a software engineering interview.",
        },
    )
    assert chat1.status_code == 200
    msg_id = chat1.json()["message_id"]

    # Step 3: Submit feedback with preference
    fb_resp = client.post(
        "/api/v1/feedback",
        json={
            "conversation_id": conv_id,
            "message_id": msg_id,
            "rating": 3,
            "feedback_text": "I prefer practical coding examples rather than theory.",
        },
    )
    assert fb_resp.status_code == 201

    # Step 4: Send another message — agent should now use preferences
    chat2 = client.post(
        "/api/v1/chat",
        json={"conversation_id": conv_id, "message": "What should I study first?"},
    )
    assert chat2.status_code == 200
    response_text = chat2.json()["response"]

    # The mock agent appends "(adapted to preferences)" when prefs are active
    assert "adapted to preferences" in response_text

    # Step 5: Verify full history is present
    history = client.get(f"/api/v1/conversations/{conv_id}").json()
    assert len(history["messages"]) == 4  # 2 user + 2 assistant

    # Step 6: Clean up
    del_resp = client.delete(f"/api/v1/conversations/{conv_id}")
    assert del_resp.json()["success"] is True
