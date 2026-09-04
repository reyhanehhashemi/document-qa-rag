from types import SimpleNamespace
from unittest.mock import patch

from django.test import (
    SimpleTestCase,
    override_settings,
)

from apps.qa.services.exceptions import (
    LLMConfigurationError,
    LLMServiceError,
)
from apps.qa.services.llm import (
    build_model_fallbacks,
    generate_llm_response,
    get_chat_model,
)


class LLMServiceTests(SimpleTestCase):
    def setUp(self):
        get_chat_model.cache_clear()

    def tearDown(self):
        get_chat_model.cache_clear()

    @override_settings(
        OPENROUTER_API_KEY="",
    )
    def test_missing_api_key_is_rejected(self):
        with self.assertRaises(
            LLMConfigurationError
        ):
            get_chat_model()

    @override_settings(
        OPENROUTER_MODEL="primary/model:free",
        OPENROUTER_FALLBACK_MODELS=[
            "fallback/one:free",
            "fallback/two:free",
        ],
    )
    def test_model_fallbacks_include_primary_first(self):
        models = build_model_fallbacks()

        self.assertEqual(
            models,
            [
                "primary/model:free",
                "fallback/one:free",
                "fallback/two:free",
            ],
        )

    @override_settings(
        OPENROUTER_MODEL="primary/model:free",
        OPENROUTER_FALLBACK_MODELS=[
            "primary/model:free",
            "fallback/model:free",
        ],
    )
    def test_model_fallbacks_remove_duplicates(self):
        models = build_model_fallbacks()

        self.assertEqual(
            models,
            [
                "primary/model:free",
                "fallback/model:free",
            ],
        )

    @override_settings(
        OPENROUTER_API_KEY="test-key",
        OPENROUTER_MODEL="primary/model:free",
        OPENROUTER_FALLBACK_MODELS=[
            "fallback/model:free",
        ],
        OPENROUTER_BASE_URL=(
            "https://openrouter.ai/api/v1"
        ),
        OPENROUTER_TEMPERATURE=0.0,
        OPENROUTER_MAX_TOKENS=512,
        OPENROUTER_TIMEOUT_MS=120000,
        OPENROUTER_MAX_RETRIES=1,
        OPENROUTER_APP_URL=(
            "http://localhost:8000"
        ),
        OPENROUTER_APP_NAME=(
            "Document QA RAG"
        ),
    )
    @patch(
        "apps.qa.services.llm.ChatOpenRouter"
    )
    def test_chat_model_uses_openrouter_settings(
        self,
        mocked_chat_openrouter,
    ):
        get_chat_model()

        mocked_chat_openrouter.assert_called_once_with(
            model="primary/model:free",
            api_key="test-key",
            base_url=(
                "https://openrouter.ai/api/v1"
            ),
            temperature=0.0,
            max_tokens=512,
            timeout=120000,
            max_retries=1,
            app_url="http://localhost:8000",
            app_title="Document QA RAG",
            model_kwargs={
                "models": [
                    "primary/model:free",
                    "fallback/model:free",
                ],
            },
        )

    @override_settings(
        OPENROUTER_API_KEY="test-key",
    )
    @patch(
        "apps.qa.services.llm.get_chat_model"
    )
    def test_generate_llm_response_returns_text(
        self,
        mocked_get_chat_model,
    ):
        fake_model = (
            mocked_get_chat_model.return_value
        )

        fake_model.invoke.return_value = (
            SimpleNamespace(
                content="  پاسخ آزمایشی  ",
            )
        )

        response = generate_llm_response(
            system_prompt=(
                "Answer the user."
            ),
            user_prompt=(
                "Test question."
            ),
        )

        self.assertEqual(
            response,
            "پاسخ آزمایشی",
        )

    def test_empty_prompt_is_rejected(self):
        with self.assertRaises(
            LLMServiceError
        ):
            generate_llm_response(
                system_prompt="",
                user_prompt="Valid question",
            )

        with self.assertRaises(
            LLMServiceError
        ):
            generate_llm_response(
                system_prompt="Valid system prompt",
                user_prompt="   ",
            )

    @override_settings(
        OPENROUTER_API_KEY="test-key",
    )
    @patch(
        "apps.qa.services.llm.get_chat_model"
    )
    def test_model_error_is_wrapped(
        self,
        mocked_get_chat_model,
    ):
        fake_model = (
            mocked_get_chat_model.return_value
        )

        fake_model.invoke.side_effect = RuntimeError(
            "Provider failed."
        )

        with self.assertRaises(
            LLMServiceError
        ):
            generate_llm_response(
                system_prompt="Answer the user.",
                user_prompt="Test question.",
            )