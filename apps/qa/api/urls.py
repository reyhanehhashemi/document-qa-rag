from django.urls import path

from .views import (
    AskQuestionAPIView,
    QuestionAnswerDetailAPIView,
    QuestionAnswerListAPIView,
)


urlpatterns = [
    path(
        "questions/ask/",
        AskQuestionAPIView.as_view(),
        name="question-ask",
    ),
    path(
        "questions/",
        QuestionAnswerListAPIView.as_view(),
        name="question-list",
    ),
    path(
        "questions/<int:pk>/",
        QuestionAnswerDetailAPIView.as_view(),
        name="question-detail",
    ),
]