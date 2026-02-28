"""
Centralized LLM Client for OpenRouter API

Single source of truth for all LLM calls in the application.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from asyncio import sleep

import httpx

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_MODEL = "openai/gpt-4.1-nano"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class LLMClient:
    """
    Centralized client for OpenRouter API calls.
    
    Usage:
        client = LLMClient()
        response = await client.complete(messages, max_tokens=1000)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Make a chat completion request to OpenRouter.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0 = deterministic)
            max_tokens: Maximum tokens in response
            response_format: Format spec, e.g. {"type": "json_object"}
            model: Override default model for this request
            
        Returns:
            Raw string response from the model
            
        Raises:
            httpx.HTTPError: On API failures after retries
            ValueError: On invalid response structure
        """
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{OPENROUTER_BASE_URL}/chat/completions",
                        json=payload,
                        headers=headers
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if "choices" not in data or len(data["choices"]) == 0:
                        raise ValueError("Invalid response structure from API")
                    
                    return data["choices"][0]["message"]["content"]
                    
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_exception = e
                logger.warning(
                    "LLM API request failed attempt=%d/%d error=%s",
                    attempt + 1,
                    self.max_retries + 1,
                    str(e)
                )
                if attempt < self.max_retries:
                    await sleep(2 ** attempt)
                    continue
                raise
            except (KeyError, ValueError) as e:
                raise ValueError(f"Failed to parse API response: {str(e)}")
        
        if last_exception:
            raise last_exception
    
    async def complete_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make a chat completion request and parse JSON response.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            model: Override default model
            
        Returns:
            Parsed JSON response as dictionary
        """
        response = await self.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            model=model
        )
        return parse_json_response(response)


def parse_json_response(response: str) -> Dict[str, Any]:
    """
    Parse JSON response with robust error handling.
    Handles markdown code blocks and whitespace.
    
    Args:
        response: Raw string response from LLM
        
    Returns:
        Parsed JSON as dictionary
        
    Raises:
        ValueError: If JSON parsing fails
    """
    try:
        response = response.strip()
        
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        return json.loads(response)
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {str(e)}\nResponse: {response[:200]}")


# Global instance for convenience (lazy initialization)
_default_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the default LLM client instance."""
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client


async def llm_complete(
    messages: List[Dict[str, str]],
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    response_format: Optional[Dict[str, str]] = None,
    model: str = DEFAULT_MODEL
) -> str:
    """
    Convenience function for one-off LLM calls.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        response_format: Format spec
        model: Model to use
        
    Returns:
        Raw string response from the model
    """
    client = get_llm_client()
    return await client.complete(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        model=model
    )


async def llm_complete_json(
    messages: List[Dict[str, str]],
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Convenience function for one-off LLM calls with JSON response.
    
    Args:
        messages: List of message dicts
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        model: Model to use
        
    Returns:
        Parsed JSON response as dictionary
    """
    client = get_llm_client()
    return await client.complete_json(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        model=model
    )
