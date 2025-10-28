import json
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from product.models import *
from userauths.models import User
from django.contrib.auth.decorators import login_required
from core.models import *
from django.urls import reverse
from django.conf import settings
from paypal.standard.forms import PayPalPaymentsForm
from core.templatetags.product_tags import shopcartcount
from address.models import Address
# from address.forms import AddressForm
from .service import *
from django.db.models import Q
from payments.views import *
from decimal import Decimal
from django.db import transaction
from datetime import datetime, timedelta
from django.views.decorators.http import require_POST, require_GET
from order.models import *
import requests
from requests.exceptions import RequestException
from django.core.exceptions import ValidationError



@login_required
@require_POST
def buy_now(request, id):
    if request.method == 'POST':
        # Store product details in session for use after successful payment
        request.session['product_id'] = id
        next_page = reverse('order:initiate_buynow')
        return JsonResponse({'redirect_url': next_page, 'message': 'Logged in successfully'}, status=200)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def initiate_buynow(request):
    amount = 0
    try:
        user_profile = get_object_or_404(Profile, user=request.user)
        product_id = request.session.get('product_id')
        quantity = 1

        product = get_object_or_404(Product, id=product_id)
        vendor = get_object_or_404(Vendor, id=product.vendor.id)
        about = get_object_or_404(About, vendor=vendor)

        amount = product.price * quantity

        delivery_options = ProductDeliveryOption.objects.filter(product=product)

        default_delivery_option = ProductDeliveryOption.objects.filter(product=product, default=True).first()
        if not default_delivery_option:
            default_delivery_option = delivery_options.first()
        
        if default_delivery_option:
            delivery_option_cost = default_delivery_option.delivery_option.cost
        else:
            delivery_option_cost = 0

        packaging_fee = calculate_packaging_fee(product.weight, product.volume) * quantity
        delivery_fee = calculate_delivery_fee(
            about.latitude, about.longitude,
            user_profile.latitude, user_profile.longitude,
            delivery_option_cost
        )

        total = Decimal(amount) + Decimal(packaging_fee) + Decimal(delivery_fee)

        context = {
            'amount': amount,
            'default_delivery_option': default_delivery_option,
            'quantity': quantity,
            'total': total,
            'user_profile': user_profile,
            'c': product,
            'total_packaging_fee': packaging_fee,
            'total_delivery_fee': delivery_fee,
            'delivery_option_cost': delivery_option_cost,
            'delivery_options': delivery_options,
        }
        return render(request, 'initiate.html', context)

    except Product.DoesNotExist:
        # Handle product not found
        return render(request, 'payment_error.html', {'message': 'Product not found.'})
    except Variants.DoesNotExist:
        # Handle variant not found
        return render(request, 'payment_error.html', {'message': 'Variant not found.'})
    except ProductDeliveryOption.DoesNotExist:
        # Handle delivery option not found
        delivery_options = []
        context = {
            'user_profile': user_profile,
            'quantity': quantity,
            'amount': amount,
            'total': Decimal(amount),
            'product': product,
            'default_delivery_option': default_delivery_option,
            'total_packaging_fee': packaging_fee,
            'total_delivery_fee': Decimal(0),
            'delivery_option_cost': Decimal(0),
            'delivery_options': delivery_options,
        }
        return render(request, 'initiate.html', context)
    except Exception as e:
        # Handle other exceptions
        return render(request, 'payment_error.html', {'message': str(e)})

