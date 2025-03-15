from fastapi.testclient import TestClient
from main import app
import pytest
from unittest.mock import patch, AsyncMock

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Instagram Data Fetching API is running"}

@patch("main.get_latest_instagram_post")
@patch("main.analyze_with_llm")
def test_get_instagram_post_endpoint(mock_analyze, mock_get_instagram):
    # Configure mocks
    mock_get_instagram.return_value = AsyncMock(return_value={
        "caption": "Test Instagram caption",
        "image_url": "https://example.com/image.jpg",
        "timestamp": "2023-04-01",
        "likes": 1000,
        "comments": 50,
        "post_url": "https://instagram.com/p/123",
        "success": True
    })()
    mock_analyze.return_value = "Analysis result"
    
    # Test the endpoint
    response = client.get("/instagram/testuser")
    
    assert response.status_code == 200
    data = response.json()
    assert data["caption"] == "Test Instagram caption"
    assert data["analysis"] == "Analysis result"
    assert data["success"] is True

@patch("main.get_latest_instagram_post")
def test_get_instagram_post_failure(mock_get_instagram):
    # Configure mock to return error
    mock_get_instagram.return_value = AsyncMock(return_value={
        "success": False,
        "error": "Failed to fetch data"
    })()
    
    # Test endpoint with error
    response = client.get("/instagram/nonexistent")
    
    assert response.status_code == 404
    assert "detail" in response.json()
    assert "Failed to fetch data" in response.json()["detail"]

@patch("main.post_to_twitter")
def test_post_tweet_endpoint(mock_post_to_twitter):
    # Configure mock
    mock_post_to_twitter.return_value = {
        "success": True,
        "tweet_id": "1234567890",
        "tweet_url": "https://twitter.com/user/status/1234567890"
    }
    
    # Test the endpoint
    response = client.post(
        "/post-tweet",
        json={"content": "Test tweet"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["tweet_id"] == "1234567890"

@patch("main.get_latest_instagram_post")
@patch("main.analyze_with_llm")
@patch("main.post_to_twitter")
def test_auto_post_endpoint(mock_post_twitter, mock_analyze, mock_get_instagram):
    # Configure mocks for auto-post workflow
    mock_get_instagram.return_value = AsyncMock(return_value={
        "caption": "Instagram post",
        "image_url": "https://example.com/image.jpg",
        "success": True
    })()
    mock_analyze.return_value = "Generated tweet"
    mock_post_twitter.return_value = {
        "success": True,
        "tweet_id": "1234567890"
    }
    
    # Test the auto-post endpoint
    response = client.post("/auto-post/testuser")
    
    assert response.status_code == 200
    data = response.json()
    assert data["instagram"]["username"] == "testuser"
    assert data["twitter"]["success"] is True
    assert data["generated_tweet"] == "Generated tweet"