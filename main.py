from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from apify_client import ApifyClient
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any
from llm_service import analyze_with_llm
from twitter_service import post_to_twitter

# Configure logging to log API activity and errors
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="instagram_api.log",
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI application
app = FastAPI(
    title="Instagram Data Fetching API",
    description="API to fetch the latest post from any Instagram account and post summaries to Twitter",
    version="1.0.0",
)

# Enable CORS (Cross-Origin Resource Sharing) to allow external requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any domain
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Define response model for Instagram post API
class InstagramPostResponse(BaseModel):
    caption: str
    image_url: str
    timestamp: str
    likes: int
    comments: int
    post_url: str
    success: bool
    analysis: Optional[str] = None  # Optional field for AI analysis
    error: Optional[str] = None  # Optional field for error messages

# Define request model for posting a tweet
class TwitterPostRequest(BaseModel):
    content: str
    image_url: Optional[str] = None  # Image URL is optional

# Define response model for Twitter post API
class TwitterPostResponse(BaseModel):
    success: bool
    tweet_id: Optional[str] = None
    tweet_url: Optional[str] = None
    error: Optional[str] = None

async def get_latest_instagram_post(username: str = "bbcnews") -> Dict[str, Any]:
    """
    Fetches the latest Instagram post from a specified username using Apify.

    Args:
        username (str): Instagram username to scrape (default: bbcnews)

    Returns:
        dict: Contains information about the latest post or an error message
    """
    try:
        logger.info(f"Starting scrape for Instagram user: {username}")

        # Retrieve Apify API key from environment variables
        api_key = os.getenv("APIFY_API_KEY")
        if not api_key:
            logger.error("APIFY_API_KEY not found in environment variables")
            return {"success": False, "error": "API key not configured"}

        client = ApifyClient(api_key)  # Initialize Apify client

        # Configure input for Apify Instagram scraper
        run_input = {
            "directUrls": [f"https://www.instagram.com/{username}/"],
            "resultsType": "posts",
            "resultsLimit": 1,  # Fetch only the latest post
            "addParentData": False,
        }

        # Start Apify actor to fetch Instagram data
        logger.info("Calling Apify actor")
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)

        logger.info(
            f"Scrape completed. Getting results from dataset: {run['defaultDatasetId']}"
        )

        # Retrieve scraped posts
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        if not items:
            logger.warning(f"No posts found for user {username}")
            return {"success": False, "error": "No posts found"}

        # Extract the most recent post
        latest_post = items[0]
        logger.info(f"Retrieved latest post for {username}")

        # Structure the response
        result = {
            "caption": latest_post.get("caption", ""),
            "image_url": latest_post.get("displayUrl", ""),
            "timestamp": latest_post.get("timestamp", ""),
            "likes": latest_post.get("likesCount", 0),
            "comments": latest_post.get("commentsCount", 0),
            "post_url": latest_post.get("url", ""),
            "success": True,
        }

        return result

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error fetching Instagram post: {error_msg}")
        return {"success": False, "error": error_msg}

# Root endpoint to check if API is running
@app.get("/")
async def root():
    return {"message": "Instagram Data Fetching API is running"}

# Fetch Instagram post for a specific username
@app.get("/instagram/{username}", response_model=InstagramPostResponse)
async def get_instagram_post(username: str = "bbcnews"):
    """
    Fetches the latest Instagram post for a given username and analyzes it using an LLM.

    Args:
        username (str): Instagram username to fetch (default: bbcnews)

    Returns:
        Instagram post data along with AI-generated analysis.
    """
    result = await get_latest_instagram_post(username)

    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "Failed to fetch Instagram post"),
        )

    # Perform AI-based analysis on the Instagram post
    analysis = analyze_with_llm(result)
    result["analysis"] = analysis

    return result

# Fetch default Instagram post (BBC News)
@app.get("/instagram/", response_model=InstagramPostResponse)
async def get_default_instagram_post():
    """
    Fetches the latest post from the default BBC News Instagram account.
    """
    return await get_instagram_post("bbcnews")

# Post a tweet on Twitter
@app.post("/post-tweet", response_model=TwitterPostResponse)
async def post_tweet(request: TwitterPostRequest):
    """
    Posts a tweet to Twitter using the configured API credentials.

    Args:
        content (str): The tweet content (max 280 characters)
        image_url (Optional[str]): URL to an image to attach to the tweet

    Returns:
        Twitter post success or failure response.
    """
    result = post_to_twitter(request.content, request.image_url)

    if not result.get("success"):
        raise HTTPException(
            status_code=400, detail=result.get("error", "Failed to post tweet")
        )

    return result

# Automates Instagram to Twitter posting
@app.post("/auto-post/{username}")
async def auto_post(username: str = "bbcnews"):
    """
    Fetches the latest Instagram post, generates a tweet using LLM, and posts it to Twitter.

    Args:
        username (str): Instagram username to fetch (default: bbcnews)

    Returns:
        A response containing Instagram post details, generated tweet, and Twitter post details.
    """
    # Step 1: Fetch latest Instagram post
    insta_result = await get_latest_instagram_post(username)

    if not insta_result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=insta_result.get("error", "Failed to fetch Instagram post"),
        )

    # Step 2: Generate tweet content using AI
    tweet_content = analyze_with_llm(insta_result)

    # Step 3: Post tweet with the Instagram image
    tweet_result = post_to_twitter(tweet_content, insta_result.get("image_url"))

    # Return a comprehensive result
    return {
        "instagram": {
            "username": username,
            "caption": insta_result.get("caption"),
            "image_url": insta_result.get("image_url"),
        },
        "twitter": tweet_result,
        "generated_tweet": tweet_content,
    }

# Run FastAPI app using Uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
