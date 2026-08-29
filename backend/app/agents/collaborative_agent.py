"""Collaborative Agent — abstract base and concrete implementations.

Architecture:
    AgentService (abstract)
        ├── GeminiAgentService  — real Gemini API calls
        └── MockAgentService    — deterministic responses for dev/test

The factory function `create_agent_service()` returns a cached singleton
based on the AGENT_MODE environment variable.
"""

import re
from abc import ABC, abstractmethod
from functools import lru_cache

from app.agents.prompts import SYSTEM_INSTRUCTION, build_system_prompt
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Type alias for conversation history
# ---------------------------------------------------------------------------
HistoryItem = dict[str, str]  # {"role": "user"|"assistant", "content": "..."}


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class AgentService(ABC):
    """Abstract interface for the agent backend.

    All concrete implementations must satisfy this contract so the rest of
    the application never imports Gemini types directly.
    """

    @abstractmethod
    async def generate_response(
        self,
        conversation_history: list[HistoryItem],
        user_message: str,
        preferences: dict[str, str],
    ) -> tuple[str, str]:
        """Generate an agent response.

        Args:
            conversation_history: Previous messages in the conversation
                (not including the current user_message).
            user_message: The latest message from the user.
            preferences: Active user preferences for this conversation.

        Returns:
            (response_text, response_type) — the agent's reply and a
            category string (e.g. 'clarifying_question', 'plan').
        """


# ---------------------------------------------------------------------------
# Gemini implementation
# ---------------------------------------------------------------------------
class GeminiAgentService(AgentService):
    """Calls the Google Gemini API using the google-genai SDK."""

    def __init__(self) -> None:
        try:
            import google.generativeai as genai  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is not installed. "
                "Run: pip install google-generativeai"
            ) from exc

        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY is not set. Add it to your .env file."
            )

        genai.configure(api_key=settings.google_api_key)
        self._model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=SYSTEM_INSTRUCTION,
        )
        logger.info("GeminiAgentService initialized with model=%s", settings.gemini_model)

    async def generate_response(
        self,
        conversation_history: list[HistoryItem],
        user_message: str,
        preferences: dict[str, str],
    ) -> tuple[str, str]:
        """Send conversation to Gemini and parse the response."""
        import asyncio

        system_prompt = build_system_prompt(preferences)

        # Rebuild the model with updated system prompt if preferences changed
        import google.generativeai as genai  # type: ignore[import]
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=system_prompt,
        )

        # Convert internal history format to Gemini SDK format
        gemini_history = [
            {
                "role": msg["role"] if msg["role"] == "user" else "model",
                "parts": [msg["content"]],
            }
            for msg in conversation_history
        ]

        try:
            chat = model.start_chat(history=gemini_history)
            # Run the blocking call in a thread pool
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: chat.send_message(user_message),
            )
            raw_text: str = response.text
            logger.debug("Gemini raw response: %s", raw_text[:200])
            return _parse_response(raw_text)

        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            raise RuntimeError("Agent failed to generate a response.") from exc


# ---------------------------------------------------------------------------
# Mock implementation
# ---------------------------------------------------------------------------
_MOCK_RESPONSES: list[tuple[str, str]] = [
    (
        "I'd love to help! To give you the best support, could you tell me:\n"
        "1. What specific goal or problem are you working on?\n"
        "2. What have you already tried?\n"
        "3. What does success look like for you?",
        "clarifying_question",
    ),
    (
        "Thanks for that context. Let me outline a practical approach for you:\n\n"
        "**Step 1 — Foundation**\nStart with the core concepts before moving to advanced topics.\n\n"
        "**Step 2 — Practice**\nWork through hands-on exercises to reinforce understanding.\n\n"
        "**Step 3 — Review**\nIdentify gaps and revisit weak areas.\n\n"
        "Does this plan work for you, or would you prefer a different approach?",
        "plan",
    ),
    (
        "Great question! Here's what I recommend:\n\n"
        "- Focus on the most important items first\n"
        "- Break your work into 25-minute focused sessions\n"
        "- Track your progress daily\n\n"
        "Would you like me to adjust this to better fit your situation?",
        "guidance",
    ),
    (
        "Understood! I'll keep that in mind and tailor my responses accordingly.",
        "acknowledgement",
    ),
]

_mock_response_index = 0


class MockAgentService(AgentService):
    """Returns deterministic mock responses — no API key required.

    Useful for local development, CI, and frontend testing.
    """

    async def generate_response(
        self,
        conversation_history: list[HistoryItem],
        user_message: str,
        preferences: dict[str, str],
    ) -> tuple[str, str]:
        global _mock_response_index  # noqa: PLW0603

        # Cycle through the mock responses
        text, response_type = _MOCK_RESPONSES[_mock_response_index % len(_MOCK_RESPONSES)]
        _mock_response_index += 1

        # Inject a preference acknowledgement if there are active preferences
        if preferences:
            pref_note = (
                "\n\n*(Note: I'm adapting based on your preferences: "
                + "; ".join(f"{k}: {v[:60]}" for k, v in preferences.items())
                + ")*"
            )
            text = text + pref_note

        logger.debug("MockAgentService returning response_type=%s", response_type)
        return text, response_type


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------
def _parse_response(raw_text: str) -> tuple[str, str]:
    """Extract response_type from the trailing JSON block Gemini appends.

    Falls back to 'answer' if parsing fails.
    """
    # Look for the last JSON object in the response
    pattern = r'\{"response_type":\s*"([^"]+)"\}'
    matches = re.findall(pattern, raw_text)

    if matches:
        response_type = matches[-1]
        # Remove the JSON block from the displayed text
        clean_text = re.sub(pattern, "", raw_text).rstrip()
        return clean_text, response_type

    return raw_text.rstrip(), "answer"


# ---------------------------------------------------------------------------
# Factory (singleton)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def create_agent_service() -> AgentService:
    """Instantiate and return a cached AgentService singleton.

    The instance is created once when the application starts and reused
    for every subsequent request, avoiding redundant Gemini client setup.
    """
    mode = settings.agent_mode.lower()
    if mode == "gemini":
        logger.info("Agent mode: gemini (real API)")
        return GeminiAgentService()
    else:
        logger.info("Agent mode: mock (no API calls)")
        return MockAgentService()