@login_required
@login_required
def update_profile_location(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        option_id = data.get('option_id', '')
        address = data.get('location')
        print(address)
        
        profile = Profile.objects.get(user=request.user)
        profile.address = address
        profile.latitude = latitude
        profile.longitude = longitude
        profile.save()
        print('heloooooooooooooooooooooooooo')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
@require_POST
def update_delivery_option(request, option_id):
    if request.method == 'POST':
        rate = request.session.get('rate', 1.0)
        currency = request.session.get('currency', "GHS")

        user_profile = Profile.objects.get(user=request.user)
        product_id = request.session.get('product_id')
        quantity = 1
        product = get_object_or_404(Product, id=product_id)
        vendor = get_object_or_404(Vendor, id=product.vendor.id)
        about = get_object_or_404(About, vendor=vendor)

        amount = product.price * quantity


        ProductDeliveryOption.objects.filter(product_id=product_id).update(default=False)
        ProductDeliveryOption.objects.filter(delivery_option_id=option_id, product_id=product_id).update(default=True)

        default_delivery_option = ProductDeliveryOption.objects.filter(product=product, default=True).first()

        delivery_option_cost = default_delivery_option.delivery_option.cost

        packaging_fee = calculate_packaging_fee(product.weight, product.volume) * quantity

        delivery_fee = calculate_delivery_fee(
            about.latitude, about.longitude,
            user_profile.latitude, user_profile.longitude,
            delivery_option_cost  # Use the first product's delivery option cost for calculation
        )

        total_delivery_fee = Decimal(delivery_fee)
        total = Decimal(packaging_fee) + total_delivery_fee + Decimal(amount)

        return JsonResponse({
            'success': True, 
            'total_amount_':f'{currency}{round(float(total) * rate, 2):,.2f}',
            'total_amount_o':f'{round(float(total) * rate, 2)}',
            'total_delivery_fee':f'{currency}{round(float(total_delivery_fee) * rate, 2):,.2f}',
            'total_packaging_fee':f'{currency}{round(float(packaging_fee) * rate, 2):,.2f}',
        })

    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


@login_required
@require_POST
def paystack_create_payment(request):
    try:
        product_id = request.POST.get('product_id')
        variant_id = request.POST.get('variant_id', '')
        quantity = int(request.POST.get('quantity', 1))
        total = request.POST.get('total')
        delivery_option = request.POST.get('delivery_option_')

        request.session['product_id'] = product_id
        request.session['variant_id'] = variant_id
        request.session['quantity'] = quantity
        request.session['delivery_option'] = delivery_option

        email = request.user.email
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        paystack_fee = float(total) * 0.01

        data = {
            "email": email,
            "amount": int((float(total) + float(paystack_fee)) * 100),  # Amount in kobo
            "callback_url": request.build_absolute_uri(reverse('order:paystack_execute'))
        }

        response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, json=data)
        response.raise_for_status()  # Raises a HTTPError if the HTTP request returned an unsuccessful status code
        response_data = response.json()

        if response_data.get('status'):
            authorization_url = response_data['data']['authorization_url']
            return redirect(authorization_url)
        else:
            return render(request, 'payment_error.html', {'error': response_data.get('message', 'An error occurred')})

    except ValueError as ve:
        messages.error(request, f"Value error: {ve}")
        return render(request, 'payment_error.html', {'error': str(ve)})
    except RequestException as re:
        messages.error(request, f"Request exception: {re}")
        return render(request, 'payment_error.html', {'error': str(re)})
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")
        return render(request, 'payment_error.html', {'error': str(e)})

@login_required
def paystack_execute(request):
    reference = request.GET.get('reference')
    payment_data = verify_payment(reference)
    if payment_data and payment_data['status'] == 'success':
        # Retrieve product details from session
        product_id = request.session.get('product_id')
        variant_id = request.session.get('variant_id')
        quantity = request.session.get('quantity')
        delivery_option = request.session.get('delivery_option')

        # Create order and order product
        product = get_object_or_404(Product, id=product_id)
        variant = get_object_or_404(Variants, id=variant_id) if variant_id else None

        if product.variant == 'None':
            amount = product.price * quantity
        else:
            amount = variant.price * quantity

        order = Order(
            user=request.user, 
            total=amount, 
            vendors=product.vendor, 
            payment_method='paystack', 
            status='pending'
        )
        invoice = f'INVOICE{order.id}'
        order.order_number = invoice
        order.save()

        OrderProduct.objects.create(
            order=order,
            product=product,
            variant=variant,
            delivery_option_id=delivery_option,
            quantity=quantity,
            amount=amount,
            price=variant.price if variant else product.price
        )
        return redirect('userauths:dashboard')  # Redirect to your checkout or success page
    else:
        return redirect('order:payment_cancelled')

