import random
from django.core.mail import send_mail
import hashlib
from decouple import config



JWT_SECRET_KEY = config("SECRET_KEY")
JWT_ALGORITH = config("ALGORITH")
JWT_EXPIRATION_TIME_MINUTES = 60 * 24 * 6


# Generates a random 4-digit number
def generate_verification_code():
    return str(random.randint(1000, 9999)) 


# Generat hash with salt 
def hash_VC(code):
    if code is not None:
        # Using hashlib for SHA-256
        hash_object = hashlib.sha256(code.encode())
        hash_value = hash_object.hexdigest()
        return hash_value
    else:
        raise ValueError("Code cannot be None. Provide a valid verification code.")


# Send verification code to email
def send_verification_email(email, verification_code):
    subject = "Your Bellyfied account verification code"
    message = f"Your verification code is: {verification_code}"
    from_email = "kukiworldwideng@gmail.com" 
    recipient_list = [email]
    try:
        send_mail(subject, message, from_email, recipient_list)
    except Exception as e:
        print(f"An error occurred: {e}")


