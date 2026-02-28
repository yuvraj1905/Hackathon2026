from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

from app.services.llm_client import LLMClient, parse_json_response


class BaseAgent(ABC):
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "openai/gpt-4.1-nano",
        temperature: float = 0,
        timeout: float = 60.0,
        max_retries: int = 2
    ):
        self.model = model
        self.temperature = temperature
        self.llm_client = LLMClient(
            api_key=api_key,
            model=model,
            timeout=timeout,
            max_retries=max_retries
        )
    
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
        """
        return await self.llm_client.complete(
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens,
            response_format=response_format
        )
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response with robust error handling.
        
        Args:
            response: Raw string response from LLM
            
        Returns:
            Parsed JSON as dictionary
        """
        return parse_json_response(response)
    
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
