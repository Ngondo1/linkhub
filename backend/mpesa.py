# mpesa.py (inside your Backend/ folder)

import requests
import base64
import datetime
import os
from flask import current_app
from dotenv import load_dotenv

load_dotenv()

# Load env vars
MPESA_ENV = os.getenv("MPESA_ENV", "sandbox")
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL")

# Base URLs
BASE_URL = "https://sandbox.safaricom.co.ke" if MPESA_ENV == "sandbox" else "https://api.safaricom.co.ke"


def get_access_token():
    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    res = requests.get(url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET))
    access_token = res.json().get("access_token")
    return access_token


def generate_password():
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    data_to_encode = MPESA_SHORTCODE + MPESA_PASSKEY + timestamp
    encoded = base64.b64encode(data_to_encode.encode())
    return encoded.decode("utf-8"), timestamp

def get_access_token():
    print("Loaded CONSUMER_KEY:", repr(MPESA_CONSUMER_KEY))
    print("Loaded CONSUMER_SECRET:", repr(MPESA_CONSUMER_SECRET))
    print("BASE_URL:", BASE_URL)
    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    res = requests.get(url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET))
    print("ACCESS TOKEN RESPONSE:", res.text)
    if res.status_code != 200:
        raise Exception(f"Failed to get access token: {res.status_code} {res.text}")
    access_token = res.json().get("access_token")
    print("ACCESS TOKEN:", access_token)
    return access_token


def stk_push(phone, amount, account_reference="LinkHub", transaction_desc="Subscription"):
    print("STK_PUSH CALLED with:", phone, amount)
    access_token = get_access_token()
    password, timestamp = generate_password()
    print("MPESA RAW RESPONSE 00:")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    print("MPESA RAW RESPONSE 01:")
    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }
    print("MPESA RAW RESPONSE 02:")
    response = requests.post(
        f"{BASE_URL}/mpesa/stkpush/v1/processrequest",
        headers=headers,
        json=payload
    )
    print("MPESA RAW RESPONSE 03:", response.text)  # Debug print

    if not response.text.strip():
        raise Exception("Empty response from M-Pesa API")

    data = response.json()
    return data