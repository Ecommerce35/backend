from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate
from userauths.utils import send_sms
from userauths.tokens import otp_token_generator

User = get_user_model()

class CustomEmailOrPhoneAuthentication(BaseAuthentication):
    def authenticate(self, request):
        email_or_phone = request.data.get('email_or_phone')
        password = request.data.get('password')

        if not email_or_phone or not password:
            return None

        # Authenticate using the custom backend
        user = authenticate(request=request, email_or_phone=email_or_phone, password=password)

        if user is None:
            raise AuthenticationFailed('Invalid credentials')

        # Check if the user's account is not active
        if not user.is_active:
            otp = otp_token_generator.generate_otp()  # Generate OTP
            otp_expiration_time = timezone.now() + timedelta(minutes=5)  # OTP valid for 5 minutes

            # Save the OTP and its expiration in the session (or use another mechanism)
            if request:
                request.session['otp'] = {
                    'otp_code': otp,
                    'otp_expiration_time': otp_expiration_time.strftime("%Y-%m-%d %H:%M:%S")
                }

            # Send OTP via SMS
            message = f"Your OTP for account activation is: {otp}"
            send_sms(user.phone, message)

            # Raise exception to signal account is inactive and OTP has been sent
            raise AuthenticationFailed({
                "message": "Account not verified. OTP sent to your phone.",
                "redirect": True,
                "user_id": user.id  # Send user ID for frontend to track
            })

        # If user is active, return the user and None (as required by DRF authentication)
        return (user, None)
