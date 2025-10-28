from rest_framework import serializers
from product.models import  *
from order.models import *
from .models import Slider, Banners
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from userauths.utils import send_sms
from django.utils import timezone
from datetime import timedelta
from userauths.tokens import otp_token_generator
from django.db.models.query_utils import Q
from address.models import *


User = get_user_model()



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','first_name', 'last_name', 'email', 'phone', 'role']

class MainCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Main_Category
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    main_category = MainCategorySerializer()

    class Meta:
        model = Category
        fields = '__all__'

class SubCategorySerializer(serializers.ModelSerializer):
    category = CategorySerializer()

    class Meta:
        model = Sub_Category
        fields = '__all__'

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'

class OpeningHourSerializer(serializers.ModelSerializer):
    day = serializers.CharField(source='get_day_display')  # Display day name instead of integer

    class Meta:
        model = OpeningHour
        fields = ['day', 'from_hour', 'to_hour', 'is_closed']

class AboutSerializer(serializers.ModelSerializer):
    # If you want to display related fields (like vendor's email or name), add custom fields
    vendor_email = serializers.EmailField(source="vendor.email", read_only=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    
    class Meta:
        model = About
        fields = [
            'vendor_email', 'vendor_name', 'profile_image', 'cover_image', 'address', 
            'about', 'latitude', 'longitude', 'shipping_on_time', 'chat_resp_time', 
            'authentic_rating', 'day_return', 'waranty_period', 'facebook_url', 
            'instagram_url', 'twitter_url', 'linkedin_url'
        ]

class VendorSerializer(serializers.ModelSerializer):
    opening_hours = OpeningHourSerializer(many=True, read_only=True, source='openinghour_set')
    is_open_now = serializers.SerializerMethodField()  # Custom field to check if the vendor is open now
    about = AboutSerializer(read_only=True)

    class Meta:
        model = Vendor
        fields = [
            'id', 'name', 'slug', 'about', 'email', 'country', 'contact', 'is_featured', 'is_approved', 'followers', 
            'is_subscribed', 'subscription_end_date', 'created_at', 'modified_at', 'is_open_now', 'opening_hours'
        ]

    def get_is_open_now(self, obj):
        return obj.is_open()

class RegionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Region
        fields = '__all__'

class ProductReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Use StringRelatedField to display the user, but make it read-only
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())  # Handle product as a related field
    product_image = serializers.SerializerMethodField()
    

    class Meta:
        model = ProductReview
        fields = ['review', 'rating', 'product', 'user', 'date', 'product_image']  # Include 'user' as read-only
        extra_kwargs = {'user': {'read_only': True}}
    
    def get_product_image(self, obj):
        # Access the image field from the related Product instance
        return obj.product.image.url if obj.product.image else None

    def create(self, validated_data):
        # Pop user from context and assign it explicitly
        user = self.context['request'].user
        review = ProductReview.objects.create(user=user, **validated_data)
        return review

class ProductSerializer(serializers.ModelSerializer):
    sub_category = SubCategorySerializer()
    vendor = VendorSerializer()
    brand = BrandSerializer()
    available_in_regions =  RegionSerializer(many=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)


    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "sub_category",
            "vendor",
            "reviews",
            "variant",
            "brand",
            "status",
            "title",
            "image",
            "video",
            "price",
            "old_price",
            "features",
            "description",
            "specifications",
            "delivery_returns",
            "available_in_regions",
            "product_type",
            "total_quantity",
            "weight",
            "volume",
            "life",
            "mfd",
            "deals_of_the_day",
            "recommended_for_you",
            "popular_product",
            "delivery_options",
            "sku",
            "date",
            "updated",
            "views",
        ]
    

class ProductImageSerializer(serializers.ModelSerializer):
    # product = ProductSerializer()

    class Meta:
        model = ProductImages
        fields = '__all__'

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = '__all__'

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'

class VariantSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    size = SizeSerializer()
    color = ColorSerializer()

    class Meta:
        model = Variants
        fields = '__all__'

class VariantImageSerializer(serializers.ModelSerializer):
    variant = VariantSerializer()

    class Meta:
        model = VariantImage
        fields = '__all__'


class WishlistSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'product', 'saved_at']

    def validate_product(self, value):
        """
        Ensure the product exists and is active (optional business rule).
        """
        if not value.status == 'published':
            raise serializers.ValidationError("The product is not available for saving.")
        return value

    def create(self, validated_data):
        """
        Ensure that the same product cannot be added multiple times for the same user.
        """
        user = validated_data['user']
        product = validated_data['product']
        wishlist_item, created = Wishlist.objects.get_or_create(user=user, product=product)
        if not created:
            raise serializers.ValidationError("This product is already in your wishlist.")
        return wishlist_item