def verify_payment(reference):
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }
    response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
    response_data = response.json()
    if response_data['status']:
        return response_data['data']
    else:
        return None

@login_required
def payment_cancelled(request):
    return render(request, 'payment_cancelled.html')


def deletefromcart(request):
    rate = request.session.get('rate', 1.0)
    currency = request.session.get('currency', "GHS")
    current_user = request.user
    device = {}
    try:
        device = request.COOKIES['device']
    except:
        device = None

    cart_count = 0
    total = 0
    data = json.loads(request.body)
    cart_id = data.pop("cart_id")
    if request.user.is_authenticated:
        Cart.objects.filter(id=cart_id, user=request.user).delete()
    else:
        Cart.objects.filter(id=cart_id, session_id=device).delete()
    
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user)
    else:
        cart = Cart.objects.filter(session_id=device)

    # Calculate cart count and total
    if current_user.is_authenticated:
        cart_items = Cart.objects.filter(user=current_user)
    else:
        cart_items = Cart.objects.filter(session_id=device)

    cart_count = sum(item.quantity for item in cart_items)
    # total = sum(item.product.price * item.quantity if item.product.variant == 'None' else item.variant.price * item.quantity for item in cart_items)

    total_packaging_fee = 0
    for rs in cart_items:
        if rs.product.variant == 'None':
            total += rs.product.price * rs.quantity
        else:
            total += rs.variant.price * rs.quantity

        packaging_fee = calculate_packaging_fee(rs.product.weight, rs.product.volume) * rs.quantity
        total_packaging_fee += packaging_fee

    return JsonResponse({
        'status': 'Success',
        'message': 'Product deleted successfully',
        'id':cart_id,
        'total_packaging_fee':f'{currency}{round(total_packaging_fee * rate, 2):,.2f}',
        'cart_count':cart_count,
        'total':f'{currency}{round(total * rate, 2):,.2f}',
        'shop_cart_count':cart.count(),
    })



def addtocart(request, id):
    rate = request.session.get('rate', 1.0)
    currency = request.session.get('currency', "GHS")
    cart_count = 0
    added_quantity = 0
    total = 0
    current_user = request.user
    
    device = request.COOKIES.get('device', None)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    
    variant_id = data.get("variant_id")
    product_id = data.get("product_id")
    product = get_object_or_404(Product, pk=product_id)

    try:
        variant = Variants.objects.get(id=variant_id)
    except Variants.DoesNotExist:
        variant = None

    if request.user.is_authenticated:
        if variant:
            cart_item, created = Cart.objects.get_or_create(
                user = request.user,
                product=product,
                quantity = 1,
                variant=variant,
            )
        else:
            cart_item, created = Cart.objects.get_or_create(
                user = request.user,
                product=product,
                quantity = 1,
                variant__isnull=True,
            )
    else:
        if variant:
            cart_item, created = Cart.objects.get_or_create(
                session_id = device,
                product=product,
                variant=variant,
                quantity = 1
            )
        else:
            cart_item, created = Cart.objects.get_or_create(
                session_id = device,
                product=product,
                quantity = 1,
                variant__isnull=True,
            )
    
    if not created:
        cart_item.quantity += 1
    else:
        cart_item.quantity = 1
    cart_item.save()
    added_quantity = cart_item.quantity
            
    # Calculate cart count and total
    if current_user.is_authenticated:
        cart_items = Cart.objects.filter(user=current_user)
    else:
        cart_items = Cart.objects.filter(session_id=device)

    cart_count = sum(item.quantity for item in cart_items)
    total = sum(item.product.price * item.quantity if item.product.variant == 'None' else item.variant.price * item.quantity for item in cart_items)

    context = {
        "cart_count": cart_count,
        "total": f'{currency}{round(total * rate, 2)}',
        "added_quantity": added_quantity,
    }

    return JsonResponse(context, safe=False)


