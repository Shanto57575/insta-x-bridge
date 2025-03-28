import os
from groq import Groq
from typing import Dict, Any


def analyze_with_llm(post_data: Dict[str, Any]) -> str:
    """
    Send the Instagram post data to Groq for analysis.

    Args:
        post_data (dict): Instagram post data.

    Returns:
        str: Analysis result from the LLM.
    """
    if not post_data:
        return "No data available to analyze."

    try:
        # Prepare prompt for the LLM to convert an Instagram post into a tweet
        prompt = f"""
            Rewrite the following Instagram post into a concise, engaging tweet (max 280 characters) 
            that conveys the core message without directly stating that it's a summary.
            The output should ONLY contain the tweet text. Do NOT add any commentary, 
            explanations, or notes about the tweet.

            Instagram Post Details:
            - Caption: {post_data['caption']}
            - Posted on: {post_data['timestamp']}
            - Engagement: {post_data['likes']} likes, {post_data['comments']} comments

            Tweet Text:
        """

        # Initialize Groq client using API key from environment variables
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Send the prompt to Groq for text generation
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Specify the LLM model to use
            messages=[
                {
                    "role": "system",
                    "content": "You are a social media assistant. Your task is to convert Instagram captions "
                               "into concise, engaging, and well-structured tweets within 280 characters.",
                },
                {"role": "user", "content": prompt},  # Provide the user prompt
            ],
        )

        # Extract the generated tweet text from the response
        tweet_text = response.choices[0].message.content.strip()

        # Ensure the tweet text does not exceed 280 characters (Twitter's limit)
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."  # Trim and add ellipsis if too long

        return tweet_text

    except Exception as e:
        # Return error message if the LLM call fails
        return f"Error during analysis: {str(e)}"
