from fastapi.testclient import TestClient
from main import api

client = TestClient(api)

def test_audit_endpoint_success():
    """Verify the API returns 200 and the expected JSON structure."""
    payload = {
        "query": "Is the Kirkland site compliant?",
        "thread_id": "gateway_test_101"
    }
    # The first call should always pass
    response = client.post("/audit", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "content" in response.json()

def test_rate_limiting_trigger():
    """Verify that the 3rd request in a minute triggers a 429 error."""
    payload = {"query": "test", "thread_id": "limit_test"}
    
    # We already used 1 in the test above. Let's trigger the limit.
    client.post("/audit", json=payload) # 2nd request
    response = client.post("/audit", json=payload) # 3rd request
    
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text
    