# Product Detail Quantity Update
def increase_quantity(request):
    rate = request.session.get('rate', 1.0)
    currency = request.session.get('currency', "GHS")
    current_user = request.user
    try:
        device = request.COOKIES['device']
    except:
        device = None

    added_quantity = 0
    cart_count = 0
    total = 0
    data = json.loads(request.body)
    product_id = data.pop("product_id")
    variant_id = data.pop("variant_id")
    current_user = request.user
    product= Product.objects.get(id=product_id)   # from variant add to cart

    if product.variant != 'None':
        cart_check = Cart.objects.filter(variant_id=variant_id)
    else:
        cart_check = Cart.objects.filter(product_id=product_id)
    for c in cart_check:
        cart_id = c.id

    if cart_check.exists():
        data = Cart.objects.get(id=cart_id)
        data.quantity += 1
        data.save()  # save data
        added_quantity = data.quantity
        msg = 'Quantity updated'
    else:
        msg = "Couldn't Update quantity"
        return HttpResponse("Couldn't Update quantity")
    
    if current_user.is_authenticated:
        cart_items = Cart.objects.filter(user=current_user)
    else:
        cart_items = Cart.objects.filter(session_id=device)

    cart_count = sum(item.quantity for item in cart_items)
    total = sum(item.product.price * item.quantity if item.product.variant == 'None' else item.variant.price * item.quantity for item in cart_items)

    context = {
        "cart_count":cart_count,
        "total":f'{currency}{round(total * rate, 2)}',
        "msg":msg,
        "added_quantity":added_quantity,
    }
    return JsonResponse(context, safe=False)

# Product Detail Quantity Update
def decrease_quantity(request):
    rate = request.session.get('rate', 1.0)
    currency = request.session.get('currency', "GHS")
    current_user = request.user
    try:
        device = request.COOKIES['device']
    except:
        device = None

    added_quantity = 0
    cart_count = 0
    total = 0
    data = json.loads(request.body)
    product_id = data.pop("product_id")
    variant_id = data.pop("variant_id")
    current_user = request.user
    product= Product.objects.get(id=product_id)   # from variant add to cart

    if product.variant != 'None':
        cart_check = Cart.objects.filter(variant_id=variant_id)
    else:
        cart_check = Cart.objects.filter(product_id=product_id)
    for c in cart_check:
        cart_id = c.id

    if cart_check.exists():
        data = Cart.objects.get(id=cart_id)
        data.quantity -= 1
        data.save()  # save data
        added_quantity = data.quantity
        msg = 'Quantity updated'
    else:
        msg = "Couldn't Update quantity"
        return HttpResponse("Couldn't Update quantity")
    
    if current_user.is_authenticated:
        cart_items = Cart.objects.filter(user=current_user)
    else:
        cart_items = Cart.objects.filter(session_id=device)

    cart_count = sum(item.quantity for item in cart_items)
    total = sum(item.product.price * item.quantity if item.product.variant == 'None' else item.variant.price * item.quantity for item in cart_items)

    context = {
        "cart_count":cart_count,
        "total":f'{currency}{round(total * rate, 2):,.2f}',
        "msg":msg,
        "added_quantity":added_quantity,
    }
    return JsonResponse(context, safe=False)


