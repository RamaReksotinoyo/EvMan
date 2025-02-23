import time
import jwt
from django.conf import settings
from typing import Tuple
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.response import Response
from core.utils.base_response import BaseResponse 

def generate_access_token(payload: dict) -> Tuple[str, int]:
    current_time = int(time.time())
    expired_at = current_time + 3600  # Token is valid for 1 hour (3600 seconds)

    payload.update({
        'exp': expired_at,
        'iat': current_time
    })

    access_token = jwt.encode(payload, settings.PRIVATE_KEY.encode('utf-8'), algorithm='RS256')
    return access_token, expired_at

def generate_refresh_token(payload: dict) -> str:
    refresh = RefreshToken.for_user(payload)
    return str(refresh)

def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.PUBLIC_KEY.encode('utf-8'), algorithms=['RS256'])
        return payload
    except jwt.ExpiredSignatureError:
        # raise Exception("Token has expired")
        return Response(BaseResponse.error_response("Invalid credentials"), status=400)
    except jwt.InvalidTokenError:
        # raise Exception("Invalid token")
        return Response(BaseResponse.error_response("Invalid credentials"), status=400)