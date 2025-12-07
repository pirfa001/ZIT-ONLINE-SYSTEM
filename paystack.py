import os
import requests

PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', '')
PAYSTACK_INITIALIZE_URL = 'https://api.paystack.co/transaction/initialize'
PAYSTACK_VERIFY_URL = 'https://api.paystack.co/transaction/verify/{}'


def _auth_headers():
    if not PAYSTACK_SECRET_KEY:
        raise RuntimeError('PAYSTACK_SECRET_KEY not configured in environment')
    return {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json'
    }


def initialize_transaction(email: str, amount_kobo: int, callback_url: str, metadata: dict = None):
    """Initialize a Paystack transaction and return the JSON response.

    amount_kobo: amount in kobo (NGN * 100)
    """
    payload = {
        'email': email,
        'amount': int(amount_kobo),
        'callback_url': callback_url,
    }
    if metadata:
        payload['metadata'] = metadata

    resp = requests.post(PAYSTACK_INITIALIZE_URL, json=payload, headers=_auth_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def verify_transaction(reference: str):
    """Verify a Paystack transaction by reference."""
    url = PAYSTACK_VERIFY_URL.format(reference)
    resp = requests.get(url, headers=_auth_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_public_key():
    return PAYSTACK_PUBLIC_KEY
