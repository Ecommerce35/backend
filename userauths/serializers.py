
from .models import User
import re
from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import smart_str, smart_bytes

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.encoding import smart_bytes
from django.core.mail import send_mail
from django.conf import settings
from .models import User 
from .utils import send_password_reset_email
from rest_framework_simplejwt.tokens import RefreshToken, TokenError




class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=70, min_length=8, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'password']
    
    def validate(self, attrs):
        password = attrs.get('password')
        
        # Custom password rules
        if not any(char.isupper() for char in password):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not any(char.islower() for char in password):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not any(char.isdigit() for char in password):
            raise serializers.ValidationError("Password must contain at least one number.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise serializers.ValidationError("Password must contain at least one special character.")
        
        # Additional Django password validation (optional)
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        # Check for duplicate email or phone number
        email = attrs.get('email')
        phone = attrs.get('phone')

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("An account with this email already exists. Login or reset password")
        
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("An account with this phone number already exists. Login or reset password")
        
        return super().validate(attrs)

    def create(self, validated_data):
        # Create user and hash the password
        user = User.objects.create_user(**validated_data)
        return user

class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")
        cached_otp = cache.get(f"otp_{email}")
        
        if not cached_otp:
            raise serializers.ValidationError("OTP has expired. Please request a new one.")
        if cached_otp != otp:
            raise serializers.ValidationError("Invalid OTP.")
        
        return attrs

class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=6)
    password = serializers.CharField(max_length=68, write_only=True)
    refresh_token = serializers.CharField(max_length=300, read_only=True)
    access_token = serializers.CharField(max_length=300, read_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'access_token', 'refresh_token']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        request = self.context.get('request')

        # Authenticate user
        user = authenticate(request, email=email, password=password)

        if not user:
            raise AuthenticationFailed('Invalid credentials, please try again.')
        if not user.is_active:
            raise AuthenticationFailed('Account is not active. Please verify your email.')

        # Get tokens for authenticated user
        user_tokens = user.tokens()

        return {
            'email': user.email,
            'access_token': user_tokens['access'],
            'refresh_token': user_tokens['refresh'],
        }


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        refresh_token = attrs.get('refresh')

        if not refresh_token:
            raise serializers.ValidationError("Refresh token is required.")

        try:
            refresh = RefreshToken(refresh_token)
            attrs['access'] = str(refresh.access_token)
        except TokenError as e:
            raise serializers.ValidationError("Invalid or expired refresh token.")
        
        return attrs


class PasswordResestRequestSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=50)

    class Meta:
        model = User
        fields = ['email']

    def validate(self, attrs):
        email = attrs.get('email')

        try:
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            request = self.context.get('request')
            protocol = 'https' if request.is_secure() else 'http'

            # site_domain = '192.168.102.89:5173/'
            # # site_domain = get_current_site(request).domain
            # relative_link = reverse('userauths:password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
            # reset_link = f'{protocol}://{site_domain}{relative_link}'

            frontend_reset_url = 'http://192.168.102.89:5173/auth/reset-password'  # Adjust to your actual frontend URL
            reset_link = f'{frontend_reset_url}?uidb64={uidb64}&token={token}'

            # Send the reset email
            if not send_password_reset_email(email=email, reset_link=reset_link, user_name=user.first_name):
                raise serializers.ValidationError("Failed to send the password reset email.")

        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        return super().validate(attrs)

class PasswordResetConfirmSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    confirm_password = serializers.CharField(write_only=True, min_length=8, max_length=128)

    class Meta:
        model = User
        fields = ['password', 'confirm_password']

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

class LogOutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(max_length=300)

    default_error_messages = {
        'bad_token': "Invalid or expired token.",
    }

    def validate(self, attrs):
        # Validate the presence of the refresh token
        self.token = attrs.get('refresh_token')
        if not self.token:
            raise serializers.ValidationError("Refresh token is required.")
        return attrs

    def save(self, **kwargs):
        try:
            # Attempt to blacklist the token
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            # Handle invalid or expired token errors
            self.fail('bad_token')
        return {"success": "Logged out successfully."}