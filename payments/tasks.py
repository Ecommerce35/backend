from celery import shared_task
from .models import Payment
from order.models import *
from product.models import *
from django.utils.crypto import get_random_string
from userauths.models import User
from celery.utils.log import get_task_logger


logger = get_task_logger(__name__)


@shared_task
def create_order_task(user_id, payment_data, payment_id, cart_items_data, address_data, ip):

    try:
        from order.models import Order, OrderProduct  # Import here to avoid serialization issues
        from userauths.models import User
        from product.models import Product, Variants

        user = User.objects.get(id=user_id)
        address = Address.objects.get(id=address_data['id'])

        # Create an Order
        order = Order.objects.create(
            user=user,
            total=payment_data["amount"] / 100,
            payment_method='paystack',
            payment_id=payment_id,
            status="pending",
            address=address,
            ip=ip,
            is_ordered=True,
        )

        # Extract unique vendors
        unique_vendors = set()
        for item_data in cart_items_data:
            product = Product.objects.get(id=item_data["product_id"])
            if product.vendor:
                unique_vendors.add(product.vendor)
        order.vendors.set(unique_vendors)

        # Generate order number
        while True:
            order_number = f"INVOICE_NO-{get_random_string(8)}"
            if not Order.objects.filter(order_number=order_number).exists():
                break
        order.order_number = order_number
        order.save()

        # Loop through serialized cart items and create OrderProduct
        for item_data in cart_items_data:
            product = Product.objects.get(id=item_data["product_id"])
            variant = Variants.objects.get(id=item_data["variant_id"]) if item_data["variant_id"] else None
            price = variant.price if variant else product.price

            OrderProduct.objects.create(
                order=order,
                product=product,
                variant=variant,
                quantity=item_data["quantity"],
                price=price,
                amount=price * item_data["quantity"],
                selected_delivery_option=item_data["delivery_option_id"]
            )

            # Update stock
            if variant:
                variant.quantity -= item_data["quantity"]
                variant.save()
            else:
                product.total_quantity -= item_data["quantity"]
                product.save()

        return order.id
    except Exception as e:
        logger.error(f"Error creating order for user {user_id}: {e}")
        raise

