import requests
from django.core.cache import cache
from django.conf import settings
from django.core.mail import send_mail, get_connection
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def get_valid_access_token():
    # TODO: implementeren als er meer gebruik gemaakt wordt van mail functie, moet tijd nog vergelijken met huidige tijd
    # token = cache.get('access_token')
    # if token:
    #     return token
    # Vraag een nieuw token op
    TENANT_ID = settings.EMAIL_O365_TENANT_ID
    CLIENT_ID = settings.EMAIL_O365_CLIENT_ID
    CLIENT_SECRET = settings.EMAIL_O365_CLIENT_SECRET
    # Token URL voor Microsoft OAuth2
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    # De data die we nodig hebben voor de client credentials flow
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default'  # Gebruikt de .default scope
    }

    # Verkrijg het access token
    response = requests.post(token_url, data=data)

    if response.status_code == 200:
        token_data = response.json()
        token = token_data['access_token']
        expires_in = token_data['expires_in']
        cache.set('access_token', token, timeout=expires_in - 300)  # 5 minuten marge
        return token
    else:
        raise Exception(f"Failed to retrieve access token: {response.text}")

def send_mail_via_graph_api(access_token, to_email, subject, body):
    headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }

    url = f'https://graph.microsoft.com/v1.0/users/{settings.DEFAULT_FROM_EMAIL}/sendMail'
    
    email_data = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body
            },
            "toRecipients": [
                {"emailAddress": {"address": to_email}}
            ]
        }
    }
    response = requests.post(url, json=email_data, headers=headers)
    response.raise_for_status()


def send_mail(subject, email_inhoud, to_email_list):
    # Gebruik je token
    access_token = get_valid_access_token()
    for to_email in to_email_list:
        send_mail_via_graph_api(access_token, to_email, subject, email_inhoud)
    