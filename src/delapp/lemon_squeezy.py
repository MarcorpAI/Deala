import requests
from django.conf import settings
import hmac
import hashlib

LEMON_SQUEEZY_API_URL = 'https://api.lemonsqueezy.com/v1'
LEMON_SQUEEZY_WEBHOOK_SECRET = settings.LEMON_SQUEEZY_WEBHOOK_SECRET


def create_checkout(variant_id, user_email, customer_id):
    variant_id = variant_id or settings.LEMON_SQUEEZY_DEFAULT_PLAN_ID
    store_id = settings.LEMON_SQUEEZY_STORE_ID
    headers = {
        'Accept': 'application/vnd.api+json',
        'Content-Type': 'application/vnd.api+json',
        'Authorization': f'Bearer {settings.LEMON_SQUEEZY_API_KEY}'
    }
    
    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "store_id": store_id,
                "variant_id": variant_id,
                "custom_price": None,
                "product_options": {
                    "name": "Checkout",
                    "description": f"Subscription for {user_email}",
                    "redirect_url": settings.LEMON_SQUEEZY_REDIRECT_URL,
                    "receipt_thank_you_note": "Thank you for your purchase!",
                    "receipt_link_url": settings.LEMON_SQUEEZY_RECEIPT_LINK_URL,
                    "receipt_button_text": "Continue",
                    "enabled_variants": [],
                },
                "checkout_data": {
                    "email": user_email,
                }
            },
            "relationships": {
                "store": {
                    "data": {
                        "type": "stores",
                        "id": str(store_id)
                    }
                },
                "variant": {
                    "data": {
                        "type": "variants",
                        "id": str(variant_id)
                    }
                }
            }
        }
    }
    
    # Only add customer_id if it exists
    if customer_id:
        payload["data"]["attributes"]["checkout_data"]["customer_id"] = customer_id
    
    response = requests.post(f'{LEMON_SQUEEZY_API_URL}/checkouts', json=payload, headers=headers)
    
    if response.status_code != 201:
        print(f"Error response: {response.status_code}")
        print(f"Response content: {response.content}")
    
    response.raise_for_status()
    return response.json()

def verify_webhook(payload, signature):
    secret = LEMON_SQUEEZY_WEBHOOK_SECRET.encode()
    expected_signature = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_signature, signature)