# # Cart Quantity Update
def updateQuantity(request):
    rate = request.session.get('rate', 1.0)
    currency = request.session.get('currency', "GHS")
    device = {}
    try:
        device = request.COOKIES['device']
    except:
        device = None

    added_quantity = 0
    cart_count = 0
    total = 0
    current_user = request.user
    product_id = int(request.POST.get('product_id'))
    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity'))
    cart_id = int(request.POST.get('cart_id'))
    
    current_user = request.user
    product= Product.objects.get(pk=product_id)   # from variant add to cart

    try:
        cart_item = Cart.objects.get(
            id=cart_id,
        )
        cart_item.quantity=quantity
        cart_item.save()
        added_quantity = cart_item.quantity
        msg = 'Quantity updated'
    except Cart.DoesNotExist:
        msg = 'Could not update'
        pass
        
    if current_user.is_authenticated:
        cart_items = Cart.objects.filter(user=current_user)
    else:
        cart_items = Cart.objects.filter(session_id=device)

    cart_count = sum(item.quantity for item in cart_items)
    # total = sum(item.product.price * item.quantity if item.product.variant == 'None' else item.variant.price * item.quantity for item in cart_items)

    total_packaging_fee = 0
    for rs in cart_items:
        if rs.product.variant == 'None':
            total += rs.product.price * rs.quantity
        else:
            total += rs.variant.price * rs.quantity

        packaging_fee = calculate_packaging_fee(rs.product.weight, rs.product.volume) * rs.quantity
        total_packaging_fee += packaging_fee

    context = {
        "cart_count":cart_count,
        "total": f'{currency}{round(total * rate, 2):,.2f}',
        "msg":msg,
        "added_quantity":added_quantity,
        "total_packaging_fee":f'{currency}{round(total_packaging_fee * rate, 2):,.2f}',
    }
    return JsonResponse(context, safe=False)
  
@login_required
def shopcart(request):
    device = {}
    try:
        device = request.COOKIES['device']
    except:
        device = None

    current_user = request.user  #Access session infromation
    if request.user.is_authenticated:
        cart = Cart.objects.filter(Q(user=current_user, added=True))
    else:
        cart = Cart.objects.filter(session_id=device, added=True)
    products = Product.objects.all()
    total = 0
    total_packaging_fee = 0
    
    for rs in cart:
        if rs.product.variant == 'None':
            total += rs.product.price * rs.quantity
        else:
            total += rs.variant.price * rs.quantity

        packaging_fee = calculate_packaging_fee(rs.product.weight, rs.product.volume)* rs.quantity
        total_packaging_fee += packaging_fee
        
    context = {
        'shopcart':cart,
        'total':total,
        'total_packaging_fee':total_packaging_fee,
        'products':products,
    }
    return render(request, "shopcart.html", context)


def address_view(request):
    current_user = request.user
    # addresses = Address.objects.filter(user=current_user).order_by('-date')
    # if request.method == 'POST':
    #     form = AddressForm(request.POST)
    #     if form.is_valid():
    #         first_name = form.cleaned_data['first_name']
    #         last_name = form.cleaned_data['last_name']
    #         email = form.cleaned_data['email']
    #         address = form.cleaned_data['address']
    #         mobile = form.cleaned_data['mobile']
    #         country = form.cleaned_data['country']
    #         region = form.cleaned_data['region']
    #         town = form.cleaned_data['town']

    #         new = Address.objects.create(
    #             user = current_user,
    #             first_name=first_name,
    #             last_name=last_name,
    #             email=email,
    #             address=address,
    #             mobile=mobile,
    #             region=region,
    #             country=country,
    #             town=town,
    #         )
    #         new.save()
    #         messages.success(request, "Address Added Successfully.")
    #         return redirect("order:address")
    # else:
    #     print("Error")
    #     form = AddressForm()
        
    context = {
        # 'addresses': addresses,
        # 'form': form,
    }
    return render(request, 'address.html', context)

