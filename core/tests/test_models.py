import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Received a naive datetime")

from django.test import TestCase
from django.core.exceptions import ValidationError
from ..models import Event, Session, Attendee, Track
from datetime import datetime


class EventModelTest(TestCase):
    def setUp(self):
        # Initial data for testing
        self.event1 = Event.objects.create(
            name="Naruto Conference",
            description="For naruto fans out there, come here, join with us",
            start_date=datetime(2023, 12, 1, 10, 0),
            end_date=datetime(2023, 12, 1, 18, 0),
            venue="Convention Center",
            capacity=1000
        )

    def test_event_creation(self):
        """Test creating a valid event."""
        event = Event(
            name="Workshop",
            description="Python workshop",
            start_date=datetime(2023, 12, 2, 10, 0),
            end_date=datetime(2023, 12, 2, 12, 0),
            venue="Room 666",
            capacity=50
        )
        event.full_clean()
        event.save()
        self.assertEqual(Event.objects.count(), 2)

    def test_event_overlap(self):
        """Test event overlap validation."""
        event = Event(
            name="Overlapping Event",
            description="This event overlaps with Tech Conference",
            start_date=datetime(2023, 12, 1, 12, 0),  # Overlaping with event1
            end_date=datetime(2023, 12, 1, 14, 0),
            venue="Room 123",
            capacity=50
        )
        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_event_no_overlap(self):
        """Test event with no overlap."""
        event = Event(
            name="Non-Overlapping Event",
            description="This event does not overlap with Tech Conference",
            start_date=datetime(2023, 12, 2, 10, 0),  # Tidak overlap dengan event1
            end_date=datetime(2023, 12, 2, 12, 0),
            venue="Room 103",
            capacity=50
        )
        event.full_clean()
        event.save()
        self.assertEqual(Event.objects.count(), 2)

    def test_event_edge_case_overlap(self):
        """Test edge case where events start/end at the same time."""
        event = Event(
            name="Edge Case Event",
            description="This event starts exactly when Tech Conference ends",
            start_date=datetime(2023, 12, 1, 18, 0),
            end_date=datetime(2023, 12, 1, 20, 0),
            venue="Room 104",
            capacity=50
        )
        event.full_clean()
        event.save()
        self.assertEqual(Event.objects.count(), 2)

    def test_event_edge_case_overlap_fail(self):
        """Test edge case where events overlap by one minute."""
        event = Event(
            name="Edge Case Overlap Event",
            description="This event overlaps with Tech Conference by one minute",
            start_date=datetime(2023, 12, 1, 17, 59),  # Overlap dengan event1
            end_date=datetime(2023, 12, 1, 19, 0),
            venue="Room 105",
            capacity=50
        )
        with self.assertRaises(ValidationError):
            event.full_clean()


class SessionModelTest(TestCase):

    def setUp(self):
        """ Initial data testing for session"""
        self.event = Event.objects.create(
            name="Naruto Conference",
            description="Suits for wibu indo",
            start_date=datetime(2025, 3, 1, 9, 0),
            end_date=datetime(2025, 3, 1, 17, 0),
            venue="GBK",
            capacity=100
        )

        self.track1 = Track.objects.create(
            name="Lele tech",
            event=self.event,
        )

        self.track2 = Track.objects.create(
            name="Wader tech",
            event=self.event,
        )

    def test_valid_session(self):
        """ Should be valid for creating session valid within event """
        session = Session(
            title="Django Workshop",
            event=self.event,
            start_time=datetime(2025, 3, 1, 10, 0),
            end_time=datetime(2025, 3, 1, 11, 0),
            speaker="Emily Amstrong",
            track=self.track1
        )
        try:
            session.full_clean()
            session.save()
        except ValidationError:
            self.fail("Valid session should not raise ValidationError")

    def test_session_outside_event_time(self):
        """ Should fail if the session is outside the event time range """
        session = Session(
            title="Out of Bounds Session",
            event=self.event,
            start_time=datetime(2025, 3, 1, 8, 0),
            end_time=datetime(2025, 3, 1, 9, 30),
            speaker="Alice"
        )
        with self.assertRaises(ValidationError):
            session.full_clean()

    def test_session_overlap(self):
        """ should fail if the session collides with another session in the event """
        Session.objects.create(
            title="First Session",
            event=self.event,
            start_time=datetime(2025, 3, 1, 10, 0),
            end_time=datetime(2025, 3, 1, 11, 0),
            speaker="Mike Shonida",
            track=self.track1,
        )

        overlapping_session = Session(
            title="Overlapping Session",
            event=self.event,
            start_time=datetime(2025, 3, 1, 10, 30),  # Collide
            end_time=datetime(2025, 3, 1, 11, 30),
            speaker="Micky Mouse",
            track=self.track1,
        )
        with self.assertRaises(ValidationError):
            overlapping_session.full_clean()

    def test_session_end_time_before_start_time(self):
        """ Should be fail if end_time less than or same with start_time """
        session = Session(
            title="Invalid Time Session",
            event=self.event,
            start_time=datetime(2025, 3, 1, 10, 0),
            end_time=datetime(2025, 3, 1, 9, 30),
            speaker="Tom Araya"
        )
        with self.assertRaises(ValidationError):
            session.full_clean()

