from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import httpx
import json
import os
from asyncio import sleep


class BaseAgent(ABC):
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "openai/gpt-4o-mini",
        temperature: float = 0,
        timeout: float = 60.0,
        max_retries: int = 2
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")
    
    async def call_llm(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Dict[str, str]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Call OpenRouter API with retry logic and error handling.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            response_format: Optional format spec, e.g. {"type": "json_object"}
            temperature: Override default temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Raw string response from the model
            
        Raises:
            httpx.HTTPError: On API failures after retries
            ValueError: On invalid response structure
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
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
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if "choices" not in data or len(data["choices"]) == 0:
                        raise ValueError("Invalid response structure from API")
                    
                    content = data["choices"][0]["message"]["content"]
                    return content
                    
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < self.max_retries:
                    await sleep(2 ** attempt)
                    continue
                raise
            except (KeyError, ValueError) as e:
                raise ValueError(f"Failed to parse API response: {str(e)}")
        
        if last_exception:
            raise last_exception
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response with robust error handling.
        
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
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's primary task.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Processed output data
        """
        pass
