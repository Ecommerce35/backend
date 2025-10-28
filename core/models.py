from django.db import models

# Create your models here.
from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from userauths.models import User
from taggit.managers import TaggableManager
from ckeditor_uploader.fields import RichTextUploadingField
from django.urls import reverse
from django.utils.text import slugify
from django_countries.fields import CountryField
from vendor.models import *
from product.models import *
import math


class CurrencyRate(models.Model):
    currency = models.CharField(max_length=3, unique=True)
    rate = models.FloatField()

    def __str__(self):
        return f"{self.currency} - {self.rate}"

STATUS_CHOICE = (
    ("processing", "Processing"),
    ("delivered", "Delivered"),
    ("shipped", "Shipped"),
)

STATUS = (
    ("draft", "Draft"),
    ("disabled", "Disabled"),
    ("rejected", "Rejected"),
    ("in_review", "In Review"),
    ("published", "Published"),
)

RATING = (
    (1, "★✰✰✰✰"),
    (2, "★★✰✰✰"),
    (3, "★★★✰✰"),
    (4,"★★★★✰"),
    (5,"★★★★★"),
)


def user_directory_path(instance, filename):
    return 'user_{0}/{1}'.format(instance.user.id, filename)

# Create your models here.

############################################################
####################### MAIN SLIDER MODEL ##################
############################################################

class Slider(models.Model):
    DISCOUNT_DEAL = (
        ('hot deals','HOT DEALS'),
        ('new arrivals','NEW ARRIVALS'),
    )
    image = models.ImageField(upload_to='slider_imgs')
    discount_deal = models.CharField(choices=DISCOUNT_DEAL, max_length=100)
    sale = models.IntegerField()
    brand_name = models.CharField(max_length=200)
    discount = models.IntegerField()
    link = models.CharField(max_length=200)

    def __str__(self):
        return self.brand_name
    

############################################################
####################### MAIN BANNERS MODEL ##################
############################################################

class Banners(models.Model):
    image = models.ImageField(upload_to='banner_imgs')
    link = models.CharField(max_length=200)
    title = models.CharField(max_length=100, unique=True, default="Food")


    def __str__(self):
        return self.title

############################################################
####################### IMAGE MODEL ##################
############################################################



