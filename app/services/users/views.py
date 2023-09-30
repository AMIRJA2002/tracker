from .service import UserQueries, send_otp_and_set_cache, login_user
from services.common.utils import get_tokens_for_user
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework import status
import redis

User = get_user_model()

r = redis.Redis(host='redis', port=6379, db=0)


class RegisterAPIView(APIView):

    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        password = serializers.CharField()
        confirm_password = serializers.CharField()

        def validate_email(self, email):
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError('email already exists!')
            return email

        def validate(self, data):
            if not data.get("password") or not data.get("confirm_password"):
                raise serializers.ValidationError("please fill password and confirm password")

            if data.get("password") != data.get("confirm_password"):
                raise serializers.ValidationError("confirm password is not equal to password")
            return data

    @extend_schema(request=InputSerializer)
    def post(self, request):
        data = self.InputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        email = data.validated_data['email']
        password = data.validated_data['password']

        UserQueries.create_one(email=email, password=password)
        send_otp_and_set_cache(email)
        return Response({'data': data.data, 'message': 'please confirm your email'}, status=status.HTTP_201_CREATED)


class ConfirmEmailAndLoginAPIView(APIView):
    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        otp = serializers.CharField()

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            exclude = ['password']

    @extend_schema(request=InputSerializer, responses=OutputSerializer)
    def post(self, request):
        data = self.InputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        user = UserQueries.validate_user_email(email=data.validated_data['email'], otp=data.validated_data['otp'])
        _tokens = get_tokens_for_user(user)

        return Response({'user': self.OutputSerializer(instance=user).data, 'tokens': _tokens})

    def get(self, request):  # generate new otp
        email = request.POST.get('email')
        if email:
            UserQueries.check_user_is_active(email)
            send_otp_and_set_cache(email)
            return Response({'message': 'sent'}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        password = serializers.CharField()

    @extend_schema(request=InputSerializer)
    def post(self, request):
        data = self.InputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        user = login_user(data.validated_data)
        token = get_tokens_for_user(user)
        return Response(token)
