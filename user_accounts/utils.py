import re
import random
from django.core.mail import send_mail

def is_valid_phone(phone):
    # This regular expression validates phone numbers in various formats, including those with country codes.
    pattern = r'^\+?1?\d{10,}$'
    return bool(re.match(pattern, phone))

def is_strong_password(password):
    # Minimum 8 characters, at least one letter, one number, and one special character
    pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
    return bool(re.match(pattern, password))


def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_to_email(email, otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}'
    email_from = 'aparnavalloth@gmail.com'
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)