class TrackModelTest(TestCase):

    def setUp(self):
        """ Initial data testing for track"""
        self.event = Event.objects.create(
            name="Lele Conference",
            description="A great tech event",
            start_date=datetime(2025, 3, 1, 9, 0),
            end_date=datetime(2025, 3, 1, 17, 0),
            venue="Main Hall",
            capacity=3
        )

    def test_valid_track(self):
        """ Should be valid for creating valid track inside event """
        track = Track(
            name="Air raksa",
            event=self.event,
        )
        try:
            track.full_clean()
            track.save()
        except ValidationError:
            self.fail("Valid track should not raise ValidationError")

    def test_track_without_name(self):
        """ Track without name should be failed """
        track = Track(
            name="",
            event=self.event,
        )
        with self.assertRaises(ValidationError):
            track.full_clean()

    def test_track_belongs_to_event(self):
        """ Make sure the track is connected to the correct event """
        track = Track.objects.create(name="Introduction to statistical learning", event=self.event)
        self.assertEqual(track.event, self.event)

    def test_multiple_tracks_in_one_event(self):
        """ make sure the event can have more than one track """
        track1 = Track.objects.create(name="Data Science", event=self.event)
        track2 = Track.objects.create(name="Web Development", event=self.event)
        
        self.assertEqual(Track.objects.filter(event=self.event).count(), 2)

    def test_track_str_representation(self):
        """ Make sure the track representation string matches """
        track = Track.objects.create(name="Cyber Security", event=self.event)
        self.assertEqual(str(track), "Cyber Security - Lele Conference")


class AttendeeModelTest(TestCase):
    def setUp(self):
        """ Initial data testing for attendee"""
        self.event1 = Event.objects.create(
            name="Tech Conference",
            description="Annual tech conference",
            start_date=datetime(2023, 12, 1, 10, 0),
            end_date=datetime(2023, 12, 1, 18, 0),
            venue="Convention Center",
            capacity=2
        )
        self.event2 = Event.objects.create(
            name="Another Conference",
            description="Another tech conference",
            start_date=datetime(2023, 12, 2, 10, 0),
            end_date=datetime(2023, 12, 2, 18, 0),
            venue="Another Venue",
            capacity=500
        )

    def test_create_attendee(self):
        """ Test creating a valid attendee. """
        attendee = Attendee(
            name="John Doe",
            email="john@example.com",
            event=self.event1
        )
        attendee.full_clean()
        attendee.save()
        self.assertEqual(Attendee.objects.count(), 1)

    def test_duplicate_email_in_same_event(self):
        """ Test that the same email cannot be used for the same event. """
        attendee1 = Attendee(
            name="Ramaido",
            email="ramaido@example.com",
            event=self.event1
        )
        attendee1.full_clean()
        attendee1.save()

        attendee2 = Attendee(
            name="Ramaido",
            email="ramaido@example.com",
            event=self.event1
        )
        with self.assertRaises(ValidationError):
            attendee2.full_clean()

    def test_same_email_in_different_events(self):
        """ Test that the same email can be used for different events. """
        attendee1 = Attendee(
            name="Fafifu",
            email="fafifu@example.com",
            event=self.event1
        )
        attendee1.full_clean()
        attendee1.save()

        attendee2 = Attendee(
            name="Fafifu",
            email="fafifu@example.com",
            event=self.event2
        )
        attendee2.full_clean()
        attendee2.save()
        self.assertEqual(Attendee.objects.count(), 2)

    def test_missing_name(self):
        """ Test that name is required. """
        attendee = Attendee(
            email="fafifu@example.com",
            event=self.event1
        )
        with self.assertRaises(ValidationError):
            attendee.full_clean()

    def test_missing_email(self):
        """ Test that email is required. """
        attendee = Attendee(
            name="Ramaido",
            event=self.event1
        )
        with self.assertRaises(ValidationError):
            attendee.full_clean()

    def test_missing_event(self):
        """ Test that event is required. """
        attendee = Attendee(
            name="Haha Hihi",
            email="haha@example.com"
        )
        with self.assertRaises(ValidationError) as context:
            attendee.full_clean()
        self.assertIn("Event is required.", str(context.exception))

    def test_attendee_registration_when_capacity_not_full(self):
        """ Test if attendee can register when event capacity is not full. """
        attendee1 = Attendee(name="Haha hihi", email="haha@example.com", event=self.event1)
        attendee1.full_clean()
        attendee1.save()

        attendee2 = Attendee(name="hihi haha", email="hihi@example.com", event=self.event1)
        attendee2.full_clean()
        attendee2.save()

        self.assertEqual(Attendee.objects.count(), 2)

    def test_attendee_registration_fails_when_capacity_full(self):
        """ Test that registration fails when event capacity is full. """
        Attendee.objects.create(name="John Doe", email="john@example.com", event=self.event1)
        Attendee.objects.create(name="Jane Doe", email="jane@example.com", event=self.event1)

        attendee3 = Attendee(name="Nguyen", email="nguyen@example.com", event=self.event1)
        with self.assertRaises(ValidationError) as context:
            attendee3.full_clean()

        self.assertIn("Event capacity has been reached", str(context.exception))
        self.assertEqual(Attendee.objects.count(), 2)