@login_required
def checkout_view(request):
    current_user = request.user
    user_profile = get_object_or_404(Profile, user=request.user)
    
    cart_items = Cart.objects.filter(user=current_user).order_by('date')
    
    if not cart_items.exists():
        messages.info(request, "There are no items to checkout")
        return redirect('order:shopcart')
    
    total_delivery_fee = 0
    all_product_delivery_options = {}
    processed_vendors = set()
    delivery_date_ranges = {}
    vendor_delivery_fees = {}

    for item in cart_items:
        product = item.product
        vendor = product.vendor

        # Retrieve delivery options for the product that are set to default
        default_delivery_options = ProductDeliveryOption.objects.filter(product=product, default=True).first()
        

        if default_delivery_options:
            # Collect the costs of all default delivery options without summing them
            delivery_option_cost = default_delivery_options.delivery_option.cost

            if vendor not in processed_vendors:
                # Calculate the delivery fee based on the vendor's location and add it once
                delivery_fee = calculate_delivery_fee(
                    vendor.about.latitude, vendor.about.longitude,
                    user_profile.latitude, user_profile.longitude,
                    delivery_option_cost  # Use the first product's delivery option cost for calculation
                )
                total_delivery_fee += Decimal(delivery_fee)
                vendor_delivery_fees[vendor.id] = Decimal(delivery_fee)
                processed_vendors.add(vendor)
            else:
                # If the vendor has been processed, add only the delivery option cost
                total_delivery_fee += delivery_option_cost
        else:
            messages.warning(request, f"No delivery options found for product {product.title}")
        
        # Calculate delivery date range
        min_delivery_date = datetime.now() + timedelta(days=default_delivery_options.delivery_option.min_days)
        max_delivery_date = datetime.now() + timedelta(days=default_delivery_options.delivery_option.max_days)
        delivery_date_range = f"{min_delivery_date.strftime('%d %B')} to {max_delivery_date.strftime('%d %B')}"

        delivery_date_range = default_delivery_options.get_delivery_date_range()
           

        # Store the delivery date range in a separate dictionary
        delivery_date_ranges[product.id] = delivery_date_range

        # Store all delivery options for the product for display purposes
        all_product_delivery_options[product.id] = ProductDeliveryOption.objects.filter(product=product)
        
    
    # Calculate total price of items in the cart
    total = sum(
        Decimal(rs.product.price) * rs.quantity if rs.product.variant == 'None' else Decimal(rs.variant.price) * rs.quantity
        for rs in cart_items
    )

    total_packaging_fee = 0
    for rs in cart_items:
        packaging_fee = calculate_packaging_fee(rs.product.weight, rs.product.volume) * rs.quantity
        total_packaging_fee += packaging_fee

    grand_total = total + total_delivery_fee + Decimal(total_packaging_fee)

    # Coupon handling
    clipped_coupons = ClippedCoupon.objects.filter(user=current_user)
    applied_coupon = None
    discount_amount = Decimal(0)

    # Check if a coupon is already stored in the session
    if 'applied_coupon' in request.session:
        try:
            coupon = Coupon.objects.get(id=request.session['applied_coupon'])
            if coupon.is_valid() and clipped_coupons.filter(coupon=coupon).exists():
                applied_coupon = coupon
                if coupon.discount_amount:
                    discount_amount = coupon.discount_amount
                elif coupon.discount_percentage:
                    discount_amount = (grand_total * Decimal(coupon.discount_percentage / 100)).quantize(Decimal('0.01'))
                grand_total -= discount_amount
        except Coupon.DoesNotExist:
            del request.session['applied_coupon']  # Remove invalid coupon from session

    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                if coupon.is_valid() and clipped_coupons.filter(coupon=coupon).exists():
                    applied_coupon = coupon
                    if coupon.discount_amount:
                        discount_amount = coupon.discount_amount
                    elif coupon.discount_percentage:
                        discount_amount = (grand_total * Decimal(coupon.discount_percentage / 100)).quantize(Decimal('0.01'))
                    grand_total -= discount_amount
                    coupon.used_count += 1
                    coupon.save()
                    request.session['applied_coupon'] = coupon.id  # Store the coupon in the session
                else:
                    messages.error(request, "Invalid or expired coupon.")
            except Coupon.DoesNotExist:
                messages.error(request, "Coupon does not exist.")

    context = {
        'total_delivery_fee': total_delivery_fee,
        'shopcart': cart_items,
        'default_delivery_options': default_delivery_options,
        'grand_total': grand_total,
        'total_packaging_fee': total_packaging_fee,
        'total': total,
        'delivery_date_range': delivery_date_range,
        'product_delivery_options': all_product_delivery_options,
        'clipped_coupons': clipped_coupons,
        'user_profile': user_profile,
        'applied_coupon': applied_coupon,
        'discount_amount': discount_amount,
    }
    return render(request, 'checkout.html', context)

@require_POST
@login_required
def remove_coupon(request):
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']
    return redirect('order:checkout')

