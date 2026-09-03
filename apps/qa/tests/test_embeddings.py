from unittest.mock import patch

from django.test import SimpleTestCase

from apps.qa.services.embeddings import (
    embed_query,
    embed_texts,
)
from apps.qa.services.exceptions import (
    EmbeddingServiceError,
)


class FakeEmbeddingModel:
    def encode(
        self,
        texts,
        batch_size,
        show_progress_bar,
        convert_to_numpy,
        normalize_embeddings,
    ):
        return [
            [1.0] + [0.0] * 383
            for _ in texts
        ]


class EmbeddingServiceTests(SimpleTestCase):
    @patch(
        "apps.qa.services.embeddings.get_embedding_model"
    )
    def test_embed_texts_returns_384_dimension_vectors(
        self,
        mocked_get_model,
    ):
        mocked_get_model.return_value = (
            FakeEmbeddingModel()
        )

        vectors = embed_texts(
            [
                "First text",
                "Second text",
            ]
        )

        self.assertEqual(
            len(vectors),
            2,
        )

        self.assertEqual(
            len(vectors[0]),
            384,
        )

        self.assertEqual(
            len(vectors[1]),
            384,
        )

    @patch(
        "apps.qa.services.embeddings.get_embedding_model"
    )
    def test_embed_query_returns_single_vector(
        self,
        mocked_get_model,
    ):
        mocked_get_model.return_value = (
            FakeEmbeddingModel()
        )

        vector = embed_query(
            "What is this document about?"
        )

        self.assertEqual(
            len(vector),
            384,
        )

    def test_empty_query_is_rejected(self):
        with self.assertRaises(
            EmbeddingServiceError
        ):
            embed_query(
                "   "
            )

    def test_empty_text_list_is_rejected(self):
        with self.assertRaises(
            EmbeddingServiceError
        ):
            embed_texts(
                []
            )

    @patch(
        "apps.qa.services.embeddings.get_embedding_model"
    )
    def test_invalid_embedding_dimension_is_rejected(
        self,
        mocked_get_model,
    ):
        class InvalidDimensionModel:
            def encode(
                self,
                texts,
                batch_size,
                show_progress_bar,
                convert_to_numpy,
                normalize_embeddings,
            ):
                return [
                    [1.0, 2.0]
                    for _ in texts
                ]

        mocked_get_model.return_value = (
            InvalidDimensionModel()
        )

        with self.assertRaises(
            EmbeddingServiceError
        ):
            embed_texts(
                ["Test text"]
            )