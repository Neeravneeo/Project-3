from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register():
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password", "full_name": "Test User"}
    )
    assert response.status_code == 201
    assert "access_token" in response.json()

def test_login():
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
