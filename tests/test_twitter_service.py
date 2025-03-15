import pytest
from unittest.mock import patch, MagicMock
from twitter_service import TwitterService, post_to_twitter

@pytest.fixture
def mock_tweepy_components():
    with patch('twitter_service.tweepy.Client') as mock_client, \
         patch('twitter_service.tweepy.API') as mock_api, \
         patch('twitter_service.tweepy.OAuth1UserHandler') as mock_auth:
        
        # Create mock tweet response
        mock_response = MagicMock()
        mock_response.data = {"id": "1234567890"}
        
        # Configure client
        mock_client_instance = MagicMock()
        mock_client_instance.create_tweet.return_value = mock_response
        mock_client.return_value = mock_client_instance
        
        # Configure media upload
        mock_media = MagicMock()
        mock_media.media_id = "media123"
        
        mock_api_instance = MagicMock()
        mock_api_instance.media_upload.return_value = mock_media
        mock_api.return_value = mock_api_instance
        
        yield {
            "client": mock_client,
            "api": mock_api,
            "auth": mock_auth
        }

def test_twitter_service_init():
    # Test initialization with credentials
    with patch('os.getenv', return_value='fake-credential'):
        service = TwitterService()
        assert service.client is not None
    
    # Test initialization without credentials
    with patch('os.getenv', side_effect=lambda x: None):
        service = TwitterService()
        assert service.client is None

def test_post_tweet_basic(mock_tweepy_components):
    with patch.multiple('os', getenv=lambda x: 'fake-credential'):
        service = TwitterService()
        service.client = mock_tweepy_components['client'].return_value
        service.api = mock_tweepy_components['api'].return_value
        
        result = service.post_tweet("Test tweet")
        
        assert result['success'] is True
        assert result['tweet_id'] == "1234567890"
        
        # Verify tweet was created with correct text
        mock_tweepy_components['client'].return_value.create_tweet.assert_called_once_with(
            text="Test tweet"
        )

def test_post_tweet_with_image(mock_tweepy_components):
    with patch.multiple('os', getenv=lambda x: 'fake-credential'), \
         patch('twitter_service.requests.get') as mock_get:
        
        # Configure image download
        mock_response = MagicMock()
        mock_response.content = b'test image data'
        mock_get.return_value = mock_response
        
        service = TwitterService()
        service.client = mock_tweepy_components['client'].return_value
        service.api = mock_tweepy_components['api'].return_value
        
        result = service.post_tweet(
            "Tweet with image", 
            image_url="https://example.com/image.jpg"
        )
        
        assert result['success'] is True
        
        # Verify media was uploaded
        mock_tweepy_components['api'].return_value.media_upload.assert_called_once()
        
        # Verify tweet created with media ID
        mock_tweepy_components['client'].return_value.create_tweet.assert_called_once_with(
            text="Tweet with image",
            media_ids=["media123"]
        )

def test_post_to_twitter_wrapper():
    # Test the wrapper function
    with patch('twitter_service.twitter_service.post_tweet') as mock_post_tweet:
        mock_post_tweet.return_value = {"success": True}
        
        result = post_to_twitter("Test tweet")
        
        assert result["success"] is True
        mock_post_tweet.assert_called_once_with("Test tweet", None)