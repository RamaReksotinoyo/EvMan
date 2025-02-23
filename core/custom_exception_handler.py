# core/custom_exception_handler.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    # Panggil exception handler default
    response = exception_handler(exc, context)

    if response is not None:
        # Format ulang respons error
        custom_response = {
            "success": False,
            "message": response.data.get("detail", "An error occurred"),
            "data": None
        }
        response.data = custom_response

    return response