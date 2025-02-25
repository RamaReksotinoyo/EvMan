# python -Wd manage.py test core/tests -v 3
# python -Wd manage.py test core.tests.test_units -v 3

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Received a naive datetime")

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser, User
# from ..apis import IsAuthenticatedExceptPaths
from ..authentication import IsAuthenticatedExceptPaths
from ..authentication import JWTCookieAuthentication
from core.utils.base_response import BaseResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status
from ..utils import helpers
from ..utils.limit import rate_limiter
from django.test import TestCase, RequestFactory
from django.core.cache import cache
from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from unittest.mock import patch
from datetime import datetime, timedelta
from rest_framework.test import APIClient


class IsAuthenticatedExceptPathsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsAuthenticatedExceptPaths()
        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def test_public_get_events(self):
        """GET /api/events/ without authentication must be allowed"""
        request = self.factory.get('/api/events/3fa85f64-5717-4562-b3fc-2c963f66afa6/details/')
        request.user = AnonymousUser()
        self.assertTrue(self.permission.has_permission(request, None))

# {'url': '/api/docs/', 'method': 'GET'},
    def test_public_get_docs(self):
        """GET /api/docs/ without authentication must be allowed"""
        request = self.factory.get('/api/docs/')
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

class TestSanitizeInput(TestCase):

    def test_basic_html_removal(self):
        input_text = "<p>Hello World</p>"
        expected = "Hello World"
        self.assertEqual(helpers.sanitize_input(input_text), expected)
    
    def test_nested_html_tags(self):
        input_text = "<div><span>Nested</span> Tags</div>"
        expected = "Nested Tags"
        self.assertEqual(helpers.sanitize_input(input_text), expected)
    
    def test_special_characters(self):
        input_text = "Hello & World"
        expected = "Hello & World"
        self.assertEqual(helpers.sanitize_input(input_text), expected)
    
    def test_script_tags(self):
        input_text = '<script>alert("XSS")</script>'
        expected = 'alert("XSS")'
        self.assertEqual(helpers.sanitize_input(input_text), expected)
    
    def test_mixed_content(self):
        input_text = '<p>Hello & <b>World</b></p>'
        expected = 'Hello &amp; World'
        self.assertEqual(helpers.sanitize_input(input_text), expected)
    
    def test_whitespace_handling(self):
        input_text = "  <p>Extra Space</p>  "
        expected = "Extra Space"
        self.assertEqual(helpers.sanitize_input(input_text), expected)
    
    def test_empty_string(self):
        input_text = ""
        expected = ""
        self.assertEqual(helpers.sanitize_input(input_text), expected)
    
    def test_only_special_chars(self):
        input_text = "<<>>&"
        # expected = "&lt;&lt;&gt;&gt;&amp;"
        expected = "&gt;&amp;"
        self.assertEqual(helpers.sanitize_input(input_text), expected)

    def test_malformed_html(self):
        input_text = "<p>Unclosed Tag <b>Bold</p>"
        expected = "Unclosed Tag Bold"
        self.assertEqual(helpers.sanitize_input(input_text), expected)

    def test_input_contains_lt_chars_but_valid(self):
        input_text = "CHARACTERISTICS OF CHILDREN`S DHF CASE <14 YEARS BASED ON MEDICAL RECORD DATA IN UNGARAN HOSPITAL, 2018"
        expected = "CHARACTERISTICS OF CHILDREN`S DHF CASE <14 YEARS BASED ON MEDICAL RECORD DATA IN UNGARAN HOSPITAL, 2018"
        self.assertEqual(helpers.sanitize_input(input_text), expected)
     
    def test_input_contains_and_chars_but_valid(self):
        input_text = "DESCRIPTIVE ANALYSIS ON CHARACTERISTICS & FACTORS RELATED TO INFANT MATERNAL DEATH IN KRATON REGIONAL HOSPITAL IN PEKALONGAN IN 2017"
        expected = "DESCRIPTIVE ANALYSIS ON CHARACTERISTICS & FACTORS RELATED TO INFANT MATERNAL DEATH IN KRATON REGIONAL HOSPITAL IN PEKALONGAN IN 2017"
        self.assertEqual(helpers.sanitize_input(input_text), expected)

    def test_input_contains_quote_chars_but_valid(self):
        input_text = 'PERANCANGAN REDESIGN VISUAL BRANDING "AZZAHRAH COFFEE & TRADITIONAL CAKE"'
        expected = 'PERANCANGAN REDESIGN VISUAL BRANDING "AZZAHRAH COFFEE & TRADITIONAL CAKE"'
        self.assertEqual(helpers.sanitize_input(input_text), expected)

    def test_input_contains_dash_chars_but_valid(self):
        input_text = "Analisis Anime Kanojo Okarishimasu Episode 6-10, Pergeseran Uchi-Soto Pada Karakter Shun & Ruka"
        expected = "Analisis Anime Kanojo Okarishimasu Episode 6-10, Pergeseran Uchi-Soto Pada Karakter Shun & Ruka"
        self.assertEqual(helpers.sanitize_input(input_text), expected)

    def test_tag_img_chars(self):
        input_text = '<img src=x onerror=alert("XSS")>'
        expected = ''
        self.assertEqual(helpers.sanitize_input(input_text), expected)

    def test_tag_iframe_chars(self):
        input_text = 'mari<iframe src="http://attacker.example.com/xss.html">kita coba dengan misi-misian'
        expected = 'marikita coba dengan misi-misian'
        self.assertEqual(helpers.sanitize_input(input_text), expected)

    def test_url_encoded_html_tags(self):
        input_text = "%3Cscript%3Ealert('XSS')%3C/script%3E"
        expected = "alert('XSS')"
        self.assertEqual(helpers.sanitize_input(input_text), expected)

    def test_html_entity_encoded_tags(self):
        input_text = "&lt;script&gt;alert('XSS')&lt;/script&gt;"
        expected = "alert('XSS')"
        self.assertEqual(helpers.sanitize_input(input_text), expected)

    def test_double_encoded_xss(self):
        input_text = "%26lt%3Bscript%26gt%3Balert('XSS')%26lt%3B/script%26gt%3B"
        expected = "alert('XSS')"
        self.assertEqual(helpers.sanitize_input(input_text), expected)

    def test_mixed_encoded_html(self):
        input_text = "%3Cp%3EHello <b>World%3C/p%3E"
        expected = "Hello World"
        self.assertEqual(helpers.sanitize_input(input_text), expected)

    def test_encoded_ampersand(self):
        input_text = "DESKRIPSI ANALISIS DATA%26INFORMASI"
        expected = "DESKRIPSI ANALISIS DATA&INFORMASI"
        self.assertEqual(helpers.sanitize_input(input_text), expected)