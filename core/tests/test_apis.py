import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Received a naive datetime")

from django.test import TestCase
from ..models import Event, Session, Attendee, Track
from rest_framework.test import APIClient
import uuid
from datetime import datetime, timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
import uuid
from django.urls import reverse
from django.test import TestCase


User = get_user_model()

class EventViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='fafifu',
            password='fafifu123'
        )
        self.client.force_authenticate(user=self.user)

        self.event1 = Event.objects.create(
            id=uuid.uuid4(),
            name="Event 1",
            start_date=now(),
            end_date=now() + timedelta(days=2),
            venue="ytta",
            description="ytta",
            capacity=50,
        )
        self.event2 = Event.objects.create(
            id=uuid.uuid4(),
            name="Event 2",
            start_date=now() + timedelta(days=5),
            end_date=now() + timedelta(days=7),
            venue="ytta",
            description="ytta",
            capacity=50,
        )

    def test_list_events(self):
        response = self.client.get('/api/events/')
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 2)

    def test_retrieve_event(self):
        response = self.client.get(f'/api/events/{self.event1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], "Event 1")

    def test_create_event(self):
        new_event_data = {
            "name": "New Event",
            "start_date": (now() + timedelta(days=10)).isoformat(),
            "end_date": (now() + timedelta(days=12)).isoformat(),
            "venue": "(now() + timedelta(days=12)).isoformat()",
            "description": "(now() + timedelta(days=12)).isoformat()",
            "capacity": 50
        }
        response = self.client.post('/api/events/', new_event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], "New Event")

    # def test_update_event(self):
    #     update_data = {
    #         "name": "Updated Event Name"
    #     }
    #     response = self.client.put(f'/api/events/{self.event1.id}/', update_data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertTrue(response.data['success'])
    #     self.assertEqual(response.data['data']['name'], "Updated Event Name")

    def test_delete_event(self):
        response = self.client.delete(f'/api/events/{self.event1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Event.objects.filter(id=self.event1.id).exists())
        


class AttendeeViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='fafifu',
            password='fafifu123'
        )
        self.client.force_authenticate(user=self.user)
        self.event = Event.objects.create(
            name="Tech Conference",
            description="Annual tech conference",
            start_date=datetime(2023, 12, 1, 10, 0),
            end_date=datetime(2023, 12, 1, 18, 0),
            venue="Convention Center",
            capacity=2
        )
        self.attendee_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "event": self.event.id
        }
        self.url = reverse('attende-list')

    def test_create_attendee_success(self):
        """ Test creating a valid attendee. """
        response = self.client.post(self.url, self.attendee_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Attendee.objects.count(), 1)
        self.assertEqual(response.data['message'], "Attendee created successfully")

    def test_create_attendee_duplicate_email(self):
        """ Test creating an attendee with duplicate email in the same event. """
        self.client.post(self.url, self.attendee_data, format='json')

        # Attendee kedua dengan email yang sama
        response = self.client.post(self.url, self.attendee_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "The fields email, event must make a unique set.")

    def test_create_attendee_event_capacity_reached(self):
        """ Test creating an attendee when event capacity is reached (negative case). """
        self.client.post(self.url, self.attendee_data, format='json')

        # Attendee kedua
        attendee2_data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "event": self.event.id
        }
        self.client.post(self.url, attendee2_data, format='json')

        # Attendee ketiga (melebihi kapasitas)
        attendee3_data = {
            "name": "Alice Smith",
            "email": "alice@example.com",
            "event": self.event.id
        }
        response = self.client.post(self.url, attendee3_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "Event capacity has been reached.")

    # def test_create_attendee_missing_event(self):
    #     """ Test creating an attendee without providing event. """
    #     invalid_data = {
    #         "name": "John Doe",
    #         "email": "john@example.com"
    #     }
    #     response = self.client.post(self.url, invalid_data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(response.data['message'], "Event is required.")

    def test_list_attendees_success(self):
        """ Test listing all attendees. """
        # Buat beberapa attendee
        Attendee.objects.create(
            name="John Doe",
            email="john@example.com",
            event=self.event
        )
        Attendee.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            event=self.event
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(len(response.data['data']), 2)
        # self.assertEqual(response.data['message'], "Attendees retrieved successfully")
        self.assertEqual(response.data['count'], 2)

    def test_list_attendees_by_event_success(self):
        """ Test listing attendees filtered by event ID (positive case). """
        # Buat beberapa attendee
        Attendee.objects.create(
            name="John Doe",
            email="john@example.com",
            event=self.event
        )
        Attendee.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            event=self.event
        )

        url = f"{self.url}by-event/{self.event.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)
        self.assertEqual(response.data['message'], "Attendees retrieved successfully")

    def test_list_attendees_by_event_not_found(self):
        """ Test listing attendees for a non-existent event. """
        non_existent_event_id = uuid.uuid4()
        url = f"{self.url}by-event/{non_existent_event_id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], "No attendees found for the given event")
