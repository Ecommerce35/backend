from enum import unique
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import post_save
from django.utils import timezone

from django.utils.translation import gettext_lazy as _
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from rest_framework_simplejwt.tokens import RefreshToken
# from address.models import Country, Region, Town

ROLE_CHOICES = (
    ('vendor', 'Vendor'),
    ('customer', 'Customer'),
    ('technical', 'Technical'),
    ('support', 'Support'),
    ('manager', 'Manager'),
    ('admin', 'Admin'),
)

class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, email, phone, password=None):
        if not email:
            raise ValueError('Please provide an email address')

        if not phone:
            raise ValueError('Please provide a phone number')

        user = self.model(
            email=self.normalize_email(email),
            phone=phone,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, phone, password=None):
        user = self.create_user(
            email=self.normalize_email(email),
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        user.role = 'admin'  # Assign a default role for superuser, adjust as needed
        user.is_superuser = True
        user.is_active = True
        user.is_admin = True
        user.is_staff = True
        user.save(using=self._db)
        return user

AUTH_PROVIDER = { 
    'email': 'email',
    'google': 'google',
}

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    email = models.EmailField(max_length=128, unique=True)
    phone = models.CharField(max_length=32, unique=True)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    auth_provider = models.CharField(max_length=50, default=AUTH_PROVIDER.get('email'))

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']

    objects = UserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return True
    
    def tokens(self):
        refresh = RefreshToken.for_user(self)  # Pass the user instance
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

def user_directory_path(instance, filename):
    return 'user_{0}/{1}'.format(instance.user.id, filename)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other','Other')], blank=True, null=True)
    address = models.CharField(max_length=900, blank=True, null=True)
    newsletter_subscription = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email

    def save(self, *args, **kwargs):
        super(Profile, self).save(*args, **kwargs)
        if not self.profile_image:
            self.generate_initials_profile_picture()

    def generate_initials_profile_picture(self):
        # Generate initials from user's first and last name
        initials = self.user.first_name[0] + self.user.last_name[0] if self.user.first_name and self.user.last_name else 'U'

        # Create an image with initials
        image = Image.new('RGB', (200, 200), (255, 255, 255))  # White background
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("arial.ttf", 80)
        
        # Get the bounding box of the text
        text_bbox = draw.textbbox((0, 0), initials, font=font)
        
        # Extract width and height from the bounding box
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Center the text
        text_position = ((200 - text_width) // 2, (200 - text_height) // 2)
        
        # Draw the text on the image
        draw.text(text_position, initials, font=font, fill=(0, 0, 0))  # Black text
        
        # Save image to a BytesIO buffer
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Save image to ImageField
        self.profile_image.save(f'{self.user.email}_profile.png', ContentFile(buffer.read()), save=True)


    


class ContactUs(models.Model):
    full_name = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    phone = models.CharField(max_length=200) # +234 (456) - 789
    subject = models.CharField(max_length=200) # +234 (456) - 789
    message = models.TextField()

    class Meta:
        verbose_name = "Contact Us"
        verbose_name_plural = "Contact Us"

    def __str__(self):
        return self.full_name
    
class SubscribedUsers(models.Model):
    email = models.EmailField(unique=True, max_length=100)
    created_date = models.DateTimeField('Date created', default=timezone.now)

    def __str__(self):
        return self.email
    
class MailMessage(models.Model):
    title = models.CharField(max_length=200, null=True)
    message = models.TextField()


    def __str__(self):
        return self.title
    
    
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)

# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()

 
# post_save.connect(create_user_profile, sender=User)
# post_save.connect(save_user_profile, sender=User)   