class ProductDeliveryOptionSerializer(serializers.ModelSerializer):
    delivery_date_range = serializers.SerializerMethodField()

    class Meta:
        model = ProductDeliveryOption
        fields = ['product', 'variant', 'delivery_option', 'default', 'delivery_date_range']

    # This method calls the get_delivery_date_range method from the model
    def get_delivery_date_range(self, obj):
        return obj.get_delivery_date_range()

class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = ['code', 'discount_amount', 'discount_percentage', 'valid_from', 'valid_to', 'active', 'max_uses', 'used_count', 'min_purchase_amount', 'is_valid']

    # Custom method to return the validity status of the coupon
    def get_is_valid(self, obj):
        return obj.is_valid()
    

class SavedProductSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects)

class ProductWithRatingSerializer(serializers.ModelSerializer):
    average_rating_percentage = serializers.FloatField()
    variants = VariantSerializer(many=True)
    colors = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'image', 'variants', 'colors']

    def get_colors(self, obj):
        product_variants = Variants.objects.filter(product=obj)
        return product_variants.values('color__name', 'color__code').distinct()


class SliderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slider
        fields = ['image', 'discount_deal', 'sale', 'brand_name', 'discount', 'link']


class BannersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banners
        fields = ['image', 'link', 'title']

class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Sub_Category
        fields = '__all__'


#################################AUTH#########################################

class UserRegistrationSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'password', 'latitude', 'longitude']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    
    def validate(self, data):
        # Add custom validation logic here if needed
        if 'phone' in data and not data['phone'].isdigit():
            raise serializers.ValidationError({'phone': 'Phone number must be digits only.'})
        return data

##########################################################################

from rest_framework import serializers
from .models import DeliveryOption  # Adjust the import according to your project structure

class DeliveryOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryOption
        fields = '__all__'  # This will include all fields in the model
        read_only_fields = []  # Specify any fields that should be read-only, if necessary

    def create(self, validated_data):
        """Override the create method if you want to customize the creation of DeliveryOption."""
        return DeliveryOption.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Override the update method if you want to customize the update of DeliveryOption."""
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.min_days = validated_data.get('min_days', instance.min_days)
        instance.max_days = validated_data.get('max_days', instance.max_days)
        instance.cost = validated_data.get('cost', instance.cost)
        instance.save()
        return instance


class ProductDeliveryOptionSerializer(serializers.ModelSerializer):
    delivery_option = DeliveryOptionSerializer()

    class Meta:
        model = ProductDeliveryOption
        fields = '__all__'

    def get_delivery_date_range(self, obj):
        now = datetime.now()
        if (obj.delivery_option.name.lower() == "same-day delivery" or 
            obj.delivery_option.name.lower() == "same-day" and now.hour >= 10):
            return 'Tomorrow'
        elif (obj.delivery_option.name.lower() == "same-day delivery" or 
              obj.delivery_option.name.lower() == "same-day" and now.hour <= 9):
            return 'Today'

        min_delivery_date = now + timedelta(days=obj.delivery_option.min_days)
        max_delivery_date = now + timedelta(days=obj.delivery_option.max_days)
        return f"{min_delivery_date.strftime('%d %B')} to {max_delivery_date.strftime('%d %B')}"


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    variant = VariantSerializer()
    delivery_option = DeliveryOptionSerializer()
    delivery_range = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['product','id', 'variant', 'quantity', 'delivery_option', 'delivery_range']  # Specify required fields explicitly

    def validate(self, attrs):
        if 'quantity' not in attrs:
            raise serializers.ValidationError("Quantity is required.")
        # Add more validations if needed
        return attrs
    
    def get_delivery_range(self, obj):
        """
        Calculate the delivery range for the cart item's delivery option.
        """
        delivery_option = obj.delivery_option

        if delivery_option:
            # Calculate delivery range based on min_days and max_days
            min_delivery_date = timezone.now() + timezone.timedelta(days=delivery_option.min_days)
            max_delivery_date = timezone.now() + timezone.timedelta(days=delivery_option.max_days)

            return f"{min_delivery_date.strftime('%d %B')} to {max_delivery_date.strftime('%d %B')}"

        return "No delivery option selected."
    
class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    total_items = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = '__all__'

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'user','latitude','longitude','full_name', 'country', 'region', 'town', 'address', 'gps_address', 'email', 'mobile', 'status','date_added']
        read_only_fields = ['id', 'date_added']