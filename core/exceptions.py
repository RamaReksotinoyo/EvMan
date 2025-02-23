from rest_framework.views import exception_handler
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    if isinstance(exc, AuthenticationFailed):
        return Response(
            {
                'success': False,
                'message': 'Invalid credentials',
                'data': None
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    return exception_handler(exc, context)

