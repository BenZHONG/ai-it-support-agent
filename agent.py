# agent.py

from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)

from config import get_api_key, get_model
from prompts import IT_SUPPORT_SYSTEM_PROMPT


class ITSupportAgent:
    """Stage 2: LLM-powered IT Support Assistant."""

    def __init__(
        self,
        client: Any | None = None,
        model: str | None = None,
    ) -> None:
        self.client = client or OpenAI(
            api_key=get_api_key(),
            timeout=30.0,
            max_retries=2,
        )

        self.model = model or get_model()

        # Conversation history stored in memory.
        self.history: list[dict[str, str]] = []

    def chat(self, message: str) -> str:
        """Send a message and return the AI response."""

        message = message.strip()

        if not message:
            raise ValueError("Message cannot be empty.")

        if len(message) > 4000:
            raise ValueError("Message is too long.")

        # Include previous successful conversation turns.
        conversation = [
            *self.history,
            {
                "role": "user",
                "content": message,
            },
        ]

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=IT_SUPPORT_SYSTEM_PROMPT,
                input=conversation,
                store=False,
                max_output_tokens=1200,
            )

            answer = (response.output_text or "").strip()

            if not answer:
                return "I could not generate an answer. Please try again."

        except RateLimitError:
            return (
                "The AI service is busy or has reached "
                "its usage limit. Please try again later."
            )

        except (APIConnectionError, APITimeoutError):
            return "I cannot connect to the AI service. Please try again later."

        except APIStatusError:
            return (
                "The AI service returned an error. "
                "Please contact IT support if it continues."
            )

        # Only save successful conversation turns.
        self.history.extend(
            [
                {
                    "role": "user",
                    "content": message,
                },
                {
                    "role": "assistant",
                    "content": answer,
                },
            ]
        )

        return answer

    def reset_conversation(self) -> None:
        """Clear the current conversation history."""
        self.history.clear()