@csrf_exempt
@login_required
def update_delivery_fee(request):
    rate = request.session.get('rate', 1.0)
    currency = request.session.get('currency', "GHS")

    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        delivery_option_id = data.get('delivery_option_id')

        current_user = request.user
        cart_items = Cart.objects.filter(user=current_user)
        total = 0
        total_packaging_fee = 0

        for rs in cart_items:
            if rs.product.variant == 'None':
                total += rs.product.price * rs.quantity
            else:
                total += rs.variant.price * rs.quantity

            packaging_fee = calculate_packaging_fee(rs.product.weight, rs.product.volume) * rs.quantity
            total_packaging_fee += packaging_fee

        try:
            user_profile = Profile.objects.get(user=current_user)

            with transaction.atomic():
                # Update all delivery options for the product to False except the selected one
                ProductDeliveryOption.objects.filter(product_id=product_id).update(default=False)
                
                # Set the selected delivery option as default
                ProductDeliveryOption.objects.filter(delivery_option_id=delivery_option_id, product_id=product_id).update(default=True)

                total_delivery_fee = Decimal(0)
                processed_vendors = set()
                quantity = 0

                for item in cart_items:
                    product = item.product
                    vendor = product.vendor
                    quantity += item.quantity

                    # Retrieve the default delivery option for the product
                    default_delivery_option = ProductDeliveryOption.objects.filter(product=product, default=True).first()

                    if default_delivery_option:
                        delivery_option_cost = default_delivery_option.delivery_option.cost

                        if vendor not in processed_vendors:
                            # Calculate the delivery fee based on the vendor's location and add it once
                            delivery_fee = calculate_delivery_fee(
                                vendor.about.latitude, vendor.about.longitude,
                                user_profile.latitude, user_profile.longitude,
                                delivery_option_cost  # Use the first product's delivery option cost for calculation
                            )
                            total_delivery_fee += Decimal(delivery_fee)
                            processed_vendors.add(vendor)
                        else:
                            # If the vendor has been processed, add only the delivery option cost
                            total_delivery_fee += Decimal(delivery_option_cost)

                        total = sum(
                            Decimal(rs.product.price) * Decimal(rs.quantity) if rs.product.variant == 'None' else Decimal(rs.variant.price) * Decimal(rs.quantity)
                            for rs in cart_items
                        )

                        total_packaging_fee = 0
                        for rs in cart_items:
                            packaging_fee = calculate_packaging_fee(rs.product.weight, rs.product.volume) * rs.quantity

                            total_packaging_fee += packaging_fee

                        grand_total = Decimal(total) + Decimal(total_delivery_fee) + Decimal(total_packaging_fee)

                        discount_amount = Decimal(0)
                        if 'applied_coupon' in request.session:
                            try:
                                coupon = Coupon.objects.get(id=request.session['applied_coupon'])
                                if coupon.is_valid() and ClippedCoupon.objects.filter(user=current_user, coupon=coupon).exists():
                                    if coupon.discount_amount:
                                        discount_amount = coupon.discount_amount
                                    elif coupon.discount_percentage:
                                        discount_amount = (grand_total * Decimal(coupon.discount_percentage / 100)).quantize(Decimal('0.01'))
                                    grand_total -= discount_amount
                            except Coupon.DoesNotExist:
                                del request.session['applied_coupon']  # Remove invalid coupon from session

                    else:
                        messages.warning(request, f"No delivery options found for product {product.title}")

                return JsonResponse({
                    'total_delivery_fee': f'{currency}{round(Decimal(total_delivery_fee) * Decimal(rate), 2):,.2f}',
                    'total': f'{currency}{round(Decimal(total) * Decimal(rate), 2):,.2f}',
                    'grand_total': f'{currency} {round(Decimal(grand_total) * Decimal(rate), 2):,.2f}',
                    'discount_amount': f'{currency}{round(Decimal(discount_amount) * Decimal(rate), 2):,.2f}'
                })


        except ProductDeliveryOption.DoesNotExist:
            return JsonResponse({'error': 'Selected delivery option does not exist.'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)
