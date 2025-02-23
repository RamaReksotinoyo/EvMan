from django.db import models
from django.core.exceptions import ValidationError
import uuid


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    venue = models.CharField(max_length=255)
    capacity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """ Make sure end_date is greater than start_date """

        """ Validation so that the event does not collide with other events at the same time """
        overlapping_events = Event.objects.filter(
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        ).exclude(id=self.id)

        if overlapping_events.exists():
            raise ValidationError("Event overlaps with existing events.")

        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")

    def __str__(self):
        return self.name


class Track(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tracks")

    def __str__(self):
        return f"{self.name} - {self.event.name}"


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="sessions")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    speaker = models.CharField(max_length=255)

    def clean(self):
        """ Validate sessions to be in the event and not overlapping """
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

        if self.start_time < self.event.start_date or self.end_time > self.event.end_date:
            raise ValidationError("Session must be within the event time range.")

        if self.track:
            overlapping_sessions = Session.objects.filter(
                track=self.track,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exclude(id=self.id)

            if overlapping_sessions.exists():
                raise ValidationError("Session overlaps with another session in the same track.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            # Constraint to make sure end_time > start_time
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F('start_time')),
                name='check_end_time_after_start_time'
            )
        ]

    def __str__(self):
        return f"{self.title} - {self.track.name} ({self.event.name})"


class Attendee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="attendees")

    def clean(self):
        event = getattr(self, 'event', None)
        if not event:
            raise ValidationError("Event is required.")
        
        if event.attendees.count() >= event.capacity:
            raise ValidationError("Event capacity has been reached. No more registrations allowed.")

        """ Validate that emails are not duplicates in one event """
        if Attendee.objects.filter(event=event, email=self.email).exclude(id=self.id).exists():
            raise ValidationError("Email has been registered for this event.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        """
        This is done so that the same email cannot be registered for the same event & 
        1 email can be used to register for multiple events.
        """
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'event'],
                name='unique_email_per_event'
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.event.name}"
    
