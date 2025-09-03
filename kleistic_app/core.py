from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

def custom_exception_handler(exc, context):
    # Let DRF handle the error first
    response = exception_handler(exc, context)

    if isinstance(exc, (InvalidToken, TokenError)):
        return Response(
            {"error": "Your authentication token is invalid or has expired. Please log in again."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    return response
