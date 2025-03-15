import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from main import get_latest_instagram_post

@pytest_asyncio.fixture
async def mock_apify_client():
    with patch('main.ApifyClient') as mock_client:
        # Setup mock dataset with sample Instagram post
        mock_dataset = MagicMock()
        mock_dataset.iterate_items.return_value = [
            {
                "caption": "Test Instagram caption",
                "displayUrl": "https://example.com/test.jpg",
                "timestamp": "2023-04-01T12:00:00Z",
                "likesCount": 1000,
                "commentsCount": 50,
                "url": "https://instagram.com/p/test123"
            }
        ]
        
        # Setup mock actor run
        mock_run = {"defaultDatasetId": "test-dataset-id"}
        mock_actor = MagicMock()
        mock_actor.call.return_value = mock_run
        
        # Configure client to return mocks
        mock_client_instance = MagicMock()
        mock_client_instance.actor.return_value = mock_actor
        mock_client_instance.dataset.return_value = mock_dataset
        
        mock_client.return_value = mock_client_instance
        yield mock_client

@pytest.mark.asyncio
async def test_get_latest_instagram_post_success(mock_apify_client):
    with patch('os.getenv', return_value='fake-api-key'):
        result = await get_latest_instagram_post('testuser')
        
        assert result['success'] is True
        assert result['caption'] == "Test Instagram caption"
        assert result['image_url'] == "https://example.com/test.jpg"
        
        # Verify correct API call
        call_args = mock_apify_client.return_value.actor().call.call_args[1]['run_input']
        assert call_args['directUrls'] == ["https://www.instagram.com/testuser/"]
        assert call_args['resultsLimit'] == 1

@pytest.mark.asyncio
async def test_get_latest_instagram_post_no_posts(mock_apify_client):
    # Configure empty dataset
    mock_apify_client.return_value.dataset.return_value.iterate_items.return_value = []
    
    with patch('os.getenv', return_value='fake-api-key'):
        result = await get_latest_instagram_post('testuser')
        assert result['success'] is False
        assert "No posts found" in result['error']

@pytest.mark.asyncio
async def test_get_latest_instagram_post_api_failure(mock_apify_client):
    # Configure API failure
    mock_apify_client.return_value.actor.return_value.call.side_effect = Exception("API error")
    
    with patch('os.getenv', return_value='fake-api-key'):
        result = await get_latest_instagram_post('testuser')
        assert result['success'] is False
        assert "API error" in result['error']