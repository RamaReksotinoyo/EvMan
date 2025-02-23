# python -Wd manage.py test core/tests -v 3
# python -Wd manage.py test core.tests.test_units -v 3

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Received a naive datetime")

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser, User
from ..apis import IsAuthenticatedExceptPaths
from ..authentication import JWTCookieAuthentication
from core.utils.base_response import BaseResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status


class IsAuthenticatedExceptPathsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsAuthenticatedExceptPaths()
        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def test_public_get_events(self):
        """GET /api/events/ without authentication must be allowed"""
        request = self.factory.get('/api/events/')
        request.user = AnonymousUser()
        self.assertTrue(self.permission.has_permission(request, None))

    def test_public_post_attendees(self):
        """POST /api/attendees/ without authentication must be allowed"""
        request = self.factory.post('/api/attendees/')
        request.user = AnonymousUser()
        self.assertTrue(self.permission.has_permission(request, None))

    def test_authenticated_access(self):
        """Logged-in user must be able to access any endpoint"""
        request = self.factory.get('/api/protected/')
        request.user = self.user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_protected_post_events(self):
        """POST /api/events/ without authentication should be rejected"""
        request = self.factory.post('/api/events/')
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))

    def test_protected_get_without_auth(self):
        """GET /api/protected/ without authentication should be rejected"""
        request = self.factory.get('/api/protected/')
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))


class JWTCookieAuthenticationTest(TestCase):
    def setUp(self):
        """ Setup database for testing """
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword123'
        )
        self.access_token = str(AccessToken.for_user(self.user))
        self.authentication = JWTCookieAuthentication()

    def test_authenticate_with_valid_token(self):
        # Create request with valid token in cookies
        request = self.factory.get('/')
        request.COOKIES['access_token'] = self.access_token

        # Run authentication
        user, token = self.authentication.authenticate(request)

        # Verify
        self.assertEqual(user, self.user)
        self.assertEqual(token.payload['user_id'], self.user.id)
        
    def test_authenticate_without_token(self):
        # Create request without token
        request = self.factory.get('/')

        # Verify that AuthenticationFailed appears
        with self.assertRaises(AuthenticationFailed) as context:
            self.authentication.authenticate(request)

        # Statuscode verification (401 Unauthorized)
        self.assertEqual(context.exception.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticate_with_invalid_token(self):
        # Create request with invalid token in cookies
        request = self.factory.get('/')
        request.COOKIES['access_token'] = 'invalid.token.here'

        # Verify that AuthenticationFailed appears
        with self.assertRaises(AuthenticationFailed) as context:
            self.authentication.authenticate(request)

        # Statuscode verification (401 Unauthorized)
        self.assertEqual(context.exception.status_code, status.HTTP_401_UNAUTHORIZED)