from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
# from userauths.models import User

# UserModel = get_user_model()

# class EmailBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         try:
#             user = UserModel.objects.get(email__iexact=username)  # Query using email
#         except UserModel.DoesNotExist:
#             return None

#         if user.check_password(password) and self.user_can_authenticate(user):
#             return user
        
# class EmailOrPhoneBackend(ModelBackend):
#     def authenticate(self, request, email_or_phone=None, password=None, **kwargs):
#         User = get_user_model()
#         try:
#             user = User.objects.get(
#                 Q(email=email_or_phone) | Q(phone=email_or_phone)
#             )
#             if user.check_password(password):
#                 return user
#         except User.DoesNotExist:
#             return None

#     def get_user(self, user_id):
#         User = get_user_model()
#         try:
#             return User.objects.get(pk=user_id)
#         except User.DoesNotExist:
#             return 

User = get_user_model()


class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, email_or_phone=None, password=None, **kwargs):
        try:
            data = email_or_phone
            user = User.objects.get(Q(email=data) | Q(phone=data))
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None