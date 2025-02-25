from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from datetime import datetime, timedelta
from .base_response import BaseResponse
from rest_framework import status
from rest_framework.response import Response


def rate_limiter(max_calls: int, time_frame: int, reset_time: int):
    """
    Rate limiter decorator untuk Django ViewSet.
    - max_calls: Jumlah maksimal permintaan dalam `reset_time` menit.
    - reset_time: Waktu reset cache dalam menit.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Ambil request dari parameter kedua
            ip_address = request.META.get('REMOTE_ADDR', 'unknown')
            cache_key = f"rate_limit:{ip_address}"
            request_data = cache.get(cache_key, {'count': 0, 'last_reset_time': datetime.now()})

            current_time = datetime.now()

            # Reset hitungan jika melewati reset_time menit
            if current_time >= request_data['last_reset_time'] + timedelta(minutes=reset_time):
                request_data = {'count': 0, 'last_reset_time': current_time}

            # Jika melewati batas rate limit
            if request_data['count'] >= max_calls:
                return Response(
                    BaseResponse.error_response("Rate limiter exceeded."),
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # Tambah hitungan
            request_data['count'] += 1
            cache.set(cache_key, request_data, timeout=reset_time * 60)

            return view_func(self, request, *args, **kwargs)

        return wrapper
    return decorator
