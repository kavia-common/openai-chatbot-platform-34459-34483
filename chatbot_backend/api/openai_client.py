import os
import requests
from typing import List, Dict, Optional


class OpenAIClientError(Exception):
    """Custom exception for OpenAI client errors."""


class OpenAIClient:
    """
    Thin wrapper around OpenAI Chat Completions API without LangChain/RAG.

    PUBLIC_INTERFACE
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize OpenAIClient.

        Args:
            api_key: OpenAI API key (read from OPENAI_API_KEY if None).
            model: Model to use (default gpt-4o-mini if not provided).
            base_url: Optional override for OpenAI API base URL.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        if not self.api_key:
            raise OpenAIClientError("OPENAI_API_KEY is not configured in environment.")

    # PUBLIC_INTERFACE
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: Optional[int] = None) -> str:
        """
        Call OpenAI Chat Completions API and return the assistant message content.

        Args:
            messages: List of dicts with role and content.
            temperature: Sampling temperature.
            max_tokens: Optional limit for response length.

        Returns:
            The assistant message content as string.

        Raises:
            OpenAIClientError on failures or unexpected responses.
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
        except requests.RequestException as e:
            raise OpenAIClientError(f"Network error calling OpenAI: {e}") from e

        if resp.status_code >= 400:
            raise OpenAIClientError(f"OpenAI API error {resp.status_code}: {resp.text}")

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception as e:
            raise OpenAIClientError(f"Unexpected OpenAI response format: {data}") from e
        return content
