from functools import lru_cache

from django.conf import settings
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)
from langchain_openrouter import ChatOpenRouter

from .exceptions import (
    LLMConfigurationError,
    LLMServiceError,
)


def validate_llm_configuration():
    """
    Validate required OpenRouter configuration.
    """
    if not settings.OPENROUTER_API_KEY:
        raise LLMConfigurationError(
            "OPENROUTER_API_KEY is not configured."
        )

    if not settings.OPENROUTER_MODEL:
        raise LLMConfigurationError(
            "OPENROUTER_MODEL is not configured."
        )

    if settings.OPENROUTER_MAX_TOKENS <= 0:
        raise LLMConfigurationError(
            "OPENROUTER_MAX_TOKENS must be greater than zero."
        )

    if settings.OPENROUTER_TIMEOUT_MS <= 0:
        raise LLMConfigurationError(
            "OPENROUTER_TIMEOUT_MS must be greater than zero."
        )

    if settings.OPENROUTER_MAX_RETRIES < 0:
        raise LLMConfigurationError(
            "OPENROUTER_MAX_RETRIES cannot be negative."
        )


@lru_cache(maxsize=1)
def get_chat_model():
    """
    Create and cache the configured LangChain OpenRouter model.
    """
    validate_llm_configuration()

    try:
        return ChatOpenRouter(
            model=settings.OPENROUTER_MODEL,
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            temperature=settings.OPENROUTER_TEMPERATURE,
            max_tokens=settings.OPENROUTER_MAX_TOKENS,
            timeout=settings.OPENROUTER_TIMEOUT_MS,
            max_retries=settings.OPENROUTER_MAX_RETRIES,
            app_url=settings.OPENROUTER_APP_URL or None,
            app_title=settings.OPENROUTER_APP_NAME or None,
        )
    except Exception as exc:
        raise LLMConfigurationError(
            "Unable to initialize the OpenRouter chat model."
        ) from exc


def extract_response_text(content):
    """
    Extract plain text from a LangChain chat response.
    """
    if isinstance(content, str):
        text = content.strip()

        if text:
            return text

    if isinstance(content, list):
        text_parts = []

        for block in content:
            if isinstance(block, str):
                value = block.strip()

                if value:
                    text_parts.append(
                        value
                    )

            elif isinstance(block, dict):
                value = block.get(
                    "text"
                )

                if isinstance(value, str):
                    value = value.strip()

                    if value:
                        text_parts.append(
                            value
                        )

        text = "\n".join(
            text_parts
        ).strip()

        if text:
            return text

    raise LLMServiceError(
        "The language model returned an empty response."
    )


def generate_llm_response(
    system_prompt,
    user_prompt,
):
    """
    Generate a text response through LangChain and OpenRouter.
    """
    if (
        not isinstance(system_prompt, str)
        or not system_prompt.strip()
    ):
        raise LLMServiceError(
            "System prompt cannot be empty."
        )

    if (
        not isinstance(user_prompt, str)
        or not user_prompt.strip()
    ):
        raise LLMServiceError(
            "User prompt cannot be empty."
        )

    model = get_chat_model()

    messages = [
        SystemMessage(
            content=system_prompt.strip(),
        ),
        HumanMessage(
            content=user_prompt.strip(),
        ),
    ]

    try:
        response = model.invoke(
            messages
        )
    except Exception as exc:
        raise LLMServiceError(
            "Unable to generate a response from OpenRouter."
        ) from exc

    return extract_response_text(
        response.content
    )