from django import forms

from apps.documents.models import Document


class AskQuestionAdminForm(forms.Form):
    """
    Admin form used to ask a document-grounded question.
    """

    question = forms.CharField(
        label="Question",
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": (
                    "Enter a question about the indexed documents."
                ),
            }
        ),
    )

    documents = forms.ModelMultipleChoiceField(
        label="Documents",
        queryset=Document.objects.none(),
        required=False,
        help_text=(
            "Optional. Leave empty to search all indexed documents."
        ),
    )

    top_k = forms.IntegerField(
        label="Maximum retrieved chunks",
        min_value=1,
        max_value=10,
        initial=5,
        help_text=(
            "Maximum number of relevant chunks included "
            "in the RAG context."
        ),
    )

    min_similarity = forms.FloatField(
        label="Minimum similarity",
        min_value=0.0,
        max_value=1.0,
        initial=0.20,
        help_text=(
            "Chunks below this cosine similarity "
            "threshold will be ignored."
        ),
    )

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.fields["documents"].queryset = (
            Document.objects.filter(
                status=Document.Status.INDEXED,
            )
            .order_by(
                "title",
                "id",
            )
        )