# Instagram to Twitter Posting Service

## System Overview and Architecture

This service fetches the latest posts from Instagram accounts, uses an LLM to summarize the captions into tweet-length content, and posts them to Twitter. The system consists of three main components:

1. **Instagram Data Fetching Service**: Retrieves the latest post from any Instagram account using the Apify scraping platform.
2. **LLM Summarization Module**: Uses Groq's LLaMA 3.3 model to convert Instagram captions into Twitter-friendly summaries.
3. **Twitter Integration Service**: Posts the generated summaries to Twitter, with support for attaching images.

## Setup Instructions

### Prerequisites

- Python 3.11
- pip (Python package manager)
- Accounts for the following services:
  - Apify (for Instagram scraping)
  - Groq (for LLM summarization)
  - Twitter Developer Account (for posting tweets)

### Environment Variables

A sample environment file `.env.template` is included for reference. Copy this file and rename it to `.env` to configure your environment variables.

Create a `.env` file in the root directory with the following variables:

```
# Apify API
APIFY_API_KEY=your_apify_api_key

# Groq API
GROQ_API_KEY=your_groq_api_key

# Twitter API
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
```

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/instagram-to-twitter.git
   cd instagram-to-twitter
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## API Endpoints

### 1. Get Instagram Post

**Endpoint:** `/instagram/{username}`  
**Method:** GET  
**Description:** Fetches the latest post from the specified Instagram account and analyzes it with the LLM.

**Parameters:**

- `username` (string): Instagram username to fetch (default: "bbcnews")

**Response:**

```json
{
	"caption": "The full Instagram caption",
	"image_url": "URL to the post image",
	"timestamp": "Post timestamp",
	"likes": 1000,
	"comments": 50,
	"post_url": "URL to the Instagram post",
	"success": true,
	"analysis": "LLM-generated tweet summary"
}
```

### 2. Post Tweet

**Endpoint:** `/post-tweet`  
**Method:** POST  
**Description:** Posts a tweet to Twitter using the configured API credentials.

**Request Body:**

```json
{
	"content": "Tweet content (max 280 characters)",
	"image_url": "Optional URL to attach an image"
}
```

**Response:**

```json
{
	"success": true,
	"tweet_id": "1234567890",
	"tweet_url": "https://twitter.com/user/status/1234567890"
}
```

### 3. Auto-Post

**Endpoint:** `/auto-post/{username}`  
**Method:** POST  
**Description:** Performs the entire workflow: fetches the latest Instagram post, generates a tweet, and posts it to Twitter.

**Parameters:**

- `username` (string): Instagram username to fetch (default: "bbcnews")

**Response:**

```json
{
	"instagram": {
		"username": "bbcnews",
		"caption": "The Instagram caption",
		"image_url": "URL to the post image"
	},
	"twitter": {
		"success": true,
		"tweet_id": "1234567890",
		"tweet_url": "https://twitter.com/user/status/1234567890"
	},
	"generated_tweet": "The generated tweet content"
}
```

## Customization

### Changing Target Instagram Username

The service is designed to work with any public Instagram account. You can change the target username in three ways:

1. **API Parameter**: Pass the username as a parameter in the API endpoints:

   ```
   GET /instagram/bbcnews
   POST /auto-post/bbcnews
   ```

2. **Default Value**: Change the default username in the function parameters:

   ```python
   async def get_instagram_post(username: str = "your_default_username"):
   ```

3. **Environment Variable**: Add a `DEFAULT_INSTAGRAM_USERNAME` variable to your `.env` file and update the code to use it.

### Customizing LLM Behavior

The LLM prompt can be customized in the `llm_service.py` file. You can modify the system prompt or the user prompt to change how the LLM generates tweet content.

### Local Development

Run the FastAPI application locally:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

The API docs will be available at `http://localhost:8000/docs`
