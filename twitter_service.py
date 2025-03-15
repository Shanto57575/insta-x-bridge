import os
import logging
import tweepy
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import requests
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class TwitterService:
    def __init__(self):
        """Initialize the Twitter service with API credentials."""
        # Retrieve API credentials from environment variables
        self.consumer_key = os.getenv("TWITTER_API_KEY")
        self.consumer_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

        # Check if credentials are available
        if not all(
            [
                self.consumer_key,
                self.consumer_secret,
                self.access_token,
                self.access_token_secret,
            ]
        ):
            logger.error("Twitter API credentials are not properly configured")
            self.client = None
        else:
            # Initialize the Twitter API client
            try:
                self.client = tweepy.Client(
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret,
                )
                # Initialize OAuth1UserHandler for media upload
                self.auth = tweepy.OAuth1UserHandler(
                    self.consumer_key,
                    self.consumer_secret,
                    self.access_token,
                    self.access_token_secret,
                )
                self.api = tweepy.API(self.auth)
                logger.info("Twitter API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter API client: {str(e)}")
                self.client = None

    def _download_image(self, image_url: str) -> Optional[BytesIO]:
        """
        Download an image from a URL and return it as a BytesIO object.

        Args:
            image_url (str): URL of the image to download.

        Returns:
            BytesIO: Image data in memory.
        """
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            return BytesIO(response.content)
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None

    def post_tweet(
        self, content: str, image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a tweet with optional media.

        Args:
            content (str): The tweet content.
            image_url (str, optional): URL to an image to attach to the tweet.

        Returns:
            dict: Result of the operation with status and details.
        """
        if not self.client:
            return {"success": False, "error": "Twitter API client not initialized"}

        if len(content) > 280:
            logger.warning("Tweet content exceeds 280 characters. Truncating...")
            content = content[:277] + "..."

        try:
            media_ids = []
            if image_url:
                # Download the image
                image_data = self._download_image(image_url)
                if image_data:
                    # Upload the image to Twitter
                    media = self.api.media_upload(filename="image.jpg", file=image_data)
                    media_ids.append(media.media_id)
                    logger.info(f"Image uploaded successfully: {media.media_id}")
                else:
                    logger.warning(
                        "Failed to download image. Proceeding without image."
                    )

            # Post the tweet with or without media
            if media_ids:
                response = self.client.create_tweet(text=content, media_ids=media_ids)
            else:
                response = self.client.create_tweet(text=content)

            tweet_id = response.data["id"]
            logger.info(f"Tweet posted successfully with ID: {tweet_id}")

            return {
                "success": True,
                "tweet_id": tweet_id,
                "tweet_url": f"https://twitter.com/user/status/{tweet_id}",
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error posting tweet: {error_msg}")
            return {"success": False, "error": error_msg}


twitter_service = TwitterService()


def post_to_twitter(content: str, image_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Wrapper function to post content to Twitter.

    Args:
        content (str): The tweet content.
        image_url (str, optional): URL to an image to attach to the tweet.

    Returns:
        dict: Result of the operation with status and details.
    """
    return twitter_service.post_tweet(content, image_url)
