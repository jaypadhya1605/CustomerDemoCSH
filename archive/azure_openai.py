"""
Azure OpenAI Service wrapper for Conversational Analytics demo.
"""
import os
from dataclasses import dataclass
from typing import Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ChatResponse:
    """Response from Azure OpenAI with usage metadata."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    finish_reason: str


class AzureOpenAIService:
    """Wrapper for Azure OpenAI API calls with token tracking."""

    SYSTEM_PROMPT = """You are a clinical quality analytics assistant helping healthcare quality leaders
analyze VTE (Venous Thromboembolism) prevention performance data. You help identify:
- Performance trends against goals
- Departments or units needing improvement
- Opportunities to enhance VTE prophylaxis rates
- Patterns in clinical quality metrics

Be concise, data-driven, and actionable in your responses. When discussing metrics,
reference specific numbers and percentages when available."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: Optional[str] = None,
        deployment: Optional[str] = None,
    ):
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        self.deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")

        if not self.endpoint or not self.api_key:
            raise ValueError("Azure OpenAI endpoint and API key are required")

        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )

    def chat(
        self,
        user_message: str,
        conversation_history: Optional[list] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> ChatResponse:
        """
        Send a chat completion request and return response with usage metadata.

        Args:
            user_message: The user's input message
            conversation_history: Optional list of previous messages
            system_prompt: Optional custom system prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            ChatResponse with content and token usage
        """
        messages = [
            {"role": "system", "content": system_prompt or self.SYSTEM_PROMPT}
        ]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            max_completion_tokens=max_tokens,
        )

        choice = response.choices[0]
        usage = response.usage

        return ChatResponse(
            content=choice.message.content or "",
            model=response.model,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            finish_reason=choice.finish_reason,
        )

    def chat_with_context(
        self,
        user_message: str,
        vte_context: str,
        conversation_history: Optional[list] = None,
        max_tokens: int = 2048,
    ) -> ChatResponse:
        """
        Chat with VTE data context included in the system prompt.

        Args:
            user_message: The user's question
            vte_context: Summary of VTE data to include
            conversation_history: Previous messages
            max_tokens: Maximum response tokens

        Returns:
            ChatResponse with content and usage
        """
        enhanced_system_prompt = f"""{self.SYSTEM_PROMPT}

Current VTE Data Summary:
{vte_context}

Use this data to answer questions about VTE performance, identify trends,
and provide actionable recommendations."""

        return self.chat(
            user_message=user_message,
            conversation_history=conversation_history,
            system_prompt=enhanced_system_prompt,
            max_tokens=max_tokens,
        )


def test_connection():
    """Test the Azure OpenAI connection."""
    try:
        service = AzureOpenAIService()
        response = service.chat("Say 'Connection successful!' in exactly those words.")
        print(f"Response: {response.content}")
        print(f"Tokens used: {response.total_tokens}")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
