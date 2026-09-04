from rest_framework.pagination import (
    PageNumberPagination,
)


class QuestionHistoryPagination(
    PageNumberPagination
):
    """
    Pagination for persisted question-answer history.
    """

    page_size = 20

    page_size_query_param = (
        "page_size"
    )

    max_page_size = 100