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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="instagram_api.log",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Instagram Data Fetching API",
    description="API to fetch the latest post from any Instagram account and post summaries to Twitter",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InstagramPostResponse(BaseModel):
    caption: str
    image_url: str
    timestamp: str
    likes: int
    comments: int
    post_url: str
    success: bool
    analysis: Optional[str] = None
    error: Optional[str] = None


class TwitterPostRequest(BaseModel):
    content: str
    image_url: Optional[str] = None


class TwitterPostResponse(BaseModel):
    success: bool
    tweet_id: Optional[str] = None
    tweet_url: Optional[str] = None
    error: Optional[str] = None


async def get_latest_instagram_post(username: str = "bbcnews") -> Dict[str, Any]:
    """
    Fetches the latest Instagram post from the specified username using Apify.

    Args:
        username (str): Instagram username to scrape (default: bbcnews)

    Returns:
        dict: Contains information about the latest post
    """
    try:
        logger.info(f"Starting scrape for Instagram user: {username}")

        # Initialize the ApifyClient with API token
        api_key = os.getenv("APIFY_API_KEY")
        if not api_key:
            logger.error("APIFY_API_KEY not found in environment variables")
            return {"success": False, "error": "API key not configured"}

        client = ApifyClient(api_key)

        # Prepare the Actor input
        run_input = {
            "directUrls": [f"https://www.instagram.com/{username}/"],
            "resultsType": "posts",
            "resultsLimit": 1,  # We only need the most recent post
            "addParentData": False,
        }

        # Run the Actor and wait for it to finish
        logger.info("Calling Apify actor")
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)

        logger.info(
            f"Scrape completed. Getting results from dataset: {run['defaultDatasetId']}"
        )

        # Get the dataset items
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        if not items:
            logger.warning(f"No posts found for user {username}")
            return {"success": False, "error": "No posts found"}

        # Get the first post (most recent)
        latest_post = items[0]
        logger.info(f"Retrieved latest post for {username}")

        # Extract the required information
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


@app.get("/")
async def root():
    return {"message": "Instagram Data Fetching API is running"}


@app.get("/instagram/{username}", response_model=InstagramPostResponse)
async def get_instagram_post(username: str = "bbcnews"):
    """
    Fetches the latest post from the specified Instagram account and analyzes it with an LLM.

    - **username**: Instagram username to fetch (default: bbcnews)

    Returns the latest post with caption, image URL, and LLM analysis.
    """
    result = await get_latest_instagram_post(username)

    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "Failed to fetch Instagram post"),
        )

    # Add LLM analysis to the result
    analysis = analyze_with_llm(result)
    result["analysis"] = analysis

    return result


@app.get("/instagram/", response_model=InstagramPostResponse)
async def get_default_instagram_post():
    """
    Fetches the latest post from the default BBC News Instagram account.

    Returns the latest post with caption and image URL.
    """
    return await get_instagram_post("bbcnews")


@app.post("/post-tweet", response_model=TwitterPostResponse)
async def post_tweet(request: TwitterPostRequest):
    """
    Posts a tweet to Twitter using the configured API credentials.

    - **content**: The tweet content (max 280 characters)
    - **image_url**: Optional URL to an image to attach to the tweet

    Returns the result of the tweet posting operation.
    """
    result = post_to_twitter(request.content, request.image_url)

    if not result.get("success"):
        raise HTTPException(
            status_code=400, detail=result.get("error", "Failed to post tweet")
        )

    return result


@app.post("/auto-post/{username}")
async def auto_post(username: str = "bbcnews"):
    """
    Fetches the latest Instagram post, generates a tweet, and posts it to Twitter - all in one operation.

    - **username**: Instagram username to fetch (default: bbcnews)

    Returns the result of the entire operation.
    """
    # Step 1: Get the latest Instagram post
    insta_result = await get_latest_instagram_post(username)

    if not insta_result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=insta_result.get("error", "Failed to fetch Instagram post"),
        )

    # Step 2: Generate tweet content with LLM
    tweet_content = analyze_with_llm(insta_result)

    # Step 3: Post to Twitter
    tweet_result = post_to_twitter(tweet_content, insta_result.get("image_url"))

    # Return comprehensive result
    return {
        "instagram": {
            "username": username,
            "caption": insta_result.get("caption"),
            "image_url": insta_result.get("image_url"),
        },
        "twitter": tweet_result,
        "generated_tweet": tweet_content,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
