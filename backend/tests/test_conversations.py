"""Tests for the conversations API."""


def test_create_conversation(client):
    response = client.post("/api/v1/conversations", json={"user_id": "test-user"})
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "test-user"
    assert "conversation_id" in data
    assert "created_at" in data


def test_create_conversation_missing_user_id(client):
    response = client.post("/api/v1/conversations", json={})
    assert response.status_code == 422


def test_create_conversation_empty_user_id(client):
    response = client.post("/api/v1/conversations", json={"user_id": ""})
    assert response.status_code == 422


def test_get_conversation_not_found(client):
    response = client.get("/api/v1/conversations/nonexistent-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"


def test_get_conversation_history(client):
    # Create a conversation
    create_resp = client.post("/api/v1/conversations", json={"user_id": "history-user"})
    conv_id = create_resp.json()["conversation_id"]

    # Send a message to populate history
    client.post("/api/v1/chat", json={"conversation_id": conv_id, "message": "Hello"})

    # Retrieve history
    history_resp = client.get(f"/api/v1/conversations/{conv_id}")
    assert history_resp.status_code == 200
    data = history_resp.json()
    assert data["conversation_id"] == conv_id
    assert len(data["messages"]) == 2  # user + assistant
    roles = [m["role"] for m in data["messages"]]
    assert "user" in roles
    assert "assistant" in roles


def test_delete_conversation(client):
    create_resp = client.post("/api/v1/conversations", json={"user_id": "del-user"})
    conv_id = create_resp.json()["conversation_id"]

    delete_resp = client.delete(f"/api/v1/conversations/{conv_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    # Should 404 now
    get_resp = client.get(f"/api/v1/conversations/{conv_id}")
    assert get_resp.status_code == 404


def test_delete_nonexistent_conversation(client):
    response = client.delete("/api/v1/conversations/does-not-exist")
    assert response.status_code == 404
