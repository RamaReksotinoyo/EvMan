"""
URL configuration for EvMan project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
# from core.apis import LoginView

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.apis import EventViewSet, SessionViewSet, AttendeeViewSet, TrackViewSet
from core.serializers import CustomTokenObtainPairView, CustomTokenRefreshView

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.permissions import AllowAny

router = DefaultRouter()
router.register(r'api/events', EventViewSet, basename='event')
router.register(r'api/sessions', SessionViewSet, basename='session')
router.register(r'api/attendees', AttendeeViewSet, basename='attende')
router.register(r'api/tracks', TrackViewSet, basename='track')

    # path("api/login/", LoginView.as_view(), name="auth-login"),


urlpatterns = [

    path('', include(router.urls)),
    # path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # path('api/schema/', SpectacularAPIView.as_view(permission_classes=[AllowAny]), name='schema'),
    # path('api/docs/', SpectacularSwaggerView.as_view(permission_classes=[AllowAny]), name='swagger-ui'),
    # path('api/redoc/', SpectacularRedocView.as_view(permission_classes=[AllowAny]), name='redoc'),
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=[AllowAny]), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[AllowAny]), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema', permission_classes=[AllowAny]), name='redoc'),

    path('admin/', admin.site.urls),

    path("api/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/refresh-token/", CustomTokenRefreshView.as_view(), name="token_refresh"),
]
