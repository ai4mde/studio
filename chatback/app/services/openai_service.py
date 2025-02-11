from openai import AsyncOpenAI, APIError
from app.core.config import settings
import logging
from typing import List, Dict, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL_NAME
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        
        if not self.api_key:
            logger.warning("OpenAI API key not set. Using mock responses.")

    async def get_chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Get a chat completion from OpenAI API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
        
        Returns:
            str: The AI response text
        """
        if not self.client:
            mock_response = (
                "This is a mock response as OpenAI API key is not configured. "
                "Please set OPENAI_API_KEY in your environment variables."
            )
            logger.info(f"Returning mock response: {mock_response}")
            return mock_response

        try:
            logger.debug(f"Sending request to OpenAI with {len(messages)} messages")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            ai_response = response.choices[0].message.content
            logger.debug(f"Received response from OpenAI: {ai_response[:100]}...")
            return ai_response

        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI service: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while processing your request"
            )