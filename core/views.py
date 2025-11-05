from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import *
from order.models import *
from .serializers import *
from django.db.models import Avg, Count
from datetime import datetime, timedelta
from django.contrib.auth import authenticate, login, logout
from django.db.models.query_utils import Q
from django.contrib import messages, auth
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics
from django.db import transaction
from .services import verify_payment
import random
from decimal import Decimal
from rest_framework.pagination import PageNumberPagination
import json
from django.db.models import Sum

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.utils import timezone
from rest_framework.permissions import AllowAny
from django.urls import reverse
from .serializers import UserRegistrationSerializer, UserSerializer
from userauths.tokens import otp_token_generator
from userauths.utils import send_sms
from userauths.models import Profile, User
from order.service import *

# User = get_user_model()
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({"message": "This is a protected route"}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_data(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)


class MainAPIView(APIView):
    """
    API View to retrieve products, sliders, banners, and subcategories data
    """

    def get(self, request, *args, **kwargs):
        # Get latest products with average ratings
        new_products = Product.objects.filter(status='published', product_type="new").annotate(average_rating=Avg('reviews__rating'), review_count=Count('reviews')).order_by('-date')[:9]
        most_popular = Product.objects.filter(status='published').annotate(average_rating=Avg('reviews__rating'), review_count=Count('reviews')).order_by('-views')[:8]

        category = Category.objects.all()
        category_data = CategorySerializer(category, many=True, context={'request': request}).data


        specific_category = Category.objects.filter().first()
        # Get and serialize subcategory data
        sub_cat = Sub_Category.objects.filter(category=specific_category)[0:4]
        sub_data = SubCategorySerializer(sub_cat, many=True, context={'request': request}).data
        
        
        # Serialize new products with ratings
        products_with_details = []
        for product in new_products: 
            # Serialize product data
            product_data = {
                'product': ProductSerializer(product, context={'request': request}).data,  # Serialize the product instance
                'average_rating': product.average_rating or 0,
                'review_count': product.review_count or 0,
                # 'variants': VariantSerializer(product_variants, many=True).data,
                # 'colors': list(product_colors),  # ensure list is serialized correctly
            }
            products_with_details.append(product_data)

        # Get and serialize slider data
        sliders = Slider.objects.all()
        slider_data = SliderSerializer(sliders, many=True, context={'request': request}).data

        # Get and serialize banner data
        banners = Banners.objects.all()
        banner_data = BannersSerializer(banners, many=True, context={'request': request}).data

        # Get and serialize subcategory data
        subcategories = Sub_Category.objects.all()
        subcategory_data = SubCategorySerializer(subcategories, many=True, context={'request': request}).data
        
        context = {
            "new_products": products_with_details,
            "most_popular": ProductSerializer(most_popular, many=True, context={'request': request}).data,
            "sliders": slider_data,
            "banners": banner_data,
            "sub_data": sub_data,
            "main": CategorySerializer(specific_category, context={'request': request}).data,
            "subcategories": subcategory_data,
            "category_data": category_data,
        }

        return Response(context, status=status.HTTP_200_OK)



class CheckEmailPhoneView(APIView):
    def post(self, request):
        email_or_phone = request.data.get('email')
        
        user = User.objects.filter(email=email_or_phone).first() or User.objects.filter(phone=email_or_phone).first()
        if user:
            return Response({"message": "User exists"}, status=status.HTTP_200_OK)
        return Response({"error": "No account found with this email."}, status=status.HTTP_404_NOT_FOUND)


class IncrementViewCount(APIView):
    """
    Increment the view count of a product if it has not been viewed by the browser before.
    """

    def post(self, request, slug):
        try:
            # Get the product using the slug
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get the list of viewed product IDs from the request data
        viewed_product_ids = request.data.get('viewedProductIds', [])

        # Check if the product ID is already in the viewed product IDs
        if product.id not in viewed_product_ids:
            product.views += 1  # Increment the view count
            product.save()  # Save the updated product
            return JsonResponse({'message': 'View count incremented'}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({'message': 'View already counted'}, status=status.HTTP_200_OK)

class AddProductReviewView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def post(self, request, *args, **kwargs):
        serializer = ProductReviewSerializer(data=request.data, context={'request': request})

        # Extract the product ID from the request data
        product_id = request.data.get('product')

        # Check if the user has purchased the product
        if not self.user_has_purchased_product(request.user, product_id):
            return Response(
                {'detail': 'You must purchase the product before reviewing it.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if serializer.is_valid():
            serializer.save()  # Save the review with the user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def user_has_purchased_product(self, user, product_id):
        # Check if there's an order for the user that contains the specific product
        return OrderProduct.objects.filter(
            order__user=user,
            product_id=product_id, 
            order__is_ordered=True,  # Ensure the order is marked as completed
            order__status="delivered",  # Ensure the order is marked as completed
        ).exists()


class ViewedProductsView(APIView):

    def post(self, request):
        # Retrieve existing viewed products from cookies
        viewed_products = request.COOKIES.get('viewed_product', '[]')
        viewed_products = json.loads(viewed_products)

        # Get the new viewed products from the request
        new_viewed_products = request.data.get('viewed_products', [])

        # Add new products to the list, ensuring no duplicates
        for new_product in new_viewed_products:
            # Check for existing product in the list
            if not any(vp['id'] == new_product['id'] for vp in viewed_products):
                viewed_products.append(new_product)

        # Limit to the last 10 viewed products
        if len(viewed_products) > 10:
            viewed_products = viewed_products[-10:]

        # Set the cookie with the updated viewed products
        response = Response({'status': 'success'}, status=status.HTTP_200_OK)
        response.set_cookie('viewed_product', json.dumps(viewed_products), max_age=365*24*60*60, httponly=False)  # 1 year
        return response

    def get(self, request):
        # Retrieve recently viewed product IDs from the session
        product_ids = request.session.get('recently_viewed', [])
        
        if not product_ids:
            return Response({'recently_viewed': []}, status=status.HTTP_200_OK)
        
        # Query the Product model for these IDs and filter for published products
        products = Product.objects.filter(id__in=product_ids, status='published')
        
        # Create a dictionary to map product IDs to their instances for quick lookup
        products_dict = {product.id: product for product in products}
        
        # Maintain the order of the products based on the session history
        sorted_products = [products_dict[pid] for pid in product_ids if pid in products_dict]
        
        # Serialize the sorted products
        serialized_products = ProductSerializer(sorted_products, many=True, context={'request': request}).data
        
        return Response({'recently_viewed': serialized_products}, status=status.HTTP_200_OK)
    
class SearchedProducts(APIView):
    def post(self, request):
        # Retrieve existing search history from cookies
        search_history = request.COOKIES.get('search_history', '[]')
        search_history = json.loads(search_history)

        # Get the new search queries from the request
        new_searched_queries = request.data.get('search_history', [])

        # Process each query in new_searched_queries
        for query in new_searched_queries:
            # If query already exists, remove it to prevent duplicates
            if query in search_history:
                search_history.remove(query)
            # Insert query at the beginning of the list (most recent first)
            search_history.insert(0, query)

        # Limit search history to the last 10 queries
        if len(search_history) > 10:
            search_history = search_history[:10]

        # Set the updated search history back in cookies
        response = Response({'status': 'success'}, status=status.HTTP_200_OK)
        response.set_cookie('search_history', json.dumps(search_history), max_age=365*24*60*60, httponly=False)  # 1 year
        return response


class RecommendedProducts(APIView):

    def get(self, request):
        # 1. Retrieve and Sort Recently Viewed Products
        viewed_product_ids = request.session.get('recently_viewed', [])
        
        # Query Product model for viewed product IDs
        products = Product.objects.filter(id__in=viewed_product_ids, status='published')
        
        # Map product IDs to maintain viewed order
        products_dict = {product.id: product for product in products}
        sorted_viewed_products = [products_dict[pid] for pid in viewed_product_ids if pid in products_dict]

        # 2. Retrieve Related Products Based on Category
        related_products = set()
        for product in products:
            related_products.update(Product.objects.filter(
                status='published',
                sub_category=product.sub_category
            ).exclude(id=product.id))

        # 3. Retrieve Related Products Based on Search History
        search_history = json.loads(request.COOKIES.get('search_history', '[]'))
        search_related_products = set()
        for query in search_history:
            search_related_products.update(
                Product.objects.filter(status="published", title__icontains=query)
                .distinct().exclude(id__in=viewed_product_ids)
            )
            search_related_products.update(
                Product.objects.filter(status="published", description__icontains=query)
                .distinct().exclude(id__in=viewed_product_ids)
            )

        # Combine category-related and search-related products, then shuffle
        all_related_products = list(related_products | search_related_products)
        random.shuffle(all_related_products)

        # Limit to 10 recommended products
        recommending_products = all_related_products[:10]

        # Serialize recommended products and viewed products
        serialized_viewed_products = ProductSerializer(sorted_viewed_products, many=True, context={'request': request}).data
        serialized_recommended_products = ProductSerializer(recommending_products, many=True, context={'request': request}).data

        return Response({
            'recently_viewed': serialized_viewed_products,
            'recommended_products': serialized_recommended_products
        })

#########################################VENDOR
class VendorProductPagination(PageNumberPagination):
    page_size = 10  # Number of items per page

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
        vendor_serializer = VendorSerializer(vendor, context={'request': request})
        
        # Serialize the products
        product_serializer = ProductSerializer(products, many=True, context={'request': request})

        reviews = ProductReview.objects.filter(product__in=products, status=True).order_by("-date")
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg']

        products_with_details = []
        for product in products:
            product_variants = Variants.objects.filter(product=product)
            product_colors = product_variants.values('color__name', 'color__code', 'sku').distinct()

            product_data = {
                'product': ProductSerializer(product, context={'request': request}).data,  # Serialize the product instance
                'average_rating': product.average_rating or 0,
                'review_count': product.review_count or 0,
                'variants': VariantSerializer(product_variants, many=True).data,
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
            "reviews": ProductReviewSerializer(reviews, many=True, context={'request': request}).data,
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
#########################################VENDOR  

class UpdateProductView(APIView):
    def post(self, request, product_id):
        session_key = f"viewed_{product_id}"
        if not request.session.get(session_key):
            try:
                product = Product.objects.get(id=product_id)
                product.views += 1
                product.save()
                request.session[session_key] = True
                return Response({"message": "View count updated", "views": product.views}, status=status.HTTP_200_OK)
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "View already recorded"}, status=status.HTTP_200_OK)
    
def get_or_create_cart(user, request):
    if user.is_authenticated:
        # For authenticated users, retrieve or create their cart
        cart, created = Cart.objects.get_or_create(user=user)
    else:
        # For guest users, check for a cart in the session
        session_cart_id = request.session.get('cart_id')

        if session_cart_id:
            # If a cart exists in session, retrieve it
            cart = Cart.objects.get(id=session_cart_id)
        else:
            # Create a new cart for guest users and store its ID in the session
            cart = Cart.objects.create(user=None)
            request.session['cart_id'] = cart.id  # Store cart ID in session

    return cart

from rest_framework.exceptions import NotFound, ValidationError

class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity', 1))

        # Validate product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise NotFound(detail="Product not found.")

        # If variant_id is provided, validate the variant
        variant = None
        if variant_id:
            try:
                variant = Variants.objects.get(id=variant_id, product=product)
            except Variants.DoesNotExist:
                raise ValidationError(detail="Variant not found or does not belong to the specified product.")

        # Retrieve or create the user's cart
        cart = Cart.objects.filter(user=user).first()
        if not cart:
            cart = Cart.objects.create(user=user)

        # Get the default delivery option for the product
        default_delivery_option = ProductDeliveryOption.objects.filter(
            product=product, default=True
        ).first()

        # Add the product (with or without a variant) to the cart with the default delivery option
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant if variant else None,
            defaults={
                'quantity': quantity,
                'delivery_option': default_delivery_option.delivery_option if default_delivery_option else None
            }
        )
        if not created:
            # If the item already exists, increase the quantity
            cart_item.quantity += quantity
            cart_item.save()

        return Response({"message": "Item added to cart successfully."})




class RemoveFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')

        # Retrieve the user's cart
        cart = get_or_create_cart(user, request)
            
        # Get the total quantity of items in the cart
        total_quantity = cart.cart_items.aggregate(total=models.Sum('quantity'))['total'] or 0

        # Check if the item exists in the cart
        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id, variant_id=variant_id)
            cart_item.delete()  # Remove the item from the cart
            return Response({
                "message": "Item removed from cart",
                "total_quantity": total_quantity
                }, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND)


class CheckCartView(APIView):
    """
    View to check if a product (and variant, if applicable) exists in the user's cart.
    """
    def get(self, request):
        product_id = request.query_params.get('product_id')
        variant_id = request.query_params.get('variant_id')

        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Get or create the user's cart (assuming there's a method for it)
            cart = get_or_create_cart(request.user, request)

            # Sum the total quantity of all items in the cart
            total_quantity = cart.total_items

            # Retrieve the product
            product = get_object_or_404(Product, id=product_id)

            # Check if variant handling is required
            if variant_id:
                cart_item = CartItem.objects.filter(cart=cart, product_id=product_id, variant_id=variant_id).first()
            else:
                cart_item = CartItem.objects.filter(cart=cart, product=product).first()

            if cart_item:
                return Response({
                    "inCart": True,
                    "quantity": cart_item.quantity,
                    "total_quantity": total_quantity,
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "inCart": False,
                    "quantity": 0,
                    "total_quantity": total_quantity,
                }, status=status.HTTP_200_OK)

        # If the user is not authenticated, respond with an error
        return Response({"error": "User is not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

class SyncCartView(APIView):
    """
    Sync cart items from localStorage to the server-side cart after user login.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Ensure the user is authenticated
        if not user.is_authenticated:
            return Response({"error": "User must be authenticated to sync cart"}, status=status.HTTP_401_UNAUTHORIZED)


        cart_data = request.data.get('cart', [])
    
        cart = get_or_create_cart(user, request)

        # Sync each item from the localStorage cart to the server-side cart
        for item in cart_data:
            product_id = item.get('productId')
            variant_id = item.get('variantId')
            quantity = item.get('quantity')

            # Fetch the product and variant (if applicable)
            try:
                product = Product.objects.get(id=product_id)
                variant = Variants.objects.get(id=variant_id) if variant_id else None
            except Product.DoesNotExist:
                continue  # Skip invalid products
            except Variants.DoesNotExist:
                continue  # Skip invalid variants

            default_delivery_option = ProductDeliveryOption.objects.filter(
                product=product, default=True
            ).first()

            # Check if the item already exists in the user's cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                variant=variant,
                defaults={
                'quantity': quantity,
                'delivery_option': default_delivery_option.delivery_option if default_delivery_option else None}
            )

            if not created:
                # If the item already exists, update the quantity
                cart_item.quantity += quantity
                cart_item.save()
            total_quantity = cart.cart_items.aggregate(total=models.Sum('quantity'))['total'] or 0
            

        return Response({
            "message": "Cart synced successfully",
            "total_quantity": total_quantity
            }, status=status.HTTP_200_OK)

class CartItemCountView(APIView):
    """
    View to get the total quantity of items in the cart.
    Only works for authenticated users.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_authenticated:
            # Get the user's cart
            cart = get_or_create_cart(request.user, request)
            
            # Get the total quantity of items in the cart
            total_quantity = cart.total_quantity

            total_amount = cart.total_price
            packaging_fees = cart.calculate_packaging_fees()

            user_profile = Profile.objects.get(user=request.user)  # Fetch user profile
            total_delivery_fee = cart.calculate_total_delivery_fee(user_profile)
            grand_total = cart.calculate_grand_total(user_profile)

            return Response({
                "total_quantity": total_quantity,
                "total_amount": float(total_amount),  # Convert to float for JSON serialization
                "packaging_fees": float(packaging_fees),  # Convert to float for JSON serialization
                "total_delivery_fee": float(total_delivery_fee),  # Convert to float for JSON serialization
                "grand_total": float(grand_total),  # Convert to float for JSON serialization
            }, status=status.HTTP_200_OK)

        # If the user is not authenticated, return an error
        return Response({"error": "User is not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    
class UserProgressCheck(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Check if user has a default address
        has_default_address = Address.objects.filter(user=user, status=True).exists()

        # Check if user has a saved payment method
        # has_payment_method = PaymentMethod.objects.filter(user=user).exists()

        return Response({
            "has_default_address": has_default_address,
            # "has_payment_method": has_payment_method,
        }) 

class CartItemsView(APIView):

    def get(self, request):
        try:
            # Check if the user is authenticated
            if request.user.is_authenticated:
                # Fetch the cart for the authenticated user
                cart = get_or_create_cart(request.user, request)
                
                if not cart:
                    return Response({"error": "No cart found for this user"}, status=status.HTTP_404_NOT_FOUND)
                
                # Fetch the cart items from the database
                cart_items = CartItem.objects.filter(cart=cart)

                # Serialize the cart items
                cart_data = []
                total_amount = 0
                total_packaging_fee = 0

                
                for item in cart_items:
                    product_data = ProductSerializer(item.product, context={'request': request}).data
                    variant_data = VariantSerializer(item.variant).data if item.variant else None
                    item_total = item.quantity * item.price
                    total_amount += item_total

                    packaging_fee = calculate_packaging_fee(item.product.weight, item.product.volume)* item.quantity
                    total_packaging_fee += packaging_fee
                    
                    cart_data.append({
                        'product': product_data,
                        'variant': variant_data,
                        'quantity': item.quantity,
                        'item_total': item_total
                    })

                # Return the response with cart data and total amount
                return Response({
                    "cart_items": cart_data,
                    "total_amount": total_amount,
                    "total_packaging_fee": total_packaging_fee,
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({"error": "User not authenticated"}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        try:
            # Process cart from request body (for guests or unauthenticated users)
            cart_items = request.data

            if not cart_items:
                return Response({"error": "No cart items provided"}, status=status.HTTP_400_BAD_REQUEST)

            product_ids = [item['product_id'] for item in cart_items]
            variant_ids = [item['variant_id'] for item in cart_items if item.get('variant_id')]

            # Fetch products and variants based on the provided IDs
            products = Product.objects.filter(id__in=product_ids)
            variants = Variants.objects.filter(id__in=variant_ids) if variant_ids else []

            # Serialize the products and variants
            product_serializer = ProductSerializer(products, many=True, context={'request': request})
            variant_serializer = VariantSerializer(variants, many=True)

            # Initialize total amount and packaging fee
            total_amount = 0
            total_packaging_fee = 0

            # Format the cart items with quantity for the response
            cart_data = []
            for item in cart_items:
                product_data = next((p for p in product_serializer.data if p['id'] == item['product_id']), None)
                variant_data = next((v for v in variant_serializer.data if v['id'] == item.get('variant_id')), None)

                # Determine the price (use variant price if variant exists, otherwise product price)
                if variant_data:
                    price = variant_data.get('price', 0)
                else:
                    price = product_data.get('price', 0)

                # Calculate the total price for the current item
                item_total = price * item['quantity']
                total_amount += item_total

                # Calculate packaging fee
                product_instance = Product.objects.get(id=item['product_id'])
                packaging_fee = calculate_packaging_fee(product_instance.weight, product_instance.volume) * item['quantity']
                total_packaging_fee += packaging_fee

                cart_data.append({
                    'product': product_data,
                    'variant': variant_data,
                    'quantity': item['quantity'],
                    'item_total': item_total
                })

            # Return serialized data along with quantities
            return Response({
                "cart_items": cart_data,
                "total_amount": total_amount,
                "total_packaging_fee": total_packaging_fee
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        current_user = request.user
        user_profile = get_object_or_404(Profile, user=current_user)
        cart = get_or_create_cart(request.user, request)
                
        if not cart:
            return Response({"error": "No cart found for this user"}, status=status.HTTP_404_NOT_FOUND)

        cart_items = CartItem.objects.filter(cart=cart)

        if not cart_items.exists():
            return Response({"detail": "There are no items to checkout."}, status=status.HTTP_400_BAD_REQUEST)

        total_delivery_fee = 0
        delivery_date_ranges = {}
        vendor_delivery_fees = {}
        sub_total = cart.total_price

        # Structure to hold delivery options for each product
        all_product_delivery_options = {}

        for item in cart_items:
            product = item.product
            vendor = product.vendor

            # Fetch all delivery options for the product
            delivery_options = ProductDeliveryOption.objects.filter(product=product)

            if not delivery_options.exists():
                return Response({"detail": f"No delivery options found for product {product.title}"}, status=status.HTTP_400_BAD_REQUEST)

            all_product_delivery_options[product.id] = ProductDeliveryOptionSerializer(delivery_options, many=True).data

            # Calculate delivery fee and date range
            default_delivery_option = delivery_options.filter(default=True).first()
            if default_delivery_option:
                delivery_fee = calculate_delivery_fee(
                    vendor.about.latitude, vendor.about.longitude,
                    user_profile.latitude, user_profile.longitude,
                    default_delivery_option.delivery_option.cost
                )
                total_delivery_fee += Decimal(delivery_fee)

                # Calculate delivery date range
                min_delivery_date = timezone.now() + timezone.timedelta(days=default_delivery_option.delivery_option.min_days)
                max_delivery_date = timezone.now() + timezone.timedelta(days=default_delivery_option.delivery_option.max_days)
                delivery_date_ranges[product.id] = f"{min_delivery_date.strftime('%d %B')} to {max_delivery_date.strftime('%d %B')}"
            else:
                return Response({"detail": f"No default delivery options found for product {product.title}"}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate total price of items in the cart

        grand_total = cart.calculate_grand_total(user_profile)

        # Coupon handling
        clipped_coupons = ClippedCoupon.objects.filter(user=current_user)
        applied_coupon = None
        discount_amount = Decimal(0)

        if 'applied_coupon' in request.session:
            try:
                coupon = Coupon.objects.get(id=request.session['applied_coupon'])
                if coupon.is_valid() and clipped_coupons.filter(coupon=coupon).exists():
                    applied_coupon = coupon
                    discount_amount = coupon.discount_amount or (grand_total * Decimal(coupon.discount_percentage / 100)).quantize(Decimal('0.01'))
                    grand_total -= discount_amount
            except Coupon.DoesNotExist:
                del request.session['applied_coupon']

        # Prepare the response data
        data = {
            'cart_items': CartItemSerializer(cart_items, many=True).data,
            'sub_total': sub_total,
            'total_delivery_fee': cart.calculate_total_delivery_fee(user_profile),
            'product_delivery_options': all_product_delivery_options,  # Each product's delivery options
            'total_packaging_fee': cart.calculate_packaging_fees(),
            'grand_total': cart.calculate_grand_total(user_profile),
            'delivery_date_ranges': delivery_date_ranges,
            'clipped_coupons': CouponSerializer(clipped_coupons, many=True).data,
            'applied_coupon': CouponSerializer(applied_coupon).data if applied_coupon else None,
            'discount_amount': discount_amount,
        }

        return Response(data, status=status.HTTP_200_OK)



class UpdateDeliveryOptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Parse data from the request
            product_id = request.data.get('product_id')
            delivery_option_id = request.data.get('delivery_option_id')

            # Validate inputs
            if not product_id or not delivery_option_id:
                return Response(
                    {"error": "Product ID and Delivery Option ID are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Retrieve or create the cart for the user
            cart = get_or_create_cart(request.user, request)

            if not cart:
                return Response(
                    {"error": "No cart found for this user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Retrieve all cart items for the product ID within the user's cart
            cart_items = CartItem.objects.filter(cart=cart, product__id=product_id)

            if not cart_items.exists():
                return Response(
                    {"error": "No items found in the cart for the specified product."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Validate the delivery option
            delivery_option = get_object_or_404(DeliveryOption, id=delivery_option_id)

            # Update the delivery option for all matching cart items
            cart_items.update(delivery_option=delivery_option)

            return Response(
                {
                    "message": "Delivery option updated successfully for all matching items.",
                },
                status=status.HTTP_200_OK,
            )

        except DeliveryOption.DoesNotExist:
            return Response(
                {"error": "Selected delivery option does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from django.core.cache import cache  # Import Django's cache framework

#############################CUSTOMER DASHBOARD############################
class AddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    # List all addresses for the authenticated user or create a new one
    def get(self, request):
        addresses = Address.objects.filter(user=request.user).order_by('-status')
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]
    # Retrieve, update, or delete an address
    def get_object(self, pk):
        try:
            return Address.objects.get(pk=pk, user=self.request.user)
        except Address.DoesNotExist:
            raise KeyError

    def get(self, request, pk):
        address = self.get_object(pk)
        serializer = AddressSerializer(address)
        return Response(serializer.data)

    def put(self, request, pk):
        address = self.get_object(pk)
        serializer = AddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        address = self.get_object(pk)
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MakeDefaultAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        # Get the address ID from the request data
        address_id = request.data.get('id')

        if not address_id:
            return Response({"error": "Address ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Set all addresses for the current user to not be default
            Address.objects.filter(user=request.user).update(status=False)

            # Set the selected address as the default
            Address.objects.filter(id=address_id, user=request.user).update(status=True)

            new = Address.objects.filter(status=True, user=request.user).first()

            profile = Profile.objects.select_related('user').get(user=request.user)
            profile.address = new.address
            profile.country = new.country
            profile.mobile = new.mobile
            profile.latitude = new.latitude
            profile.longitude = new.longitude
            profile.save()

            return Response({"success": True, "message": "Address set as default"}, status=status.HTTP_200_OK)

        except Address.DoesNotExist:
            return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def get(self, request):
        try:
            # Fetch the default address for the authenticated user
            default_address = Address.objects.filter(user=request.user, status=True).first()

            if default_address:
                # Use the serializer to return the default address
                serializer = AddressSerializer(default_address)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "No default address found"}, status=status.HTTP_404_NOT_FOUND)

        except Address.DoesNotExist:
            return Response({"error": "Error retrieving default address"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#############################CUSTOMER DASHBOARD############################


################################CATEGORY#########################################
from django.db.models import Q, Avg, Max, Min
# from rest_framework.response import Response
# from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

class SubcategoryListView(APIView):

    def get(self, request, slug, category):
        # Get the main category
        category_obj = get_object_or_404(Category, slug=slug, main_category__slug=category)
        
        # Serialize the main category data
        category_data = CategorySerializer(category_obj).data
        
        # Get other categories, excluding the main one
        other_categories = Category.objects.exclude(slug=slug)
        other_categories_data = CategorySerializer(other_categories, many=True).data
        
        # Get subcategories related to the main category
        subcategories = Sub_Category.objects.filter(category=category_obj)
        subcategories_data = SubCategorySerializer(subcategories, many=True).data

        # Construct the response
        data = {
            "category": category_data,
            "other_categories": other_categories_data,
            "sub_category": subcategories_data,
        }
        
        return Response(data, status=status.HTTP_200_OK)


class CategoryListView(APIView):
    
    def get(self, request, slug):
        # Fetch the main category based on the provided slug
        category = get_object_or_404(Main_Category, slug=slug)
        
        # Fetch other main categories, excluding the current one
        other_categories = Main_Category.objects.exclude(slug=slug)
        
        # Fetch sub-categories associated with the main category
        sub_categories = Category.objects.filter(main_category=category)
        
        # Serialize the data
        category_data = MainCategorySerializer(category).data
        other_categories_data = MainCategorySerializer(other_categories, many=True).data
        sub_categories_data = CategorySerializer(sub_categories, many=True).data
        
        # Return the data in the response
        return Response({
            "category": category_data,
            "other_categories": other_categories_data,
            "sub_category": sub_categories_data,
        }, status=status.HTTP_200_OK)

class CategoryProductListView(APIView):
    def get(self, request, slug):
        # Fetch the category by slug
        category = Sub_Category.objects.filter(slug=slug).first()
        if not category:
            return Response({"detail": "Category not found"}, status=404)
        
        # Initial product query (only published products under the specific category)
        products = Product.objects.filter(status="published", sub_category=category).annotate(
            average_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )

        max_price = products.aggregate(Max('price'))['price__max']
        min_price = products.aggregate(Min('price'))['price__min']

        # Filter options from query parameters
        active_colors = [int(color_id) for color_id in request.GET.getlist('color')]
        active_sizes = [int(size_id) for size_id in request.GET.getlist('size')]
        active_brands = [int(brand_id) for brand_id in request.GET.getlist('brand')]
        active_vendors = [int(vendor_id) for vendor_id in request.GET.getlist('vendor')]
        rating = [int(rating_id) for rating_id in request.GET.getlist('rating')]
        min_price = request.GET.get('from')
        max_price = request.GET.get('to')

        # Initialize filters
        if active_colors or active_sizes or active_vendors or active_brands or min_price or max_price or rating:
            filters = Q()
            if active_colors:
                filters &= Q(variants__color__id__in=active_colors)
            if active_sizes:
                filters &= Q(variants__size__id__in=active_sizes)
            if active_vendors:
                filters &= Q(vendor__id__in=active_vendors)
            if active_brands:
                filters &= Q(brand__id__in=active_brands)
            if min_price:
                filters &= Q(price__gte=min_price)
            if max_price:
                filters &= Q(price__lte=max_price)
            if rating:
                filters &= Q(average_rating__gte=int(rating))

            # Apply the filters and distinct to avoid duplicate results
            products = products.filter(filters).distinct().annotate(average_rating=Avg('reviews__rating'), review_count=Count('reviews'))

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 12
        paged_products = paginator.paginate_queryset(products, request)

        # Serialize paginated products
        serialized_products = ProductSerializer(paged_products, many=True, context={'request': request}).data

        # Additional product details with variants and colors
        products_with_details = []
        for product in paged_products:
            product_variants = Variants.objects.filter(product=product)
            product_colors = product_variants.values('color__name', 'color__code', 'sku').distinct()

            product_data = {
                'product': ProductSerializer(product, context={'request': request}).data,  # Serialize the product instance
                'average_rating': product.average_rating or 0,
                'review_count': product.review_count or 0,
                'variants': VariantSerializer(product_variants, many=True).data,
                'colors': list(product_colors),  # ensure list is serialized correctly
            }
            products_with_details.append(product_data)

        # Get distinct filter options for sidebar
        sizes = Size.objects.filter(variants__product__sub_category=category).distinct()
        colors = Color.objects.filter(variants__product__sub_category=category).distinct()
        brands = Brand.objects.filter(product__sub_category=category).distinct()
        vendors = Vendor.objects.filter(product__sub_category=category).distinct()

        max_price = products.aggregate(Max('price'))['price__max']
        min_price = products.aggregate(Min('price'))['price__min']

        # Prepare context with all the necessary information for the frontend
        context = {
            "colors": ColorSerializer(colors, many=True).data,
            "sizes": SizeSerializer(sizes, many=True).data,
            "vendors": VendorSerializer(vendors, many=True).data,
            "brands": BrandSerializer(brands, many=True).data,
            "category": SubCategorySerializer(category).data, 
            "products": serialized_products,
            "products_with_details": products_with_details,
            "max_price": max_price,
            "min_price": min_price,
        }
        return Response(context)
    
class BrandProductListView(APIView):
    def get(self, request, slug):
        # Fetch the category by slug
        brand = Brand.objects.filter(slug=slug).first()
        if not brand:
            return Response({"detail": "Brand not found"}, status=404)
        
        # Initial product query (only published products under the specific category)
        products = Product.objects.filter(status="published", brand=brand).annotate(
            average_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )

        max_price = products.aggregate(Max('price'))['price__max']
        min_price = products.aggregate(Min('price'))['price__min']

        # Filter options from query parameters
        active_colors = [int(color_id) for color_id in request.GET.getlist('color')]
        active_sizes = [int(size_id) for size_id in request.GET.getlist('size')]
        # active_brands = [int(brand_id) for brand_id in request.GET.getlist('brand')]
        active_vendors = [int(vendor_id) for vendor_id in request.GET.getlist('vendor')]
        rating = [int(rating_id) for rating_id in request.GET.getlist('rating')]
        min_price = request.GET.get('from')
        max_price = request.GET.get('to')

        # Initialize filters
        if active_colors or active_sizes or active_vendors or min_price or max_price or rating:
            filters = Q()
            if active_colors:
                filters &= Q(variants__color__id__in=active_colors)
            if active_sizes:
                filters &= Q(variants__size__id__in=active_sizes)
            if active_vendors:
                filters &= Q(vendor__id__in=active_vendors)
            if min_price:
                filters &= Q(price__gte=min_price)
            if max_price:
                filters &= Q(price__lte=max_price)
            if rating:
                filters &= Q(average_rating__gte=int(rating))

            # Apply the filters and distinct to avoid duplicate results
            products = products.filter(filters).distinct().annotate(average_rating=Avg('reviews__rating'), review_count=Count('reviews'))

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 12
        paged_products = paginator.paginate_queryset(products, request)

        # Serialize paginated products
        serialized_products = ProductSerializer(paged_products, many=True, context={'request': request}).data

        # Additional product details with variants and colors
        products_with_details = []
        for product in paged_products:
            product_variants = Variants.objects.filter(product=product)
            product_colors = product_variants.values('color__name', 'color__code', 'sku').distinct()

            product_data = {
                'product': ProductSerializer(product, context={'request': request}).data,  # Serialize the product instance
                'average_rating': product.average_rating or 0,
                'review_count': product.review_count or 0,
                'variants': VariantSerializer(product_variants, many=True).data,
                'colors': list(product_colors),  # ensure list is serialized correctly
            }
            products_with_details.append(product_data)

        # Get distinct filter options for sidebar
        sizes = Size.objects.filter(variants__product__brand=brand).distinct()
        colors = Color.objects.filter(variants__product__brand=brand).distinct()
        # brands = Brand.objects.filter(product__sub_category=category).distinct()
        vendors = Vendor.objects.filter(product__brand=brand).distinct()

        max_price = products.aggregate(Max('price'))['price__max']
        min_price = products.aggregate(Min('price'))['price__min']

        # Prepare context with all the necessary information for the frontend
        context = {
            "colors": ColorSerializer(colors, many=True).data,
            "sizes": SizeSerializer(sizes, many=True).data,
            "vendors": VendorSerializer(vendors, many=True).data,
            "brand": BrandSerializer(brand).data,
            # "category": SubCategorySerializer(category).data, 
            "products": serialized_products,
            "products_with_details": products_with_details,
            "max_price": max_price,
            "min_price": min_price,
        }
        return Response(context)

class ProductSearchAPIView(APIView):
    def get(self, request, format=None):
        query = request.GET.get('q', '')

        productss = Product.objects.filter(
            Q(status="published") & (Q(title__icontains=query) | Q(description__icontains=query))
        )


        products = Product.objects.filter(status="published").annotate(
            average_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).distinct()
        
        # Initialize a combined filters variable
        filters = Q()

        # Handle the search query
        if query:
            filters &= Q(title__icontains=query) | Q(description__icontains=query)

        # Initialize filters for colors, sizes, vendors, min price, max price, and rating
        active_colors = [int(color_id) for color_id in request.GET.getlist('color')]
        active_sizes = [int(size_id) for size_id in request.GET.getlist('size')]
        active_vendors = [int(vendor_id) for vendor_id in request.GET.getlist('vendor')]
        min_price = request.GET.get('from')
        max_price = request.GET.get('to')
        rating = request.GET.get('rating')

        if active_colors or active_sizes or active_vendors or min_price or max_price or rating:
            # Add additional filters
            if active_colors:
                filters &= Q(variants__color__id__in=active_colors)
            if active_sizes:
                filters &= Q(variants__size__id__in=active_sizes)
            if active_vendors:
                filters &= Q(vendor__id__in=active_vendors)
            if min_price:
                filters &= Q(price__gte=min_price)
            if max_price:
                filters &= Q(price__lte=max_price)
            if rating:
                filters &= Q(reviews__rating__gte=int(rating))  # Note that the review count should be done via annotation

        # Filter products using the combined filters and annotate average rating and review count
        products = products.filter(filters).annotate(
            average_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).distinct()
        
        # paginator = PageNumberPagination()
        # paginator.page_size = 12
        # paged_products = paginator.paginate_queryset(products, request)

        # Serialize paginated products
        serialized_products = ProductSerializer(products, many=True, context={'request': request}).data

        # Additional product details with variants and colors
        products_with_details = []
        for product in products:
            product_variants = Variants.objects.filter(product=product)
            product_colors = product_variants.values('color__name', 'color__code', 'sku').distinct()

            product_data = {
                'product': ProductSerializer(product).data,  # Serialize the product instance
                'average_rating': product.average_rating or 0,
                'review_count': product.review_count or 0,
                'variants': VariantSerializer(product_variants, many=True).data,
                'colors': list(product_colors),  # ensure list is serialized correctly
            }
            products_with_details.append(product_data)

        # Get related sizes, colors, brands, vendors, and categories
        variants = Variants.objects.filter(product__in=products).distinct()
        sizes = Size.objects.filter(variants__in=variants).distinct()
        colors = Color.objects.filter(variants__in=variants).distinct()
        brands = Brand.objects.filter(product__in=products).distinct()
        vendors = Vendor.objects.filter(product__in=products).distinct()
        categories = Sub_Category.objects.filter(product__in=products).distinct()

        max_price = products.aggregate(Max('price'))['price__max']
        min_price = products.aggregate(Min('price'))['price__min']

        
        default_max = productss.aggregate(Max('price'))['price__max']
        default_min = productss.aggregate(Min('price'))['price__min']
        

        # Prepare context with all the necessary information for the frontend
        context = {
            "colors": ColorSerializer(colors, many=True).data,
            "sizes": SizeSerializer(sizes, many=True).data,
            "vendors": VendorSerializer(vendors, many=True).data,
            "brands": BrandSerializer(brands, many=True).data,
            "categories": SubCategorySerializer(categories, many=True).data,
            "products": serialized_products,
            "products_with_details": products_with_details,
            "max_price": max_price,
            "min_price": min_price,
            "default_max": default_max,
            "default_min": default_min,
        }
        return Response(context)


#########################################################################

