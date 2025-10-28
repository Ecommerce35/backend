# payments/services.py
import requests
from django.conf import settings

PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY

def verify_payment(reference):
    """
    Verifies payment with Paystack using the payment reference.
    """
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        return result
    return None
