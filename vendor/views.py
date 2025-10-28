import datetime
from django.shortcuts import get_object_or_404, redirect, render
from core.models import * 
from .models import *
from userauths.models import *
from order.models import *
from userauths.forms import *
from django.contrib import messages
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse
from userauths.utils import is_vendor
from .utils import get_vendor
from .forms import *
import json
from django.shortcuts import render, get_object_or_404, redirect
from .forms import ProductForm, ProductImagesForm, VariantsForm, VariantImageForm
from product.models import Product, ProductImages, Variants, VariantImage
from django.contrib.auth.decorators import login_required, user_passes_test

# Create your views here.
#############################################################
#################### VENDOR #################################
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import About, Vendor
from .serializers import AboutSerializer
from django.shortcuts import get_object_or_404
from .permissions import IsVendor
from .serializers import *
from django.db.models import Avg, Count
from django.db.models.functions import TruncMonth
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import OpeningHour, Vendor
from .serializers import OpeningHourSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from rest_framework.exceptions import NotFound
from django.db.models import Sum


class VendorSignUpView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def get_vendor(self, request):
        vendor = Vendor.objects.filter(user=request.user).first()
        return vendor

    def post(self, request, *args, **kwargs):
        existing_vendor = self.get_vendor(request)
        if existing_vendor:
            return Response(
                {
                    "error": "User is already associated with a vendor",
                    "details": {
                        "storeName": existing_vendor.name,
                        "email": existing_vendor.email,
                        "contact": existing_vendor.contact,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vendor-related data
        vendor_data = {
            "name": request.data.get("storeName"),
            "email": request.data.get("businessEmail"),
            "contact": request.data.get("phoneNumber"),
            "country": request.data.get("country"),
            "business_type": request.data.get("businessType"),
            "vendor_type": request.data.get("vendorType"),
            "license": request.data.get("license"),
            "student_id": request.data.get("studentId"),
        }

        try:
            # Use a transaction to ensure atomicity
            with transaction.atomic():
                # Validate and save vendor
                vendor_serializer = VendorRegistrationSerializer(data=vendor_data)
                if not vendor_serializer.is_valid():
                    print(vendor_serializer.errors)
                    return Response(
                        {"error": "Vendor validation failed", "details": vendor_serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                vendor = vendor_serializer.save(user=request.user)

                # Ensure the About instance is created
                about, created = About.objects.get_or_create(vendor=vendor)

                # Update the About instance
                about.profile_image = request.data.get("profilePicture")
                about.cover_image = request.data.get("coverImage")
                about.address = request.data.get("businessAddress")
                about.about = request.data.get("about")
                about.latitude = request.data.get("latitude")
                about.longitude = request.data.get("longitude")
                about.save()

                # Payment method data
                payment_data = {
                    "vendor": vendor.id,
                    "payment_method": request.data.get("paymentMethod"),
                    "momo_number": request.data.get("momoNumber"),
                    "momo_provider": request.data.get("momoProvider"),
                    "bank_name": request.data.get("bankName"),
                    "bank_account_name": request.data.get("bankAccountName"),
                    "bank_account_number": request.data.get("bankAccountNumber"),
                    "bank_routing_number": request.data.get("bankRoutingNumber"),
                    "country": request.data.get("country"),
                }

                # Validate and save payment details
                payment_serializer = VendorPaymentMethodSerializer(data=payment_data)
                if not payment_serializer.is_valid():
                    return Response(
                        {"error": "Payment method validation failed", "details": payment_serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                payment_serializer.save(vendor=vendor)

        except Exception as e:
            return Response(
                {"error": "Something went wrong during vendor registration", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "Vendor registered successfully!"},
            status=status.HTTP_201_CREATED,
        )

class VendorDetailView(APIView):
    
    def get(self, request, slug):
        try:
            vendor = Vendor.objects.get(slug=slug)
            # Fetch associated products
            products = Product.objects.filter(vendor=vendor, status='published').annotate(
            average_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )
        except Vendor.DoesNotExist:
            return Response({'error': 'Vendor not found'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the vendor data
        vendor_serializer = VendorSerializer(vendor)
        
        # Serialize the products
        product_serializer = ProductSerializer(products, many=True)

        reviews = ProductReview.objects.filter(product__in=products, status=True).order_by("-date")
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg']

        products_with_details = []
        for product in products:
            product_variants = Variants.objects.filter(product=product)
            product_colors = product_variants.values('color__name', 'color__code', 'sku').distinct()

            product_data = {
                'product': ProductSerializer(product).data,  # Serialize the product instance
                'average_rating': product.average_rating or 0,
                'review_count': product.review_count or 0,
                'variants': VariantsSerializer(product_variants, many=True).data,
                'colors': list(product_colors),  # ensure list is serialized correctly
            }
            products_with_details.append(product_data)


        today_date = date.today()
        today = today_date.isoweekday()
        today_operating_hours = OpeningHour.objects.filter(vendor=vendor, day=today).first()

        is_following = False
        if request.user.is_authenticated:
            is_following = vendor.followers.filter(id=request.user.id).exists()

        # Prepare the response data
        response_data = {
            'vendor': vendor_serializer.data,
            'products': products_with_details,
            'average_rating': average_rating,
            "reviews": ProductReviewSerializer(reviews, many=True).data,
            'today_operating_hours': OpeningHourSerializer(today_operating_hours).data,
            'followers_count': vendor.followers.count(),
            'is_following': is_following,
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
    def post(self, request, slug):
        if not request.user.is_authenticated:
            return Response({'error': 'Please login to follow this vendor'}, status=status.HTTP_403_FORBIDDEN)

        try:
            vendor = Vendor.objects.get(slug=slug)
        except Vendor.DoesNotExist:
            return Response({'error': 'Vendor not found'}, status=status.HTTP_404_NOT_FOUND)

        # Toggle follow/unfollow
        if vendor.followers.filter(id=request.user.id).exists():
            vendor.followers.remove(request.user)
            is_following = False
        else:
            vendor.followers.add(request.user)
            is_following = True

        response_data = {
            'is_following': is_following,
            'followers_count': vendor.followers.count(),
        }

        return Response(response_data, status=status.HTTP_200_OK)


class VendorPaymentMethodAPIView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get_vendor(self, request):
        """Retrieve the vendor associated with the current user, if exists."""
        return get_object_or_404(Vendor, user=request.user)
   
    def get(self, request, *args, **kwargs):
        """
        Retrieve the payment method for the authenticated vendor.
        """
        vendor = self.get_vendor(request) # Assuming vendor is linked to the user model
        payment_method = VendorPaymentMethod.objects.filter(vendor=vendor).first()

        if not payment_method:
            return Response({"detail": "Payment method not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = VendorPaymentMethodSerializer(payment_method)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Create a payment method for the authenticated vendor.
        """
        vendor = self.get_vendor(request) # Assuming vendor is linked to the user model
        
        # Check if the vendor already has a payment method
        if VendorPaymentMethod.objects.filter(vendor=vendor).exists():
            return Response(
                {"detail": "Vendor already has a payment method. Use PUT to update."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = request.data
        data['vendor'] = vendor.id  # Ensure vendor is linked to the authenticated user
        serializer = VendorPaymentMethodSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        Update the payment method for the authenticated vendor.
        """
        vendor = self.get_vendor(request)

        payment_method = get_object_or_404(VendorPaymentMethod, vendor=vendor)

        data = request.data
        serializer = VendorPaymentMethodSerializer(payment_method, data=data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OpeningHourDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_vendor(self, request):
        """Retrieve the vendor associated with the current user, if exists."""
        return get_object_or_404(Vendor, user=request.user)
    
    def get(self, request, *args, **kwargs):
        vendor = self.get_vendor(request)
        opening_hours = OpeningHour.objects.filter(vendor=vendor)
        serializer = OpeningHourSerializer(opening_hours, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        vendor = self.get_vendor(request)
        # serializer = OpeningHourSerializer(data=request.data)
        serializer = OpeningHourSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(vendor=vendor)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None, *args, **kwargs):
        """Fully update an existing opening hour entry."""
        vendor = self.get_vendor(request)
        opening_hour = get_object_or_404(OpeningHour, pk=pk, vendor=vendor)
        serializer = OpeningHourSerializer(opening_hour, data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk=None, *args, **kwargs):
        """Partially update an existing opening hour entry."""
        vendor = self.get_vendor(request)
        opening_hour = get_object_or_404(OpeningHour, pk=pk, vendor=vendor)
        serializer = OpeningHourSerializer(opening_hour, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        """Delete an existing opening hour entry."""
        vendor = self.get_vendor(request)
        opening_hour = get_object_or_404(OpeningHour, pk=pk, vendor=vendor)
        opening_hour.delete()
        return Response({"detail": "Opening hour deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class UpdateOrderProductStatusAPIView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get_vendor(self, request):
        """Retrieve the vendor associated with the current user."""
        return get_object_or_404(Vendor, user=request.user)

    def put(self, request, id):
        """
        Allow a vendor to update the status of their products in an order.
        """
        vendor = self.get_vendor(request)

        # Retrieve the OrderProduct
        order_product = get_object_or_404(
            OrderProduct.objects.filter(product__vendor=vendor),  # Ensure vendor ownership
            id=id
        )

        # Update the status
        status_value = request.data.get("status")
        if status_value not in dict(OrderProduct._meta.get_field('status').choices):
            return Response({"error": "Invalid status value"}, status=status.HTTP_400_BAD_REQUEST)

        order_product.status = status_value
        order_product.save()

        # Serialize and return the updated object
        serializer = OrderProductSerializer(order_product)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateOrderStatusAPIView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get_vendor(self, request):
        """Retrieve the vendor associated with the current user, if exists."""
        return get_object_or_404(Vendor, user=request.user)

    def put(self, request, order_id):
        vendor = self.get_vendor(request)
        # Get the status from the request data
        new_status = request.data.get('status')
        
        # Validate that the status is one of the allowed choices
        valid_status_choices = dict(Order.STATUS_CHOICES).keys()
        if new_status not in valid_status_choices:
            return Response(
                {"error": "Invalid status choice."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            # Retrieve the order based on the order_id
            order = Order.objects.get(id=order_id)
            
            # Update the status and save the order
            order.status = new_status
            order.save()

            # Serialize and return the updated order data
            serializer = OrderSerializer(order, context={'vendor': vendor})
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class OrderDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get_vendor(self, request):
        """Retrieve the vendor associated with the current user, if exists."""
        return get_object_or_404(Vendor, user=request.user)

    def get(self, request, id):
        try:
            vendor = self.get_vendor(request)
            order = Order.objects.get(id=id, vendors__in=[vendor])  # Ensure the vendor is part of the order
            serializer = OrderSerializer(order, context={'vendor': vendor})  # Pass vendor context to the serializer
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


class VendorAPIView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get_vendor(self, request):
        """Retrieve the vendor associated with the current user, if exists."""
        return get_object_or_404(Vendor, user=request.user)

    def get(self, request, format=None):
        """
        GET: Retrieve all orders for the authenticated vendor.
        """
        vendor = self.get_vendor(request)

        # Fetch products for the vendor
        products = Product.objects.filter(vendor=vendor, status='published').annotate(
            average_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )

        # Fetch orders associated with the vendor
        orders = Order.objects.filter(vendors=vendor)
        vendor_serializer = VendorSerializer(vendor)
        product_serializer = ProductSerializer(products, many=True)

        # Get orders by month
        orders_by_month = (
            Order.objects.filter(vendors=vendor)
            .annotate(month=TruncMonth("date_created"))
            .values("month")
            .annotate(order_count=Count("id"))
            .order_by("month")
        )

        # Get reviews for the vendor's products
        reviews = ProductReview.objects.filter(product__in=products, status=True).order_by("-date")
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        order_serializer = OrderSerializer(orders, many=True, context={'vendor': vendor})

        # Calculate product sales
        product_sales = []
        for product in products:
            sales_count = (
                OrderProduct.objects.filter(order__in=orders, product=product)
                .aggregate(total_sales=Sum('quantity'))['total_sales'] or 0
            )
            product_sales.append({
                'product': ProductSerializer(product).data,
                'sales_count': sales_count
            })

        # Response data
        response_data = {
            'vendor': vendor_serializer.data,
            'products': product_serializer.data,
            'orders': order_serializer.data,
            'average_rating': average_rating,
            "reviews": ProductReviewSerializer(reviews, many=True).data,
            'followers_count': vendor.followers.count(),
            'orders_by_month': list(orders_by_month),
            'product_sales': product_sales,  # Add product sales data
        }

        return Response(response_data, status=status.HTTP_200_OK)

class AboutAPIView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get_vendor(self, request):
        """Retrieve the vendor associated with the current user, if exists."""
        return get_object_or_404(Vendor, user=request.user)

    def get(self, request, format=None):
        """
        GET: Retrieve the About instance for the authenticated vendor or list all instances if not a vendor.
        """
        # If the user is authenticated and is a vendor, retrieve their About instance
        # if request.user.is_authenticated and hasattr(request.user, 'vendor_user'):
        vendor = self.get_vendor(request)
        about = get_object_or_404(About, vendor=vendor)
        serializer = AboutSerializer(about)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        """
        POST: Create a new About instance for the authenticated vendor.
        """
        vendor = self.get_vendor(request)
        serializer = AboutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(vendor=vendor)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, format=None):
        """
        PUT: Update the About instance for the authenticated vendor.
        """        
        # Get the authenticated vendor
        vendor = self.get_vendor(request)
        
        # Fetch the About instance for the vendor or return 404 if not found
        about = get_object_or_404(About, vendor=vendor)
        
        # Use the serializer with partial updates
        serializer = AboutSerializer(about, data=request.data, partial=True)
        
        # Check if the serializer data is valid
        if serializer.is_valid():
            # Save the validated data
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        # If there are validation errors, print them for debugging
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, format=None):
        """
        DELETE: Remove the About instance for the authenticated vendor.
        """
        vendor = self.get_vendor(request)
        about = get_object_or_404(About, vendor=vendor)
        about.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VendorProducts(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get_vendor(self, request):
        """Retrieve the vendor associated with the current user, if exists."""
        return get_object_or_404(Vendor, user=request.user)
    
    def get(self, request, *args, **kwargs):
        vendor = self.get_vendor(request)
        
        # Retrieve the product associated with the vendor
        products = Product.objects.filter(vendor=vendor)      

        # Serialize each queryset
        products_serializer = ProductSerializer(products, many=True)
        

        # Combine all serialized data into a single response
        data = {
            "products": products_serializer.data,
        }

        return Response(data)
    
class ProductRelatedDataAPIView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get(self, request, *args, **kwargs):
        sub_categories = Sub_Category.objects.all()
        brands = Brand.objects.all()
        regions = Region.objects.all()
        categories = Category.objects.all()  # Assuming you have a Category model
        delivery_options = DeliveryOption.objects.all()

        # Serialize each queryset
        sub_category_serializer = SubCategorySerializer(sub_categories, many=True)
        brand_serializer = BrandSerializer(brands, many=True)
        region_serializer = RegionSerializer(regions, many=True)
        delivery_options_serializer = DeliveryOptionSerializer(delivery_options, many=True).data

        # Combine all serialized data into a single response
        data = {
            "sub_categories": sub_category_serializer.data,
            "brands": brand_serializer.data,
            "regions": region_serializer.data,
            "delivery_options": delivery_options_serializer,
        }

        return Response(data)

class VendorProductAPIView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get_vendor(self, request):
        """Retrieve the vendor associated with the current user, if exists."""
        return get_object_or_404(Vendor, user=request.user)
    
    def get(self, request, product_id, *args, **kwargs):
        vendor = self.get_vendor(request)
        
        # Retrieve the product associated with the vendor
        product = get_object_or_404(Product, id=product_id, vendor=vendor)
        
        # Retrieve related images and delivery options for the product
        images = ProductImages.objects.filter(product=product)
        delivery_options = ProductDeliveryOption.objects.filter(product=product)

        # Serialize product details
        product_serializer = ProductSerializer(product, context={"request": request})
        
        # Serialize images and delivery options separately
        images_serializer = ProductImagesSerializer(images, many=True)
        delivery_options_serializer = ProductDeliveryOptionSerializer(delivery_options, many=True)

        # Construct response data to include all serialized information
        response_data = {
            "product": product_serializer.data,
            "images": images_serializer.data,
            "delivery_options": delivery_options_serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        vendor = self.get_vendor(request)
        main_image = request.FILES.get('image')
        additional_images = request.FILES.getlist('images[]')
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            product = serializer.save(vendor=vendor)

            if main_image:
                product.image = main_image
                product.save()

            for image in additional_images:
                ProductImages.objects.create(product=product, images=image)
            
            # Handle delivery options
            delivery_options = request.data.getlist('delivery_options')
            for option_str in delivery_options:
                try:
                    option = json.loads(option_str)  # Parse each option from JSON string
                    delivery_option = DeliveryOption.objects.get(id=option['deliveryOptionId'])
                    ProductDeliveryOption.objects.create(
                        product=product,
                        delivery_option=delivery_option,
                        default=option.get('default', False)
                    )
                except (json.JSONDecodeError, KeyError, DeliveryOption.DoesNotExist) as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        print("Validation errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, product_id, *args, **kwargs):
        vendor = self.get_vendor(request)
        # Retrieve the product to be updated
        product = get_object_or_404(Product, id=product_id, vendor=vendor)

        # Extract images from the request
        main_image = request.FILES.get('image')
        additional_images = request.FILES.getlist('images[]')
        deleted_images = request.data.get('deletedImages', []) #this should be the ids of images deleted in the frontend

        print(deleted_images)

        if deleted_images:
            ProductImages.objects.filter(id__in=deleted_images, product=product).delete()

        # Initialize serializer with existing product instance and incoming data
        serializer = ProductSerializer(product, data=request.data, partial=True)

        if serializer.is_valid():
            # Update the product with new data
            product = serializer.save()

            # Update the main image if provided
            if main_image:
                product.image = main_image
                product.save()

            # Remove old additional images and save new ones
            if additional_images:
                ProductImages.objects.filter(product=product).delete()
                for image in additional_images:
                    ProductImages.objects.create(product=product, images=image)

            # Update delivery options
            delivery_options = request.data.getlist('delivery_options')
            print(delivery_options)
            if delivery_options:
                ProductDeliveryOption.objects.filter(product=product).delete()  # Clear existing options
                for option_str in delivery_options:
                    try:
                        option = json.loads(option_str)  # Parse each option from JSON string
                        delivery_option = DeliveryOption.objects.get(id=option['deliveryOptionId'])
                        ProductDeliveryOption.objects.create(
                            product=product,
                            delivery_option=delivery_option,
                            default=option.get('default', False)
                        )
                    except (json.JSONDecodeError, KeyError, DeliveryOption.DoesNotExist) as e:
                        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            print(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Log and return validation errors
        print("Validation errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id, *args, **kwargs):
        vendor = self.get_vendor(request)
        # Retrieve the product to be updated
        product = get_object_or_404(Product, id=product_id, vendor=vendor)

        # Optionally, you can add additional checks for the vendor to ensure they have the right to delete the product
        vendor = self.get_vendor(request)
        if product.vendor != vendor:
            return Response({"error": "You do not have permission to delete this product."}, status=status.HTTP_403_FORBIDDEN)
        
        # Delete related images (if any)
        product_images = ProductImages.objects.filter(product=product)
        product_images.delete()

        # Delete related delivery options (if any)
        ProductDeliveryOption.objects.filter(product=product).delete()

        # Delete the product itself
        product.delete()
        return Response({"message": "Product and related data successfully deleted."}, status=status.HTTP_204_NO_CONTENT)



def index(request):
    return HttpResponse('<h1>Hope you good?</h1>')

def vendor_list_view(request):
    vendors = Vendor.objects.all()
    context = {
        'vendors': vendors,
    }
    return render(request, "vendor-list.html", context)

@login_required
@user_passes_test(is_vendor)
def vendor_dashboard(request):
    vendor = get_object_or_404(Vendor, user=request.user)
    if not vendor.has_active_subscription():
        messages.error(request, "Your subscription is inactive. Please renew to continue.")
        return redirect('payments:subscribe')
    
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


@login_required
@user_passes_test(is_vendor)
def dashboard_products(request):
    vendor = get_object_or_404(Vendor, user=request.user)

    if not vendor.has_active_subscription():
        messages.error(request, "Your subscription is inactive. Please renew to continue.")
        return redirect('payments:subscribe')

    all_products = Product.objects.filter(vendor=vendor)
    all_categories = Category.objects.all()
    
    context = {
        "all_products": all_products,
        "all_categories": all_categories,
    }
    return render(request, "useradmin/dashboard-products.html", context)


# def vendor_detail(request, slug):
#     vendor = get_object_or_404(Vendor, slug=slug)
#     products = Product.objects.filter(vendor=vendor, status="published")
#     operating_hours = OpeningHour.objects.filter(vendor=vendor).order_by('day', '-from_hour')
#     today_date = date.today()
#     today = today_date.isoweekday()
#     today_operating_hours = OpeningHour.objects.filter(vendor=vendor, day=today)
#     context = {
#         "vendor":vendor,
#         "products":products,
#         'operating_hours': operating_hours,
#         'today_operating_hours': today_operating_hours,
#     }
#     return render(request, "vendor_detail.html", context)


def vendor_review(request, slug):
    vendor = Vendor.objects.get(slug=slug)
    products = Product.objects.filter(vendor=vendor, status='published')
    review = ProductReview.objects.all()
    context = {
        'products':products,
        'review':review,
    }
    return render(request, 'review.html', context)


@login_required
@user_passes_test(is_vendor)
def vendor_profile(request):
    about = get_object_or_404(About, user=request.user)
    vendor = get_object_or_404(Vendor, user=request.user)
    if request.method == 'POST':
        about_form = AboutForm(request.POST, request.FILES, instance=about)
        vendor_form = VendorForm(request.POST, request.FILES, instance=vendor)
        if about_form.is_valid() and vendor_form.is_valid():
            about_form.save()
            vendor_form.save()
            messages.success(request, 'Profile updated')
            return redirect('vendor:vendor_profile')
        messages.error(request, 'Something went wrong')
        print('Masa you dey fool too much')
        return redirect('vendor:vendor_profile')
    else:
        about_form = AboutForm(instance=about)
        vendor_form = VendorForm(instance=vendor)
            
    context = {
        'about': about,
        'vendor': vendor,
        'about_form': about_form,
        'vendor_form': vendor_form,
    }
    return render(request, 'vendor_profile.html', context)


@login_required()
@user_passes_test(is_vendor)
def operating_hours(request):
    operating_hours_ = OpeningHour.objects.filter(vendor=get_vendor(request))
    form = OpeningHourForm()
    context = {
        'form': form,
        'operating_hours': operating_hours_,
    }
    return render(request, 'operating-hours.html', context)



@login_required()
@user_passes_test(is_vendor)
def vendor_product(request):
    vendor = get_object_or_404(Vendor, user=request.user)
    products = Product.objects.filter(vendor=vendor)
    context = {
        "vendor":vendor,
        "products":products,
    }
    return render(request, "vendor_product.html", context)

@login_required
@user_passes_test(is_vendor)
def add_product(request):
    if request.method == "POST":
        form = AddProductForm(request.POST, request.FILES)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = request.user
            new_form.save()
            form.save_m2m()
            messages.success(request, 'Product added successfully')
            return redirect("vendor:vendor_product")
    else:
        form = AddProductForm()
    context = {
        'form':form
    }
    return render(request, "add_product.html", context)

@login_required()
@user_passes_test(is_vendor)
def add_operating_hours(request):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'POST':
            day = request.POST.get('day')
            from_hour = request.POST.get('from_hour')
            to_hour = request.POST.get('to_hour')
            is_closed = request.POST.get('is_closed')
            try:
                hour = OpeningHour.objects.create(
                    vendor=get_vendor(request),
                    day=day,
                    from_hour=from_hour,
                    to_hour=to_hour,
                    is_closed=is_closed,
                )
                if hour:
                    day = OpeningHour.objects.get(id=hour.id)
                    if day.is_closed:
                        response = {
                            'status': 'Success',
                            'id': hour.id,
                            'day': day.get_day_display(),
                            'is_closed': 'Closed',
                        }
                    else:
                        response = {
                            'status': 'Success',
                            'id': hour.id,
                            'day': day.get_day_display(),
                            'from_hour': hour.from_hour,
                            'to_hour': hour.to_hour,
                        }
                return JsonResponse(response)
            except IntegrityError:
                response = {
                    'status': 'Failed',
                    'message': f'{from_hour} - {to_hour} already exists'
                }
                return JsonResponse(response)
        else:
            response = {
                    'status': 'Failed',
                    'message': 'Invalid request'
                }
            return JsonResponse(response)


@login_required()
@user_passes_test(is_vendor)
def remove_operating_hours(request, pk=None):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            hour = get_object_or_404(OpeningHour, pk=pk)
            hour.delete()
            return JsonResponse({
                'status': 'Success',
                'id': pk,
            })
#############################################################
#################### VENDOR #################################


@login_required
@user_passes_test(lambda u: hasattr(u, 'vendor'))
def add_product(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES)
        product_images_form = ProductImagesForm(request.POST, request.FILES)
        variants_form = VariantsForm(request.POST, request.FILES)
        variant_images_form = VariantImageForm(request.POST, request.FILES)
        
        if product_form.is_valid() and product_images_form.is_valid() and variants_form.is_valid() and variant_images_form.is_valid():
            product = product_form.save(commit=False)
            product.vendor = request.user.vendor  # Assuming vendor is linked to the user
            product.save()

            product_image = product_images_form.save(commit=False)
            product_image.product = product
            product_image.save()

            variant = variants_form.save(commit=False)
            variant.product = product
            variant.save()

            variant_image = variant_images_form.save(commit=False)
            variant_image.variant = variant
            variant_image.save()

            return redirect('vendor:vendor_product')  # Redirect to a page that shows the list of products

    else:
        product_form = ProductForm()
        product_images_form = ProductImagesForm()
        variants_form = VariantsForm()
        variant_images_form = VariantImageForm()

    return render(request, 'add_product.html', {
        'product_form': product_form,
        'product_images_form': product_images_form,
        'variants_form': variants_form,
        'variant_images_form': variant_images_form,
    })

@login_required
@user_passes_test(lambda u: hasattr(u, 'vendor'))
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user.vendor)
    product_images = ProductImages.objects.filter(product=product)
    variants = Variants.objects.filter(product=product)
    variant_images = VariantImage.objects.filter(variant__product=product)

    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES, instance=product)
        product_images_form = ProductImagesForm(request.POST, request.FILES)
        variants_form = VariantsForm(request.POST, request.FILES)
        variant_images_form = VariantImageForm(request.POST, request.FILES)
        
        if product_form.is_valid() and product_images_form.is_valid() and variants_form.is_valid() and variant_images_form.is_valid():
            product_form.save()

            # Save or update product images
            for image_form in product_images_form:
                if image_form.is_valid():
                    product_image = image_form.save(commit=False)
                    product_image.product = product
                    product_image.save()

            # Save or update variants
            for variant_form in variants_form:
                if variant_form.is_valid():
                    variant = variant_form.save(commit=False)
                    variant.product = product
                    variant.save()

            # Save or update variant images
            for variant_image_form in variant_images_form:
                if variant_image_form.is_valid():
                    variant_image = variant_image_form.save(commit=False)
                    variant_image.variant = variant
                    variant_image.save()

            return redirect('product_list')  # Redirect to a page that shows the list of products

    else:
        product_form = ProductForm(instance=product)
        product_images_form = ProductImagesForm()
        variants_form = VariantsForm()
        variant_images_form = VariantImageForm()

    return render(request, 'edit_product.html', {
        'product_form': product_form,
        'product_images_form': product_images_form,
        'variants_form': variants_form,
        'variant_images_form': variant_images_form,
        'product_images': product_images,
        'variants': variants,
        'variant_images': variant_images,
    })