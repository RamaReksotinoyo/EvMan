# from drf_spectacular.extensions import OpenApiAuthenticationExtension
# from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny
# from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
# from rest_framework import status
# from django.contrib.auth import authenticate
# from core.utils.token import generate_access_token, generate_refresh_token, verify_access_token
# from core.utils.base_response import BaseResponse 
# from rest_framework import serializers
# from .models import Event
# from rest_framework import viewsets
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.authentication import BaseAuthentication
# from rest_framework import exceptions
# from django.contrib.auth.models import User
# from django.contrib.auth import get_user_model

# class JWTAuth(BaseAuthentication):
#     def authenticate(self, request):
#         auth_header = request.headers.get('Authorization')
#         if not auth_header:
#             return None

#         try:
#             token = auth_header.split(' ')[1]
#             payload = verify_access_token(token)
#             user = User.objects.get(id=payload['user_id'])
#             return (user, None)
#         except Exception as e:
#             raise exceptions.AuthenticationFailed({
#                 'success': False,
#                 'message': 'Invalid credentials',
#                 'data': None
#             })


# class JWTBearerTokenScheme(OpenApiAuthenticationExtension):
#     # target_class = 'rest_framework_simplejwt.authentication.JWTAuthentication'
#     target_class = 'core.auth_scheme.JWTAuthentication'
#     name = 'JWTAuth'

#     def get_security_definition(self):
#         return {
#             'type': 'http',
#             'scheme': 'bearer',
#             'bearerFormat': 'JWT',
#         }

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed
from .utils.base_response import BaseResponse
import re


# class JWTCookieAuthentication(JWTAuthentication):
#     def authenticate(self, request):
#         # Jika request mengarah ke /api/docs/, abaikan autentikasi
#         if request.path.startswith('/api/docs/') or request.path.startswith('/api/attendees/') or request.path.startswith('/api/schema/'):
#             return None

#         # Ambil token dari cookie
#         token = request.COOKIES.get('access_token')
#         if not token:
#             raise AuthenticationFailed(
#                 detail=BaseResponse.error_response("Authentication credentials were not provided.")
#             )

#         try:
#             validated_token = self.get_validated_token(token)
#             user = self.get_user(validated_token)
#             return user, validated_token
#         except AuthenticationFailed:
#             raise AuthenticationFailed(
#                 detail=BaseResponse.error_response("Invalid authentication token.")
#             )

class JWTCookieAuthentication(JWTAuthentication):
    PUBLIC_PATHS = [
        r'^/api/events/[^/]+/details/$', 
        r'^/api/events/current/$',
        r'^/api/schema/$',
        r'^/api/docs/$',
    ]

    def authenticate(self, request):
        current_path = request.path
        current_method = request.method

        if current_path == "/api/attendees/" and current_method == "POST":
            return None

        for pattern in self.PUBLIC_PATHS:
            if re.match(pattern, current_path):
                return None

        token = request.COOKIES.get('access_token')
        if not token:
            raise AuthenticationFailed(
                detail=BaseResponse.error_response("Authentication credentials were not provided.")
            )

        try:
            validated_token = self.get_validated_token(token)
            user = self.get_user(validated_token)
            return user, validated_token
        except AuthenticationFailed:
            raise AuthenticationFailed(
                detail=BaseResponse.error_response("Invalid authentication token.")
            )


class IsAuthenticatedExceptPaths(BasePermission):
    PUBLIC_PATHS = [
        {'url': r'^/api/events/[^/]+/details/$', 'method': 'GET'},
        {'url': '/api/attendees/', 'method': 'POST'},
        {'url': '/api/events/current/', 'method': 'GET'},
        {'url': '/api/schema/', 'method': 'GET'},
        {'url': '/api/docs/', 'method': 'GET'},
    ]

    def has_permission(self, request, view):
        current_path = request.path
        current_method = request.method

        for path_config in self.PUBLIC_PATHS:
            url_pattern = path_config['url']

            if '{id}' in url_pattern:
                pattern = url_pattern.replace('{id}', '[^/]+')
                if re.match(pattern, current_path) and current_method == path_config['method']:
                    return True

            elif re.match(url_pattern, current_path) and current_method == path_config['method']:
                return True

        return request.user and request.user.is_authenticated
