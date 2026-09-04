from rest_framework import serializers


class APIErrorBodySerializer(
    serializers.Serializer
):
    """
    Standard error body returned by the REST API.
    """

    code = serializers.CharField()
    message = serializers.CharField()

    details = serializers.JSONField(
        required=False,
    )


class APIErrorSerializer(
    serializers.Serializer
):
    """
    Standard API error response envelope.
    """

    error = APIErrorBodySerializer()


class HealthCheckSerializer(
    serializers.Serializer
):
    """
    Health check response.
    """

    status = serializers.CharField()
    database = serializers.CharField()
    version = serializers.CharField()