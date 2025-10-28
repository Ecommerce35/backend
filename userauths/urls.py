from django.urls import path, include
from userauths import views

app_name = "userauths"

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path("cp/signup/", views.register_view, name="sign_up"),
    path("cp/email/", views.email_or_phone_view, name="email"),
    path("cp/signin/", views.password_view, name="password"),
    # path("sign-in/", views.login_view, name="sign-in"),
    path("sign-out/", views.logout_view, name="sign_out"),
    # path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('social/signup', views.signup_redirect, name='signup_redirect'),
    path('pip', views.vendor_signup, name='vendor_signup'),
    path("cp/reset/", views.password_reset_request, name="reset"),
    path("cp/acivate/", views.activation_confirm_otp, name="activate"),
    path("cp/confirm/", views.password_reset_confirm_otp, name="confirm"),
    path("cp/change/", views.password_reset_complete, name="change"),
    # path("password-change/", views.password_change, name="password-change"),
    # path("reset/<uidb64>/<token>", views.passwordResetConfirm, name="password-reset-confirm"),
    path("profile/update/", views.profile_update, name="profile-update"),
    path('dashboard/', views.vendor_dashboard, name='vendor-dashboard'),

    path('register/', views.RegisterUserView.as_view(), name='register'),
    path('verify/', views.VerifyOTPView.as_view(), name='verify'),
    path('resend-otp/', views.ResendOTPView.as_view(), name='resend-otp'),
    path('login/', views.LoginUserView.as_view(), name='login'),
    path('logout/', views.LogOutView.as_view(), name='login'),
    path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='custom_token_refresh'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm')

]