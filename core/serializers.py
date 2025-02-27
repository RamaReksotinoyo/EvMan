from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework.response import Response
from rest_framework import status
from core.utils.base_response import BaseResponse 
from rest_framework import exceptions
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import serializers
from .models import Event, Track, Session, Attendee
from .utils import helpers
from datetime import timedelta


# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     def validate(self, attrs):
#         try:
#             data = super().validate(attrs)
#             return {
#                 'success': True,
#                 'message': 'Token generated successfully',
#                 'data': {
#                     'access_token': data['access'],
#                     'refresh_token': data['refresh']
#                 }
#             }
#         except Exception as e:
#             raise exceptions.AuthenticationFailed("Username/password invalid")

# class CustomTokenRefreshSerializer(TokenRefreshSerializer):
#     def validate(self, attrs):
#         try:
#             data = super().validate(attrs)
#             return BaseResponse.success_response(
#                 data={
#                     'access_token': data['access']
#                 },
#                 message="Token refreshed successfully"
#             )
#         except Exception as e:
#             raise exceptions.AuthenticationFailed("Refresh token invalid")

# class CustomTokenObtainPairView(TokenObtainPairView):
#     serializer_class = CustomTokenObtainPairSerializer

#     def post(self, request, *args, **kwargs):
#         try:
#             serializer = self.get_serializer(data=request.data)
#             serializer.is_valid(raise_exception=True)
#             return Response(serializer.validated_data, status=status.HTTP_200_OK)
#         except exceptions.AuthenticationFailed as e:
#             return Response(
#                 BaseResponse.error_response(str(e)),
#                 status=status.HTTP_400_BAD_REQUEST
#             )

# class CustomTokenRefreshView(TokenRefreshView):
#     serializer_class = CustomTokenRefreshSerializer

#     def post(self, request, *args, **kwargs):
#         try:
#             serializer = self.get_serializer(data=request.data)
#             serializer.is_valid(raise_exception=True)
#             return Response(serializer.validated_data, status=status.HTTP_200_OK)
#         except exceptions.AuthenticationFailed as e:
#             return Response(
#                 BaseResponse.error_response(str(e)),
#                 status=status.HTTP_400_BAD_REQUEST
#             )

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        self.user = self.user  # Store user for view access
        return data

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            response = Response(
                BaseResponse.success_response(
                    message="Login successful",
                    data={"user_id": serializer.user.id, "username": serializer.user.username}
                ),
                status=status.HTTP_200_OK
            )

            # Set access token cookie
            response.set_cookie(
                'access_token',
                serializer.validated_data['access'],
                httponly=True,
                secure=True,
                samesite='Strict',
                max_age=3600,
                path='/'
            )

            # Set refresh token cookie
            response.set_cookie(
                'refresh_token',
                serializer.validated_data['refresh'],
                httponly=True,
                secure=True,
                samesite='Strict',
                max_age=86400,
                path='/'
            )

            return response

        except exceptions.AuthenticationFailed as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_401_UNAUTHORIZED
            )

