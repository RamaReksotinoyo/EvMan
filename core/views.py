from django.shortcuts import render



# class LoginRequestSerializer(serializers.Serializer):
#     username = serializers.CharField()
#     password = serializers.CharField(write_only=True)


# class LoginResponseSerializer(serializers.Serializer):
#     access_token = serializers.CharField()
#     refresh_token = serializers.CharField()
#     access_token_expired_at = serializers.IntegerField()


# # Create your views here.
# class LoginView(APIView):
#     permission_classes = [AllowAny]

#     @extend_schema(
#         request=LoginRequestSerializer,
#         responses={200: LoginResponseSerializer, 400: None},
#         summary="Login User",
#         description="User authentication and get tokens.",
#         examples=[
#             OpenApiExample(
#                 "Request Example",
#                 value={"username": "admin", "password": "123456"},
#                 request_only=True,
#             ),
#             OpenApiExample(
#                 "Response Example",
#                 value={
#                     "success": False,
#                     "message": "Invalid credentials",
#                     "data": None
#                 },
#                 response_only=True,
#             ),
#         ],
#     )
#     def post(self, request):
#         username = request.data.get("username")
#         password = request.data.get("password")
#         user = authenticate(username=username, password=password)

#         if user is not None:
#             payload = {
#                 "user_id": user.id,
#                 "username": user.username,
#             }

#             access_token, expired_at = generate_access_token(payload)
#             refresh_token = generate_refresh_token(user)

#             print(verify_access_token(access_token))

#             return Response(
#                 BaseResponse.success_response({
#                     "access_token": access_token,
#                     "refresh_token": refresh_token,
#                     "access_token_expired_at": expired_at,
#                 }),
#                 status=HTTP_200_OK
#             )
#         else:
#             return Response(BaseResponse.error_response("Invalid credentials"), status=HTTP_400_BAD_REQUEST)