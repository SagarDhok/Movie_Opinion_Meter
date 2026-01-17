import requests
from django.conf import settings

BREVO_URL = "https://api.brevo.com/v3/smtp/email" 
#  “This is the internet address where I send a POST request when I want Brevo to send an email for me.”

def send_brevo_email(to_email, subject ,text_content):
    data = {
        "sender": {"email": settings.DEFAULT_FROM_EMAIL,
                   "name": "Movie Opinion Meter" },
        "to": [{"email": to_email}],   
        "subject": subject,
        "textContent": text_content

    }
# "to": [
#   {"email": "a@gmail.com"},
#   {"email": "b@gmail.com"},
#   {"email": "c@gmail.com"}
# ] brevo is built like this to send emails in bulk 


    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json"  
    }
# Headers = extra information sent along with the request
# They tell the server how to understand the request and who is sending it.

    try:
        response = requests.post(
            BREVO_URL,
            json=data,
            headers=headers,
            timeout=10
        )
        return response.status_code in (200, 201, 202)
    except requests.exceptions.RequestException:
        return False
# Status code
# Meaning
# 200
# OK
# 201
# Created
# 202
# Accepted

#Examples of errors covered by RequestException
# All of these inherit from it:
# Timeout
# ConnectionError
# HTTPError
# TooManyRedirects
# SSLError

# Signup → User created → UID + token generated → Verification email sent →
# User clicks link → UID decoded → Token checked → Email verified → Login