class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer

    @extend_schema(
        summary="Refresh Access Token",
        description="Automatically uses refresh token from HTTP-only cookie",
        request=None,  # Remove request body
        responses={
            200: OpenApiResponse(
                description="Token refreshed successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "message": {"type": "string"},
                        "data": {"type": "null"}
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            serializer = self.get_serializer(data={'refresh': refresh_token})
            serializer.is_valid(raise_exception=True)

            response = Response(
                BaseResponse.success_response(
                    message="Token refreshed successfully",
                    data=None
                ),
                status=status.HTTP_200_OK
            )

            response.set_cookie(
                'access_token',
                serializer.validated_data['access'],
                httponly=True,
                secure=True,
                samesite='Strict',
                max_age=3600,
                path='/'
            )

            return response

        except exceptions.AuthenticationFailed as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_401_UNAUTHORIZED
            )


class EventSerializer(serializers.ModelSerializer):

    start_date = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%S",
        input_formats=["%Y-%m-%dT%H:%M:%S"],
        error_messages={
            'invalid': 'Date format must be YYYY-MM-DDThh:mm:ss (Example: 2024-02-25T14:30:00)'
        }
    )
    end_date = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%S",
        input_formats=["%Y-%m-%dT%H:%M:%S"],
        error_messages={
            'invalid': 'Date format must be YYYY-MM-DDThh:mm:ss (Example: 2024-02-25T14:30:00)'
        }
    )

    class Meta:
        model = Event
        fields = '__all__'

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        latest_event = Event.objects.exclude(id=self.instance.id if self.instance else None).order_by('-end_date').first()

        if latest_event and not self.instance:
            minimum_start_date = latest_event.end_date + timedelta(days=3)
            if start_date <= minimum_start_date:
                raise serializers.ValidationError(
                    detail=BaseResponse.error_response(
                        f"New event can only be created 3 days after the last event ends (after {minimum_start_date.strftime('%Y-%m-%dT%H:%M:%S')})"
                    )["message"]
                )

        if end_date <= start_date:
            raise serializers.ValidationError(
                detail=BaseResponse.error_response("End date must be after start date")["message"]
            )

        overlapping_events = Event.objects.filter(
            start_date__lt=end_date,
            end_date__gt=start_date
        )

        if self.instance:
            overlapping_events = overlapping_events.exclude(id=self.instance.id)

        if overlapping_events.exists():
            raise serializers.ValidationError(
                detail=BaseResponse.error_response("Event overlaps with existing events")["message"]
            )

        return data
    

class SessionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Session
        fields = '__all__'

    def validate(self, data):
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        event = data.get('event')
        track = data.get('track')

        if not track:
            raise serializers.ValidationError({"track": "Track is required"})

        if end_time <= start_time:
            raise serializers.ValidationError(
                detail=BaseResponse.error_response("End time must be after start time")["message"]
            )

        if start_time < event.start_date or end_time > event.end_date:
            raise serializers.ValidationError(
                detail=BaseResponse.error_response("Session must be within event duration")["message"]
            )

        if track and track.event != event:
            raise serializers.ValidationError(
                detail=BaseResponse.error_response("Track does not belong to the selected event")["message"]
            )
        
        overlapping_sessions = Session.objects.filter(
            track=track,
            event=event,
            start_time__lt=end_time,
            end_time__gt=start_time
        )

        if self.instance:
            overlapping_sessions = overlapping_sessions.exclude(id=self.instance.id)

        if overlapping_sessions.exists():
            raise serializers.ValidationError(
                detail=BaseResponse.error_response("Session overlaps with another session in the same track in event")["message"]
            )

        return data
    

class AttendeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendee
        fields = ['id', 'name', 'email', 'event']

    def validate_name(self, value):
        """Input sanitation of name before saving."""
        return helpers.sanitize_input(value)

    def validate(self, data):
        """Validate so that emails are not duplicated in one event."""
        event = data.get("event")
        email = data.get("email")

        if not event:
            # raise serializers.ValidationError("Event is required.")
            raise serializers.ValidationError(
                detail=BaseResponse.error_response("Event is required.")["message"]
            )

        """ Validasi kapasitas event """
        if event.attendees.count() >= event.capacity:
            raise serializers.ValidationError(
                detail=BaseResponse.error_response("Event capacity has been reached.")["message"]
            )

        if event and email:
            if Attendee.objects.filter(event=event, email=email).exists():
                raise serializers.ValidationError(
                    detail=BaseResponse.error_response("The fields email, event must make a unique set.")["message"]
                )

        return data
    

class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = "__all__"

    def validate_name(self, data):
        """ Validate track names to be unique within an event and not empty """
        if not data.strip():
            raise serializers.ValidationError("Track name cannot be empty or whitespace only.")

        event_id = self.initial_data.get("event")
        if not event_id:
            # raise serializers.ValidationError("Event is required.")
            raise serializers.ValidationError(
                detail=BaseResponse.error_response("Event is required.")["message"]
            )

        if not Event.objects.filter(id=event_id).exists():
            # raise serializers.ValidationError("Event does not exist.")
            raise serializers.ValidationError(
                detail=BaseResponse.error_response("Event does not exist")["message"]
            )

        if Track.objects.filter(name=data, event_id=event_id).exists():
            # raise serializers.ValidationError("Track name must be unique within the event.")
            raise serializers.ValidationError(
                detail=BaseResponse.error_response("Track name must be unique within the event")["message"]
            )
        
        return data