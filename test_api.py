import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base_class import Base
from app.db.init_db import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def authenticated_client():
    # Create a user
    client.post(
        "/api/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    
    # Login to get token
    response = client.post(
        "/api/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    
    # Create a new client with authentication headers
    client.headers = {
        "Authorization": f"Bearer {token}"
    }
    return client

def test_create_user():
    response = client.post(
        "/api/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"

def test_login():
    # First create a user
    client.post(
        "/api/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    
    # Then try to login
    response = client.post(
        "/api/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_create_post(authenticated_client):
    response = authenticated_client.post(
        "/api/posts",
        json={"title": "Test Post", "content": "Test Content"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Test Post"

def test_read_posts(authenticated_client):
    response = authenticated_client.get("/api/posts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_post(authenticated_client):
    # First create a post
    post = authenticated_client.post(
        "/api/posts",
        json={"title": "Original", "content": "Original"}
    ).json()
    
    # Then update it
    response = authenticated_client.put(
        f"/api/posts/{post['id']}",
        json={"title": "Updated", "content": "Updated"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"

def test_delete_post(authenticated_client):
    # First create a post
    post = authenticated_client.post(
        "/api/posts",
        json={"title": "To Delete", "content": "To Delete"}
    ).json()
    
    # Then delete it
    response = authenticated_client.delete(f"/api/posts/{post['id']}")
    assert response.status_code == 200 