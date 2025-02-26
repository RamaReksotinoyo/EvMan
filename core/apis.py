from django.http import Http404
from django.db import connection
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from core.utils.base_response import BaseResponse 
from rest_framework import serializers
from .models import Event, Session, Attendee, Track
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from .authentication import JWTCookieAuthentication, IsAuthenticatedExceptPaths
from rest_framework.decorators import action
from django.db.utils import IntegrityError
from .serializers import EventSerializer, SessionSerializer, AttendeeSerializer, TrackSerializer
from .utils.limit import rate_limiter 
from django.utils import timezone


class EventPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

@extend_schema(tags=['Events'])
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    # permission_classes = [IsAuthenticated]
    permission_classes = [IsAuthenticatedExceptPaths]
    pagination_class = EventPagination
    authentication_classes = [JWTCookieAuthentication]
    http_method_names = ['get', 'post', 'put', 'delete']

    @extend_schema(
        summary="List Events",
        description="Get all events list with pagination",
        responses={
            200: EventSerializer(many=True),
            400: {"type": "object", "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {"type": "null"}
            }},
            404: {"type": "object", "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {"type": "null"}
            }}
        },
        parameters=[
            OpenApiParameter(name='page', type=int, description='Page number'),
            OpenApiParameter(name='page_size', type=int, description='Number of items per page')
        ]
    )

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            queryset = self.get_queryset()

            user_id = request.user.id
            print(f"User ID: {user_id}")  # For debugging

            if not queryset.exists():
                return Response(
                    BaseResponse.error_response("No events found"),
                    status=status.HTTP_404_NOT_FOUND
                )
            page = self.paginate_queryset(queryset)
            if not page:
                return Response(
                    BaseResponse.error_response("No events found for the given page"),
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(BaseResponse.success_response(
                data=serializer.data,
                message="Events retrieved successfully"
            ))
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Create Event",
        description="Create a new event",
        request=EventSerializer,
        responses={201: EventSerializer}
    )
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(
                BaseResponse.success_response(
                    data=serializer.data,
                    message="Event created successfully"
                ),
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            error_message = str(e.detail) if isinstance(e.detail, str) else str(e.detail.get('non_field_errors', ['Validation error'])[0])
            if isinstance(e.detail, dict):
                for field, errors in e.detail.items():
                    if isinstance(errors, list):
                        error_message = errors[0]
                        return Response(
                            BaseResponse.error_response(str(error_message)),
                            status=status.HTTP_400_BAD_REQUEST
                        )
            return Response(
                BaseResponse.error_response(str(e.detail)),
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Retrieve Event",
        description="Get event details by ID",
        responses={200: EventSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(
                BaseResponse.success_response(
                    data=serializer.data,
                    message="Event retrieved successfully"
                ),
                status=status.HTTP_200_OK
            )
        except Event.DoesNotExist:
            return Response(
                BaseResponse.error_response("Event not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Update Event",
        description="Update event details by ID",
        request=EventSerializer,
        responses={
            200: EventSerializer,
            400: {"type": "object", "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {"type": "null"}
            }},
            404: {"type": "object", "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {"type": "null"}
            }},
            500: {"type": "object", "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {"type": "null"}
            }}
        }
    )
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(
                BaseResponse.success_response(
                    data=serializer.data,
                    message="Event updated successfully"
                ),
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            error_message = str(e.detail) if isinstance(e.detail, str) else str(e.detail.get('non_field_errors', ['Validation error'])[0])
            if isinstance(e.detail, dict):
                for field, errors in e.detail.items():
                    if isinstance(errors, list):
                        error_message = errors[0]
                        return Response(
                            BaseResponse.error_response(str(error_message)),
                            status=status.HTTP_400_BAD_REQUEST
                        )
            return Response(
                BaseResponse.error_response(str(e.detail)),
                status=status.HTTP_400_BAD_REQUEST
            )
        except Event.DoesNotExist:
            return Response(
                BaseResponse.error_response("Event not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Delete Event",
        description="Delete event by ID",
        responses={204: None}
    )
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            return Response(
                BaseResponse.success_response(
                    message="Event deleted successfully"
                ),
                status=status.HTTP_204_NO_CONTENT
            )
        except Event.DoesNotExist:
            return Response(
                BaseResponse.error_response("Event not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=False, methods=["get"], url_path="current")
    @rate_limiter(10, 1, 2)
    def get_current_event(self, request):
        """
        This is a long handler with a long execution time, 
        I decided to use raw query for the sake of performance.
        """
        try:
            with connection.cursor() as cursor:
                current_time = timezone.now()
                
                cursor.execute("""
                    SELECT id, name, description, start_date, end_date, venue, capacity, created_at, updated_at
                    FROM core_event
                    WHERE %s BETWEEN start_date AND end_date
                    LIMIT 1
                """, [current_time])
                
                event = cursor.fetchone()

                if not event:
                    return Response(
                        BaseResponse.error_response("No ongoing event found"),
                        status=status.HTTP_404_NOT_FOUND
                    )

                event_data = {
                    "id": event[0],
                    "name": event[1],
                    "description": event[2],
                    "start_date": event[3],
                    "end_date": event[4],
                    "venue": event[5],
                    "capacity": event[6],
                    "created_at": event[7],
                    "updated_at": event[8],
                    "tracks": []
                }

                cursor.execute("""
                    SELECT id, name
                    FROM core_track
                    WHERE event_id = %s
                """, [event[0]])
                tracks = cursor.fetchall()

                for track in tracks:
                    track_data = {
                        "id": track[0],
                        "name": track[1],
                        "sessions": []
                    }

                    cursor.execute("""
                        SELECT id, title, description, start_time, end_time, speaker
                        FROM core_session
                        WHERE track_id = %s
                    """, [track[0]])
                    sessions = cursor.fetchall()

                    for session in sessions:
                        session_data = {
                            "id": session[0],
                            "title": session[1],
                            "description": session[2],
                            "start_time": session[3],
                            "end_time": session[4],
                            "speaker": session[5]
                        }
                        track_data["sessions"].append(session_data)

                    event_data["tracks"].append(track_data)

            return Response(
                BaseResponse.success_response(
                    data=event_data,
                    message="Event details retrieved successfully"
                ),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SessionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(tags=['Sessions'])
class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = SessionPagination
    http_method_names = ['get', 'post', 'put', 'delete']

    @extend_schema(
        summary="List Sessions",
        description="Get all sessions list with pagination, or filter by event ID",
        responses={200: SessionSerializer(many=True)},
        parameters=[
            OpenApiParameter(name='page', type=int, description='Page number'),
            OpenApiParameter(name='page_size', type=int, description='Number of items per page'),
            OpenApiParameter(name='event_id', type=str, description='Filter by event UUID')
        ]
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())

            event_id = request.query_params.get('event_id')
            if event_id:
                queryset = queryset.filter(event_id=event_id)

            if not queryset.exists():
                return Response(
                    BaseResponse.error_response("No sessions found"),
                    status=status.HTTP_404_NOT_FOUND
                )

            page = self.paginate_queryset(queryset)
            if not page:
                return Response(
                    BaseResponse.error_response("No sessions found for the given page"),
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(BaseResponse.success_response(
                data=serializer.data,
                message="Sessions retrieved successfully"
            ))
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Create Session",
        description="Create a new session",
        request=SessionSerializer,
        responses={201: SessionSerializer}
    )
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(
                BaseResponse.success_response(
                    data=serializer.data,
                    message="Session created successfully"
                ),
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            error_dict = e.detail
            if 'track' in error_dict:
                error_message = error_dict['track'][0]  # Ambil pesan error track
                print('error_message: ', error_message)
            else:
                error_message = next(iter(error_dict.values()))[0]  # Ambil error pertama
                print('error_message: ', error_message)
            error_message = str(e.detail) if isinstance(e.detail, str) else str(e.detail.get('non_field_errors', ['Validation error'])[0])
            return Response(
                BaseResponse.error_response(error_message),
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Retrieve Session",
        description="Get session details by ID",
        responses={200: SessionSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(
                BaseResponse.success_response(
                    data=serializer.data,
                    message="Session retrieved successfully"
                ),
                status=status.HTTP_200_OK
            )
        except Session.DoesNotExist:
            return Response(
                BaseResponse.error_response("Session not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Get Sessions by Event ID",
        description="Retrieve all sessions for a specific event ID",
        responses={200: SessionSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='by-event/(?P<event_id>[^/.]+)')
    def get_sessions_by_event(self, request, event_id=None):
        try:
            queryset = Session.objects.filter(event_id=event_id)
            if not queryset.exists():
                return Response(
                    BaseResponse.error_response("No sessions found for the given event"),
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = self.get_serializer(queryset, many=True)
            return Response(
                BaseResponse.success_response(
                    data=serializer.data,
                    message="Sessions retrieved successfully"
                ),
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Update Session",
        description="Update session details by ID",
        request=SessionSerializer,
        responses={200: SessionSerializer}
    )
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(
                BaseResponse.success_response(
                    data=serializer.data,
                    message="Session updated successfully"
                ),
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            error_message = str(e.detail) if isinstance(e.detail, str) else str(e.detail.get('non_field_errors', ['Validation error'])[0])
            return Response(
                BaseResponse.error_response(error_message),
                status=status.HTTP_400_BAD_REQUEST
            )
        except Session.DoesNotExist:
            return Response(
                BaseResponse.error_response("Session not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Delete Session",
        description="Delete session by ID",
        responses={204: None}
    )
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            return Response(
                BaseResponse.success_response(
                    message="Session deleted successfully"
                ),
                status=status.HTTP_204_NO_CONTENT
            )
        except Session.DoesNotExist:
            return Response(
                BaseResponse.error_response("Session not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AttendeePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class AttendeeViewSet(viewsets.ModelViewSet):
    queryset = Attendee.objects.all()
    serializer_class = AttendeeSerializer
    # permission_classes = [IsAuthenticated]
    permission_classes = [IsAuthenticatedExceptPaths]
    authentication_classes = [JWTCookieAuthentication]
    pagination_class = SessionPagination
    http_method_names = ['get', 'post']


    @extend_schema(
        summary="List Attendee",
        description="Get all attendee list with pagination, or filter by event ID",
        responses={200: AttendeeSerializer(many=True)},
        parameters=[
            OpenApiParameter(name='page', type=int, description='Page number'),
            OpenApiParameter(name='page_size', type=int, description='Number of items per page'),
            OpenApiParameter(name='event_id', type=str, description='Filter by event UUID')
        ]
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())

            # Filter berdasarkan attendee_id jika diberikan
            attendee_id = request.query_params.get('attendee_id')
            if attendee_id:
                queryset = queryset.filter(attendee_id=attendee_id)

            if not queryset.exists():
                return Response(
                    BaseResponse.error_response("No attendee found"),
                    status=status.HTTP_404_NOT_FOUND
                )

            page = self.paginate_queryset(queryset)
            if not page:
                return Response(
                    BaseResponse.error_response("No attendee found for the given page"),
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(BaseResponse.success_response(
                data=serializer.data,
                message="Attendees retrieved successfully"
            ))
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Create Attendee",
        description="Attendee registration",
        request=AttendeeSerializer,
        responses={201: AttendeeSerializer}
    )
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(
                BaseResponse.success_response(
                    data=serializer.data,
                    message="Attendee created successfully"
                ),
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            error_message = str(e.detail) if isinstance(e.detail, str) else str(e.detail.get('non_field_errors', ['Validation error'])[0])
            return Response(
                BaseResponse.error_response(error_message),
                status=status.HTTP_400_BAD_REQUEST
            )
        except IntegrityError:
            return Response(
                BaseResponse.error_response("Email has been registered for this event."),
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="List Attendee by event",
        description="Get all attendee filtered by event ID",
        responses={200: AttendeeSerializer(many=True)},
        parameters=[
            OpenApiParameter(name='page', type=int, description='Page number'),
            OpenApiParameter(name='page_size', type=int, description='Number of items per page'),
            OpenApiParameter(name='event_id', type=str, description='Filter by event UUID')
        ]
    )
    @action(detail=False, methods=['get'], url_path='by-event/(?P<event_id>[^/.]+)')
    def list_by_event(self, request, event_id=None):
        try:
            queryset = Attendee.objects.filter(event_id=event_id)
            if not queryset.exists():
                return Response(
                    BaseResponse.error_response("No attendees found for the given event"),
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = self.get_serializer(queryset, many=True)
            return Response(
                BaseResponse.success_response(
                    data=serializer.data,
                    message="Attendees retrieved successfully"
                ),
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrackPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(tags=['Tracks'])
class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    pagination_class = TrackPagination
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTCookieAuthentication]
    http_method_names = ['get', 'post', 'put', 'delete']

    @extend_schema(
        summary="List Tracks",
        description="Get all tracks list with pagination",
        responses={
            200: TrackSerializer(many=True),
            400: {"type": "object", "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {"type": "null"}
            }},
            404: {"type": "object", "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {"type": "null"}
            }}
        }
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())

            if not queryset.exists():
                return Response(
                    BaseResponse.error_response("No tracks found"),
                    status=status.HTTP_404_NOT_FOUND
                )

            page = self.paginate_queryset(queryset)
            if not page:
                return Response(
                    BaseResponse.error_response("No tracks found for the given page"),
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(BaseResponse.success_response(
                data=serializer.data,
                message="Tracks retrieved successfully"
            ))
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Create Track",
        description="Create a new track for a specific event",
        request=TrackSerializer,
        responses={201: TrackSerializer}
    )
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(
                BaseResponse.success_response(
                    data=serializer.data,
                    message="Track created successfully"
                ),
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            error_message = str(e.detail) if isinstance(e.detail, str) else str(e.detail.get('non_field_errors', ['Validation error'])[0])
            return Response(
                BaseResponse.error_response(error_message),
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Retrieve Track",
        description="Get track details by ID",
        responses={200: TrackSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(
                BaseResponse.success_response(
                    data=serializer.data,
                    message="Track retrieved successfully"
                ),
                status=status.HTTP_200_OK
            )
        except Http404:
            return Response(
                BaseResponse.error_response("Track not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Delete Track",
        description="Delete a track by ID",
        responses={204: None}
    )
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                BaseResponse.success_response(
                    data=None,
                    message="Track deleted successfully"
                ),
                status=status.HTTP_204_NO_CONTENT
            )
        except Http404:
            return Response(
                BaseResponse.error_response("Track not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                BaseResponse.error_response(str(e)),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
