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


class TrackViewSetTest(APITestCase):
    def setUp(self):
        # User authentication
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)

        # Buat event untuk testing
        self.event = Event.objects.create(
            name="Tech Conference 2025",
            description="Annual tech conference for developers and engineers.",
            start_date="2025-11-15",
            end_date="2025-11-17",
            venue="Jakarta Convention Center",
            capacity=1000
        )

        # Track for testing
        self.track = Track.objects.create(
            name="Web Development",
            event=self.event
        )

    def test_create_track(self):
        """Test creating a new track."""
        url = reverse('track-list')
        data = {
            "name": "Data Science",
            "event": self.event.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Track.objects.count(), 2)  # Track awal + track baru

    def test_list_tracks(self):
        """Test retrieving a list of tracks."""
        url = reverse('track-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_track(self):
        """Test retrieving a single track by ID."""
        url = reverse('track-detail', args=[self.track.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['name'], "Web Development")

    def test_update_track(self):
        """Test updating a track."""
        url = reverse('track-detail', args=[self.track.id])
        data = {
            "name": "Advanced Web Development",
            "event": self.event.id
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.track.refresh_from_db()
        self.assertEqual(self.track.name, "Advanced Web Development")

    def test_delete_track(self):
        """Test deleting a track."""
        url = reverse('track-detail', args=[self.track.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Track.objects.count(), 0)  # Track sudah dihapus

    def test_create_track_with_invalid_event(self):
        """Test creating a track with an invalid event ID."""
        url = reverse('track-list')
        data = {
            "name": "Data Science",
            "event": "8f0f753e-9634-4a57-b9d4-40ec77238df2"  # Event ID tidak valid
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Validation error", response.data['message'])

    def test_create_track_with_empty_name(self):
        """Test creating a track with an empty name."""
        url = reverse('track-list')
        data = {
            "name": "",  # Empty track name
            "event": self.event.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Validation error", response.data['message'])

    def test_retrieve_nonexistent_track(self):
        """Test retrieving a track that does not exist."""
        url = reverse('track-detail', args=['8f0f753e-9634-4a57-b9d4-40ec77238df2'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Track not found", response.data['message'])

    def test_delete_nonexistent_track(self):
        """Test deleting a track that does not exist."""
        url = reverse('track-detail', args=['8f0f753e-9634-4a57-b9d4-40ec77238df2'])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Track not found", response.data['message'])


class SessionViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # User authentication
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)

        # Create event and track
        self.event = Event.objects.create(
            id=uuid.uuid4(),
            name="Test Event",
            start_date=now(),
            end_date=now() + timedelta(days=2),
            venue="ytta",
            description="ytta",
            capacity=50,
        )
        
        self.track = Track.objects.create(
            id=uuid.uuid4(),
            name="Test Track",
            event=self.event
        )

        # Create session
        self.session = Session.objects.create(
            id=uuid.uuid4(),
            title="Test Session",
            description="A test session",
            event=self.event,
            track=self.track,
            start_time=now() + timedelta(hours=1),
            end_time=now() + timedelta(hours=2),
            speaker="Test Speaker"
        )

        self.session_url = f"/api/sessions/{self.session.id}/"

    def test_create_session(self):
        """ Test creating new sesion """
        data = {
            "title": "New Session",
            "description": "A new session",
            "event": str(self.event.id),
            "track": str(self.track.id),
            "start_time": (now() + timedelta(hours=3)).isoformat(),
            "end_time": (now() + timedelta(hours=4)).isoformat(),
            "speaker": "New Speaker"
        }
        response = self.client.post("/api/sessions/", data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(response.data["message"], "Session created successfully")

    def test_list_sessions(self):
        """ Test get list of session """
        response = self.client.get("/api/sessions/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_session(self):
        """ Test retrieve session by ID """
        response = self.client.get(self.session_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(response.data["data"]["title"], self.session.title)

    def test_update_session(self):
        """ Test update session """
        updated_data = {
            "title": "Updated Session Title",
            "description": self.session.description,
            "event": str(self.event.id),
            "track": str(self.track.id),
            "start_time": self.session.start_time.isoformat(),
            "end_time": self.session.end_time.isoformat(),
            "speaker": self.session.speaker
        }
        response = self.client.put(self.session_url, updated_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(response.data["data"]["title"], "Updated Session Title")

    def test_delete_session(self):
        """ Test delete session """
        response = self.client.delete(self.session_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Session.objects.filter(id=self.session.id).exists(), False)

    def test_session_cannot_overlap(self):
        """ Test validasi: session cant collide with another session in the same track """
        overlapping_data = {
            "title": "Overlapping Session",
            "description": "Overlapping session test",
            "event": str(self.event.id),
            "track": str(self.track.id),
            "start_time": self.session.start_time.isoformat(),
            "end_time": (self.session.start_time + timedelta(hours=1)).isoformat(),
            "speaker": "Overlapping Speaker"
        }
        response = self.client.post("/api/sessions/", overlapping_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Session overlaps", response.data["message"])

    def test_session_must_be_within_event_dates(self):
        """ Test validasi: Session must be within the event date range """
        invalid_data = {
            "title": "Invalid Date Session",
            "description": "Invalid date session test",
            "event": str(self.event.id),
            "track": str(self.track.id),
            "start_time": (self.event.start_date - timedelta(days=1)).isoformat(),
            "end_time": (self.event.start_date + timedelta(hours=1)).isoformat(),
            "speaker": "Invalid Date Speaker"
        }
        response = self.client.post("/api/sessions/", invalid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Session must be within event duration", response.data["message"])

    def test_session_track_must_belong_to_event(self):
        """ Test validasi: Track must be suit with the event """
        new_event = Event.objects.create(
            id=uuid.uuid4(),
            name="Another Event",
            start_date=now(),
            end_date=now() + timedelta(days=3),
            venue="ytta",
            description="ytta",
            capacity=50,
        )

        invalid_data = {
            "title": "Invalid Track Session",
            "description": "Invalid track session test",
            "event": str(new_event.id),
            "track": str(self.track.id),  # This track belongs to a different event
            "start_time": (now() + timedelta(hours=5)).isoformat(),
            "end_time": (now() + timedelta(hours=6)).isoformat(),
            "speaker": "Invalid Track Speaker"
        }
        response = self.client.post("/api/sessions/", invalid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Track does not belong to the selected event", response.data["message"])