from django.shortcuts import get_object_or_404
from core.models import *
from product.models import *
from django.db.models import Min, Max
from vendor.models import *
from django.contrib import messages
from order.models import Cart
from userauths.models import Profile
from taggit.models import Tag
from django.db.models import Count, Avg
from datetime import datetime, timedelta
from address.models import Address
import uuid
from django.db.models import Q, Count
import json
import random



def default(request, tag_slug=None):
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key

    rate = request.session.get('rate', 1.0)
    currency = request.session.get('currency', "GHS")

    brands = Brand.objects.all()
    
    today = datetime.now()
    over_morrow = today + timedelta(2)
    current_user = request.user
    
    try:
        device = request.COOKIES['device']
    except KeyError:
        device = None
    
    if request.user.is_authenticated:
        cart = Cart.objects.filter(Q(user=current_user, added=True))
    else:
        cart = Cart.objects.filter(session_id=device, added=True)


    ##Recently viewed products
    viewed_products = request.COOKIES.get('viewed_product', '[]')
    viewed_products = json.loads(viewed_products)

    viewed_products = sorted(viewed_products, key=lambda x: x['timestamp'], reverse=True)

    viewed_product_ids = [vp['id'] for vp in viewed_products]

    products = Product.objects.filter(id__in=viewed_product_ids, status='published')
    products_dict = {product.id: product for product in products}
    sorted_products = [products_dict[pid] for pid in viewed_product_ids if pid in products_dict]

    ##products based on category
    related_products = set()
    for product in products:
        related_products.update(Product.objects.filter(
            status='published', 
            sub_category=product.sub_category
            ).exclude(id=product.id))

    ##products based on search history
    search_history = request.session.get('search_history', [])
    search_related_products = set()
    for query in search_history:
        search_related_products.update(Product.objects.filter(
            status="published", 
            title__icontains=query
            ).distinct().exclude(id__in=viewed_product_ids
            )|Product.objects.filter(
                status="published", 
                description__icontains=query
                ).distinct().exclude(id__in=viewed_product_ids))
        
    #combine the sets of related products then shuffle them randomly
    all_related_products = list(related_products | search_related_products)
    random.shuffle(all_related_products)

    #display only 10 products as recommended
    recommending_products = all_related_products[:10]
   
    
    try:
        vendor_about = About.objects.get(user=request.user)
    except:
        vendor_about = None
    
    try:
        vendor = Vendor.objects.get(user=request.user)
    except:
        vendor = None
    
    cart_count = 0
    if request.user.is_authenticated:
        try:
            if cart_items := Cart.objects.filter(Q(user=current_user, added=True)):
                for cart_item in cart_items:
                    cart_count += cart_item.quantity
            else:
                cart_count = 0
        except:
            cart_count = 0

    else:
        try:
            if cart_items := Cart.objects.filter(session_id=device, added=True):
                for cart_item in cart_items:
                    cart_count += cart_item.quantity
            else:
                cart_count = 0
        except:
            cart_count = 0
    
    total = 0

    for rs in cart:
        if rs.product.variant == 'None':
            total += rs.product.price * rs.quantity
        else:
            total += rs.variant.price * rs.quantity

    main_category = Main_Category.objects.all().order_by
    category = Category.objects.all().order_by('?')
    sub_category = Sub_Category.objects.all()
    vendors = Vendor.objects.all().order_by('?')
    recently_added = Product.objects.filter(status='published').order_by("-date")[:3]
    deals = Product.objects.filter(status='published', deals_of_the_day=True).order_by("?")[:4]
    product = Product.objects.filter(status='published')
    review = ProductReview.objects.all()
    min_max_price = Product.objects.aggregate(Min("price"), Max("price"))

    if request.user.is_authenticated:
        try:
            wishlist = Wishlist.objects.filter(user=request.user)
        except:
            messages.warning(request, "You need to login before accessing your wishlist.")
            wishlist = 0
    else:
        wishlist = 0

    try:
        address = Address.objects.get(user=request.user, status=True)
    except:
        address = None

    return {
        'rate':rate,
        'currency':currency,
        'today':today,
        'recently_viewed':sorted_products,
        'related_products':related_products,
        'search_related_products':search_related_products,
        'recommending_products':recommending_products,
        'all_related_products':all_related_products,
        'over_morrow':over_morrow,
        'main_categories':main_category,
        'category':category,
        'sub_categories':sub_category,
        'wishlist':wishlist,
        'address':address,
        'vendors':vendors,
        'min_max_price':min_max_price,
        "recently_added":recently_added,
        "deals":deals,
        "product":product,
        "cart":cart,
        "total":total,
        "cart_count":cart_count,
        # "user_profile":user_profile,
        "vendor_about":vendor_about,
        "brands":brands,
        "vendor":vendor,
        "review":review,
    }