import httpx
import sys
import json

BASE_URL = "http://127.0.0.1:8000"

def log_section(title):
    print("\n" + "="*50)
    print(f" TESTING: {title}")
    print("="*50)

# 1. Health Check
log_section("GET /health")
try:
    resp = httpx.get(f"{BASE_URL}/health")
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text}")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
except Exception as e:
    print(f"Health Check Failed: {e}")
    sys.exit(1)

# 2. Create Conversation
log_section("POST /api/v1/conversations")
try:
    payload = {"user_id": "test-e2e-user"}
    resp = httpx.post(f"{BASE_URL}/api/v1/conversations", json=payload)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
    assert resp.status_code == 201
    conv_id = resp.json()["conversation_id"]
    print(f"Saved Conversation ID: {conv_id}")
except Exception as e:
    print(f"Conversation Creation Failed: {e}")
    sys.exit(1)

# 3. Chat Turn 1
log_section("POST /api/v1/chat (Turn 1)")
try:
    payload = {
        "conversation_id": conv_id,
        "message": "I want to prepare for a backend developer interview. What topics should I study?"
    }
    resp = httpx.post(f"{BASE_URL}/api/v1/chat", json=payload, timeout=60.0)
    print(f"Status Code: {resp.status_code}")
    data = resp.json()
    print(f"Response Type: {data['response_type']}")
    print(f"Response Text:\n{data['response']}")
    assert resp.status_code == 200
    msg_id = data["message_id"]
    print(f"Saved Message ID (for feedback): {msg_id}")
except Exception as e:
    print(f"Chat Turn 1 Failed: {e}")
    sys.exit(1)

# 4. Submit Feedback
log_section("POST /api/v1/feedback")
try:
    payload = {
        "conversation_id": conv_id,
        "message_id": msg_id,
        "rating": 2,
        "feedback_text": "Please be very brief and use concise bullet points. No conversational filler."
    }
    resp = httpx.post(f"{BASE_URL}/api/v1/feedback", json=payload)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
    assert resp.status_code == 201
    assert resp.json()["success"] is True
except Exception as e:
    print(f"Submit Feedback Failed: {e}")
    sys.exit(1)

# 5. Chat Turn 2 (Adaptive response testing)
log_section("POST /api/v1/chat (Turn 2 - testing preference adaptation)")
try:
    payload = {
        "conversation_id": conv_id,
        "message": "What database topics specifically should I review?"
    }
    resp = httpx.post(f"{BASE_URL}/api/v1/chat", json=payload, timeout=60.0)
    print(f"Status Code: {resp.status_code}")
    data = resp.json()
    print(f"Response Type: {data['response_type']}")
    print(f"Response Text:\n{data['response']}")
    assert resp.status_code == 200
except Exception as e:
    print(f"Chat Turn 2 Failed: {e}")
    sys.exit(1)

# 6. Get Conversation History
log_section("GET /api/v1/conversations/{id}")
try:
    resp = httpx.get(f"{BASE_URL}/api/v1/conversations/{conv_id}")
    print(f"Status Code: {resp.status_code}")
    data = resp.json()
    print(f"Total Messages: {len(data['messages'])}")
    for m in data['messages']:
        print(f"  [{m['role'].upper()}]: {m['content'][:80]}...")
    assert resp.status_code == 200
    # Expected 4 messages (User 1, Assistant 1, User 2, Assistant 2)
    assert len(data['messages']) == 4
except Exception as e:
    print(f"Get History Failed: {e}")
    sys.exit(1)

# 7. Delete Conversation
log_section("DELETE /api/v1/conversations/{id}")
try:
    resp = httpx.delete(f"{BASE_URL}/api/v1/conversations/{conv_id}")
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
except Exception as e:
    print(f"Delete Conversation Failed: {e}")
    sys.exit(1)

# 8. Verify Deletion
log_section("GET /api/v1/conversations/{id} (Verify Deleted)")
try:
    resp = httpx.get(f"{BASE_URL}/api/v1/conversations/{conv_id}")
    print(f"Status Code: {resp.status_code} (Expected: 404)")
    print(f"Response: {resp.text}")
    assert resp.status_code == 404
except Exception as e:
    print(f"Verification of Delete Failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print(" ALL API TESTS PASSED SUCCESSFULLY E2E!")
print("="*50)
