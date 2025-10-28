from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from userauths.forms import UserLoginForm, UserRegisterForm, ProfileForm, SetPasswordForm, PasswordResetForm, EmailOrPhoneForm, PasswordForm
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages, auth
from userauths.models import User, Profile
from .models import SubscribedUsers
from vendor.models import *
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from order.models import *
from .utils import *
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from userauths.tokens import account_activation_token, otp_token_generator
from django.db.models.query_utils import Q
from django.http import JsonResponse
from django.db import DatabaseError
from django.contrib.auth import update_session_auth_hash
from datetime import timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from .decorators import user_is_superuser
from vendor.forms import *
from django.template.defaultfilters import slugify

from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.utils import timezone
from rest_framework.permissions import AllowAny
from .utils import generate_otp, send_email_otp
from django.core.cache import cache

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken


class RegisterUserView(GenericAPIView):
    serializer_class = UserRegisterSerializer

    def post(self, request):
        user_data = request.data
        serializer = self.serializer_class(data=user_data)
        
        # Validate and save user data
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()  # Get the actual user instance after saving

            # Generate OTP and secret key
            otp, secret_key = generate_otp(interval=300)

            # Send OTP email
            email_sent = send_email_otp(user.email, otp, user.first_name, request)
            if not email_sent:
                return Response({
                    'message': 'User registered, but OTP email failed to send.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'data': serializer.data,
                'message': f"Hi {user.first_name}, thanks for signing up. Check your email for the OTP."
            }, status=status.HTTP_201_CREATED)

        # Return validation errors if serializer is invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            
            # Activate the user
            try:
                user = User.objects.get(email=email)
                user.role = 'customer'
                user.is_active = True
                user.save()
            except User.DoesNotExist:
                return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

            cache.delete(f"otp_{email}")  # Clear OTP from cache
            return Response({"message": "OTP verified and account activated."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return Response({"message": "Account is already active."}, status=status.HTTP_200_OK)
            
            otp, secret_key = generate_otp(interval=300)

            # Send OTP email
            send_email_otp(user.email, otp, user.first_name, request)

            return Response({"message": "A new OTP has been sent to your email."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)

class LoginUserView(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenRefreshView(GenericAPIView):
    serializer_class = TokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            return Response({'access': serializer.validated_data['access']})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(GenericAPIView):
    def post(self, request):
        serializer = PasswordResestRequestSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            return Response({"message": "Password reset link sent to your email."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Handles resetting a user's password after verifying the token and uidb64.
    """
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, uidb64, token):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        password = serializer.validated_data['password']

        try:
            # Decode the UID to get the user ID
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)

            # Verify the token
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the new password is different from the old password
            if user.check_password(password):
                return Response({"error": "The new password must be different from the old password."}, status=status.HTTP_400_BAD_REQUEST)

            # Set the new password
            user.set_password(password)
            user.is_active=True
            user.save()

            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)

        except DjangoUnicodeDecodeError:
            return Response({"error": "Invalid UID."}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)

class LogOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogOutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# @login_required()
def dashboard(request):
    user = request.user
    # return redirect(detect_user(user)) or None
    return HttpResponse('')

@login_required
@user_passes_test(is_vendor)
def vendor_dashboard(request):
    vendor = get_object_or_404(Vendor, user=request.user)
    orders = Order.objects.filter(vendors__in=[vendor.id], is_ordered =True).order_by('-date_created')
    recent_orders = orders[:10]
    current_month = datetime.now().month
    current_month_orders = orders.filter(vendors__in=[vendor.id], date_created__month=current_month)
    current_month_revenue = sum(i.get_total_by_vendor()['total'] for i in current_month_orders)
    total_revenue = sum(order.get_total_by_vendor()['total'] for order in orders)
    context = {
        'orders': orders,
        'orders_count': orders.count(),
        'recent_orders': recent_orders,
        'total_revenue': total_revenue,
        'current_month_revenue': current_month_revenue,
    }
    return render(request, 'vendor_dashboard.html', context)

# User = settings.AUTH_USER_MODEL
#Addded by me

def signup_redirect(request):
    messages.error(request, "Something wrong here, it may be that you already have an account!")
    return redirect("core:index")



def activate(request, uidb64, token):
    # User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, "Thank you for your email confirmation. Now you can login your account.")
        return redirect("address:customer_dashboard")
    else:
        messages.error(request, "Activation link is invalid!")

    return redirect('address:customer_dashboard')

def activateEmail(request, user, to_email):
    mail_subject = "Activate your user account."
    message = render_to_string("activate_account.html", {
        'user': user,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        "protocol": 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.content_subtype = "html"
    if email.send():
        messages.success(request, f'Dear <b> {user.first_name} </b>, please go to you email <b> {to_email} </b> inbox and click on \
                received activation link to confirm and complete the registration. <b>Note:</b> Check your spam folder.')
    else:
        messages.error(request, f'Problem sending email to {to_email}, check if you typed it correctly.')

def register_view(request):
    if request.user.is_authenticated:
        return JsonResponse({'error': 'You are already signed up'}, status=400)

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        longitude = request.POST.get('longitude')
        latitude = request.POST.get('latitude')
        next = request.POST.get('next')

        if User.objects.filter(email=email).exists():
            request.session['email_or_phone'] = email
            return JsonResponse({'error': 'An account with this email already exists. Kindly log in or reset password if forgotten'}, status=400)
        elif User.objects.filter(phone=phone).exists():
            request.session['email_or_phone'] = phone
            return JsonResponse({'error': 'An account with this phone number already exists. Kindly log in or reset password if forgotten'}, status=400)
        else:
            try:
                user = User.objects.create_user(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    password=password,
                )
                user.role = 'customer'
                user.save()
                profile = Profile.objects.get(user=user)
                profile.latitude = latitude
                profile.longitude = longitude
                profile.save()

                if next:
                     next_page = next
                else:
                    next_page = request.POST.get('next', '')

                if next_page:
                    request.session['next_page'] = next_page
                
                user = User.objects.get(Q(email=email)| Q(phone=phone))
                otp = otp_token_generator.generate_otp()
                # Save OTP and its expiration time in the user's session
                otp_expiration_time = timezone.now() + timedelta(minutes=5)  # Set expiration time to 5 minutes
                request.session['account_activation_otp'] = {
                    'activation_otp': otp,
                    'activation_expiration_time': otp_expiration_time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                request.session['account_register_id'] = user.id

                try:
                    message = f'Your OTP for account activation is: {otp}'
                    send_sms(phone, message)
                except:
                    pass
                return JsonResponse({'message': 'Account created successfully! Please check your email to activate your account.', 'redirect_url': reverse('userauths:activate')}, status=200)
            except DatabaseError as e:
                return JsonResponse({'error': f'Error creating user: {e}'}, status=500)
            except Exception as e:
                return JsonResponse({'error': f'An unexpected error occurred: {e}'}, status=500)
    else:
        form = UserRegisterForm()

    return render(request, "sign_up.html")

@login_required
def vendor_signup(request):
    if request.user.is_authenticated:
        if request.user.role == 'vendor':
            return redirect('userauths:dashboard')

        # Check if the user already has a Vendor profile
        if Vendor.objects.filter(user=request.user).exists():
            return redirect('payments:subscribe')

        if request.method == 'POST':
            vendor_form = VendorForm(request.POST, request.FILES)
            if vendor_form.is_valid():
                user = request.user
                vendor = vendor_form.save(commit=False)
                vendor.user = user
                name = vendor_form.cleaned_data['name']
                vendor.slug = f'{slugify(name)}-{user.id}'
                vendor.save()

                # Get latitude and longitude from POST data
                latitude = request.POST.get('latitude')
                longitude = request.POST.get('longitude')
                
                # Ensure the About instance is created by the signal
                about_profile = About.objects.get(vendor=vendor)
                about_profile.latitude = latitude
                about_profile.longitude = longitude
                about_profile.save()
                
                return JsonResponse({'success': True, 'message':'Your store was been created successfully, please wait for approval'}, status=200)

            else:
                errors = {field: error for field, error in vendor_form.errors.items()}
                return JsonResponse({'errors': errors}, status=400)
        else:
            vendor_form = VendorForm()
    else:
        return redirect('userauths:email')

    context = {
        'vendor_form': vendor_form,
    }
    return render(request, 'vendor-signup.html', context)

def email_or_phone_view(request):
    if request.user.is_authenticated:
        messages.error(request, "Hello! You are already logged in.")
        return redirect('userauths:dashboard')

    if request.method == "POST":
        data = request.POST.get('email_or_phone')
        next = request.POST.get('next')
        try:
            user = User.objects.get(Q(email=data) | Q(phone=data))
            request.session['email_or_phone'] = data
            # Save next page URL to session if provided
            if next:
                next_page = next
            else:
                next_page = request.POST.get('next', '')

            if next_page:
                request.session['next_page'] = next_page

            return redirect('userauths:password')
        except User.DoesNotExist:
            messages.error(request, "User does not exist.")
    else:
        form = EmailOrPhoneForm()

    return render(request, "enter_email_or_phone.html", {'form': form, 'next': request.GET.get('next', '')})

# @require_POST
def password_view(request):
    if request.user.is_authenticated:
        messages.error(request, "Hello! You are already logged in.")
        return redirect('userauths:dashboard')

    email_or_phone = request.session.get('email_or_phone')
    if not email_or_phone:
        messages.error(request, "Please enter your email or phone number first.")
        return redirect('userauths:email')

    if request.method == "POST":
        data = request.POST.get('password')
        verified = User.objects.get(Q(email=email_or_phone) | Q(phone=email_or_phone))
        if verified.is_active == False:
            otp = otp_token_generator.generate_otp()
            # Save OTP and its expiration time in the user's session
            otp_expiration_time = timezone.now() + timedelta(minutes=5)  # Set expiration time to 5 minutes
            request.session['account_activation_otp'] = {
                'activation_otp': otp,
                'activation_expiration_time': otp_expiration_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            request.session['account_register_id'] = verified.id
            try:
                message = f'Your OTP for account activation is: {otp}'
                send_sms(verified.phone, message)
            except:
                pass
            return JsonResponse({'redirect_url': reverse('userauths:activate'), 'message': 'Redirecting to confirm otp'}, status=200)
        else:
            user = auth.authenticate(email_or_phone=email_or_phone, password=data)
        if user is not None:
            # Password is correct, log in the user
            auth.login(request, user)
            next_page = request.session.get('next_page', reverse('userauths:dashboard'))

            return JsonResponse({'redirect_url': next_page, 'message': 'Logged in successfully'}, status=200)
        else:
            # Password is incorrect, return error message
            return JsonResponse({'error': 'Invalid password.'}, status=400)
    else:
        form = PasswordForm()

    return render(request, "password.html", {'email_or_phone': email_or_phone})

# def login_view(request):
#     if request.user.is_authenticated:
#         messages.error(request, "Hello! You are already logged in.")
#         return redirect(request.META.get("HTTP_REFERER", 'userauths:dashboard'))

#     if request.method == "POST":
#         form = PasswordForm(request=request, data=request.POST)
#         if form.is_valid():
#             user = auth.authenticate(
#                 username=form.cleaned_data["username"],
#                 password=form.cleaned_data["password"],
#             )
#             if user is not None:
#                 auth.login(request, user)
#                 messages.success(request, f"Hello <b>{user.username}</b>! You have been logged in.")
#                 next_url = request.POST.get('next', 'userauths:dashboard')
#                 return redirect(next_url)
#             else:
#                 messages.warning(request, 'Invalid login credentials.')

#         else:
#             for key, error in form.errors.items():
#                 if key == 'captcha' and error[0] == 'This field is required.':
#                     messages.error(request, "You must pass the reCAPTCHA test.")
#                 else:
#                     messages.error(request, error)

#     else:
#         form = PasswordForm()

#     return render(request, "password.html", {"form": form})     


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You logged out.")
    return redirect("userauths:email")

@login_required
def profile_update(request):
    profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = request.user
            new_form.save()
            messages.success(request, "Profile Updated Successfully.")
            return redirect(request.META.get("HTTP_REFERER", "core:index")) 
    else:
        form = ProfileForm(instance=profile)

    context = {
        "form": form,
        "profile": profile,
    }
    return render(request, "userauths/profile-edit.html", context)

@login_required
def password_change(request):
    user = request.user
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your password has been changed, Login to continue")
            return redirect("userauths:sign-in")
        else:
            for error in list(form.errors.values() ):
                messages.error(request, error)


    form = SetPasswordForm(user)
    return render(request, 'userauths/password_reset_confirm.html', {'form': form})


User = get_user_model()
def password_reset_request(request):
    if request.method == 'POST':
        data = request.POST.get('email_or_phone')
        try:
            user = User.objects.get(Q(email=data)| Q(phone=data))
            otp = otp_token_generator.generate_otp()

            # Save OTP and its expiration time in the user's session
            otp_expiration_time = timezone.now() + timedelta(minutes=5)  # Set expiration time to 5 minutes
            request.session['password_reset_otp'] = {
                'otp': otp,
                'expiration_time': otp_expiration_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            request.session['password_reset_user_id'] = user.id

            associated_user = User.objects.get(Q(email=data) | Q(phone=data))
            subject = "Password Reset Request"
            reset_code = account_activation_token.make_token(associated_user)
            uid = urlsafe_base64_encode(force_bytes(associated_user.pk))
            domain = get_current_site(request).domain
            protocol = 'https' if request.is_secure() else 'http'
            context = {
                'user': associated_user,
                'domain': domain, 
                'uid': uid,
                'token': reset_code,
                'protocol': protocol,
                'otp': otp,
            }
            
            if "@" in data:
                message = render_to_string('userauths/template_reset_password.html', context)
                email = EmailMessage(subject, message, to=[associated_user.email])
                email.content_subtype = "html"
                email.send()
            else:
                try:
                    message = f'Your OTP is: {otp}'
                    send_sms(associated_user.phone, message)
                except:
                    print('')
            return JsonResponse({'redirect_url': reverse('userauths:confirm'),'message': 'Password reset instructions sent.'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'error': 'No user is associated with this email or phone number.'}, status=400)
    
    return render(request, 'password_reset.html')


def activation_confirm_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_data = request.session.get('account_activation_otp')
        user_id = request.session.get('account_register_id')

        if session_data:
            session_otp = session_data.get('activation_otp')
            expiration_time = session_data.get('activation_expiration_time')
            current_time_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

            # Check if the OTP is not expired
            if expiration_time and current_time_str <= expiration_time:
                if entered_otp and session_otp and int(entered_otp) == int(session_otp):
                    try:
                        user = User.objects.get(pk=user_id)
                        if user is not None:
                            # OTP is correct, allow user to reset the password
                            user.is_active = True
                            user.save()
                            next_page = request.session.get('next_page', reverse('userauths:dashboard'))
                            return JsonResponse({
                                'message': 'OTP confirmed. Redirecting...',
                                'redirect_url': next_page
                            }, status=200)
                        
                    except User.DoesNotExist:
                        return JsonResponse({'error': 'Invalid user.'}, status=400)
                else:
                    return JsonResponse({'error': 'Invalid OTP. Please try again.'}, status=400)
            else:
                # OTP has expired
                return JsonResponse({'error': 'OTP has expired. Please request a new OTP.'}, status=400)
        else:
            return JsonResponse({'error': 'No OTP found in the session. Please request a new OTP.'}, status=400)

    return render(request, 'activate_account.html')


def password_reset_confirm_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_data = request.session.get('password_reset_otp')
        user_id = request.session.get('password_reset_user_id')

        if session_data:
            session_otp = session_data.get('otp')
            expiration_time = session_data.get('expiration_time')
            current_time_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

            # Check if the OTP is not expired
            if expiration_time and current_time_str <= expiration_time:
                if entered_otp and session_otp and int(entered_otp) == int(session_otp):
                    try:
                        user = User.objects.get(pk=user_id)
                        if user is not None:
                            # OTP is correct, allow user to reset the password
                            request.session['otp_verified_user_id'] = user.id
                            return JsonResponse({
                                'message': 'OTP confirmed. Redirecting...',
                                'redirect_url': reverse('userauths:change')
                            }, status=200)
                        
                    except User.DoesNotExist:
                        return JsonResponse({'error': 'Invalid user.'}, status=400)
                else:
                    return JsonResponse({'error': 'Invalid OTP. Please try again.'}, status=400)
            else:
                # OTP has expired
                return JsonResponse({'error': 'OTP has expired. Please request a new OTP.'}, status=400)
        else:
            return JsonResponse({'error': 'No OTP found in the session. Please request a new OTP.'}, status=400)

    return render(request, 'password_reset_confirm.html')



def password_reset_complete(request):
    if request.method == 'POST':
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        user_id = request.session.get('otp_verified_user_id')

        if new_password != confirm_password:
            return JsonResponse({'error': 'Passwords do not match.'}, status=400)

        if user_id:
            try:
                user = User.objects.get(pk=user_id)
                if user.check_password(new_password):
                    return JsonResponse({'error': 'New password cannot be the same as the old password.'}, status=400)

                user.set_password(new_password)
                user.is_active = True
                user.save()
                return JsonResponse({'redirect_url': reverse('userauths:password'), 'message': 'Your password has been reset successfully.'}, status=200)
            except User.DoesNotExist:
                return JsonResponse({'error': 'Invalid user.'}, status=400)
        else:
            return JsonResponse({'error': 'User verification failed.'}, status=400)

    return render(request, 'password_change.html')

# def password_reset_request(request):
#     data = request.POST.get('password')
#     email_or_phone = request.session.get('email_or_phone')
#     if not email_or_phone:
#         messages.error(request, "Please enter your email or phone number first.")
#         return redirect('userauths:email')
#     if request.method == 'POST':
#         data = request.POST.get('password')
#         email = request.POST.get('email')
#         try:
#             user = User.objects.get(email=email)
#             otp = otp_token_generator.generate_otp()
            
#             # Save OTP in the user's session for validation (you can choose another storage method)
#             request.session['password_reset_otp'] = otp
#             request.session['password_reset_user_id'] = user.id

#             # Send the OTP via email
#             mail_subject = 'Your password reset OTP'
#             message = render_to_string('registration/password_reset_email.html', {
#                 'otp': otp,
#             })
#             send_mail(mail_subject, message, 'from@example.com', [email])

#             messages.success(request, 'An OTP has been sent to your email.')
#             return redirect('password_reset_confirm_otp')
#         except User.DoesNotExist:
#             messages.error(request, 'Email address not found.')
#     return render(request, 'registration/password_reset_form.html')

# def passwordResetConfirm(request, uidb64, token):
#     User = get_user_model()
#     try:
#         uid = force_str(urlsafe_base64_decode(uidb64))
#         user = User.objects.get(pk=uid)
#     except:
#         user = None

#     if user is not None and account_activation_token.check_token(user, token):
#         if request.method == 'POST':
#             form = SetPasswordForm(user, request.POST)
#             if form.is_valid():
#                 form.save()
#                 messages.success(request, "Your password has been set. You may go ahead and <b>log in</b> now.")
#                 return redirect("userauths:sign-in")
#             else:
#                 for error in list(form.errors.values()):
#                     messages.error(request, error)

#         form = SetPasswordForm(user)
#         return render(request, 'userauths/password_reset_confirm.html', {'form': form})
#     else:
#         messages.error(request, "Link is expired")

#     messages.error(request, 'Something went wrong, redirecting back to Homepage')
#     return redirect(request.META.get("HTTP_REFERER", "core:index"))

def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email', None)

        if not email:
            messages.error(request, "You must type legit email to subscribe to a Newsletter")
            return redirect(request.META.get("HTTP_REFERER", "core:index"))

        if get_user_model().objects.filter(email=email).first():
            messages.error(request, f"Found registered user with associated {email} email. You must login to subscribe or unsubscribe.")
            return redirect(request.META.get("HTTP_REFERER", "core:index")) 

        subscribe_user = SubscribedUsers.objects.filter(email=email).first()
        if subscribe_user:
            messages.error(request, f"{email} email address is already subscriber.")
            return redirect(request.META.get("HTTP_REFERER", "core:index"))  

        try:
            validate_email(email)
        except ValidationError as e:
            messages.error(request, e.messages[0])
            return redirect("core:index")

        subscribe_model_instance = SubscribedUsers()
        subscribe_model_instance.email = email
        subscribe_model_instance.save()
        messages.success(request, f'{email} email was successfully subscribed to our newsletter!')
        return redirect(request.META.get("HTTP_REFERER", "core:index"))  



# @user_is_superuser
# def newsletter(request):
#     if request.method == 'POST':
#         form = NewsletterForm(request.POST)
#         if form.is_valid():
#             subject = form.cleaned_data.get('subject')
#             receivers = form.cleaned_data.get('receivers').split(',')
#             email_message = form.cleaned_data.get('message')

#             mail = EmailMessage(subject, email_message, f"PyLessons <{request.user.email}>", bcc=receivers)
#             mail.content_subtype = 'html'

#             if mail.send():
#                 messages.success(request, "Email sent succesfully")
#             else:
#                 messages.error(request, "There was an error sending email")

#         else:
#             for error in list(form.errors.values()):
#                 messages.error(request, error)

#         return redirect('/')

#     form = NewsletterForm()
#     form.fields['receivers'].initial = ','.join([active.email for active in SubscribedUsers.objects.all()])
#     return render(request=request, template_name='userauths/newsletter.html', context={'form': form})

