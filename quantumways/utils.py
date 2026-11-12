from rest_framework.response import Response
from typing import Optional, Dict, Any, Type, List
from rest_framework import serializers
import re
import random
import requests
from rest_framework import serializers
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from rest_framework import status
from rest_framework_simplejwt.tokens import TokenError, AccessToken
import string
import secrets
from rest_framework.exceptions import ValidationError
import base64
import binascii
import uuid
import random
from io import BytesIO
from django.core.files.base import ContentFile
from rest_framework import serializers
from PIL import Image, ImageFile
import six
from decimal import Decimal

def response_message_utils(
        message:str=None,
        data: Optional[Dict[str, Any]]=None,
        status_code: int = 200
    ) -> Response:

        """
            Helper function to return json response

            Args:
                message (str): Message to be included in the response.
                data (dict): Optional Additional data to be returned in the response.
                status_code (int): HTTP status code for the response

            Returns:
                JsonResponse: Django JsonResponse with the given data.
        """
        response_data = {}

        if message is not None:
            response_data.update({"message": message})

        if data is not None:
            response_data.update({"data": data})

        return Response(response_data, status=status_code)


# Helper function that extracts the first error message
def extract_first_error_message(errors) -> str:
    if isinstance(errors, list): # handling errors for list of dicts
        for error in errors:
            if error: # Skip empty dict
                return extract_first_error_message(error)
    elif isinstance(errors, dict):
        for v in errors.values():
            # If value is a list return the first message
            if isinstance(v, list) and v:
                sub = extract_first_error_message(v)
                if sub:
                    return sub
            elif isinstance(v, dict):
                message = extract_first_error_message(v)
                if message:
                    return message 
            else:
                return v
    elif isinstance(errors, list) and errors:
        return errors[0] #flatten the error
    return errors




def is_field_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, dict)) and not value:
        return True
    if isinstance(value, (int, Decimal)) and not value:
        return True
    return False

def raise_validation(error_message: str):
    raise serializers.ValidationError({f"error": error_message})
    
# Regex password that must have atleast 1 uppercase, symbol, number
def is_valid_password(password) -> bool:
    pattern = r'^(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).+$'
    return bool(re.match(pattern, password))

# Regex for contact number that only accepts 11 digits
def is_valid_contact_number(conctact_number) -> bool:
    conctact_number = conctact_number.strip()

    # Accept if blank (empty or whitespace-only)
    if not conctact_number:
        return True
    
    # Accept only digits if not blank
    return bool(re.match(r'^\d+$', conctact_number))

def is_valid_input_int(input) -> bool:
    # Accept only digits if not blank
    return bool(re.match(r'^\d+$', input))

#Regex for input(string) that only accepts letters
def is_valid_input_str(input_str) -> bool:
    input_str = input_str.strip()

    # Accept if blank (empty or whitespace-only)
    if not input_str:
        return True
    
    # Accept only letters if not blank
    return bool(re.match(r'^[A-Za-z\s]+$', input_str))

# Helper function that validate the email
def is_valid_email(email) -> bool:
    #check if the email matches the regex pattern for a valid email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        #if the email does not match the pattern, return False
        return False
     #if the email matches the pattern, return True (indicating it's valid)
    return True

# Helper function that will generate password
def generate_password(password_length=12) -> str:
    
    symbols = "!@#$%"
    digits = string.digits
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    all_chars = symbols + digits + lowercase + uppercase
    
    # Ensure at least one character from each category
    password = [
        secrets.choice(symbols),
        secrets.choice(digits),
        secrets.choice(lowercase),
        secrets.choice(uppercase)
    ]
    
    password += [secrets.choice(all_chars) for _ in range(password_length - 4)]
    
    # Shuffle to avoid predictable pattern
    random.shuffle(password)

    return ''.join(password)


class CustomCharField(serializers.CharField):
    def __init__(self, blank_message=None, required_message=None, **kwargs):

        self.custom_blank_message = blank_message
        self.custom_required_message = required_message

        # Set allow_blank to True only if blank_message is provided
        if blank_message:
            kwargs["allow_blank"] = True

        super().__init__(**kwargs)

        # Inject custom error messages
        if self.custom_required_message:
            self.error_messages["required"] = self.custom_required_message
        if self.custom_blank_message:
            self.error_messages["blank"] = self.custom_blank_message

    def run_validation(self, data=serializers.empty):
        # Catch blank string manually (even if allow_blank=True)
        if data == '' and self.custom_blank_message:
            raise ValidationError(self.custom_blank_message)
        return super().run_validation(data)
    
class CustomIntegerField(serializers.IntegerField):
    def __init__(self, blank_message=None, required_message=None, **kwargs):
        self.custom_blank_message = blank_message
        self.custom_required_message = required_message

        super().__init__(**kwargs)

        if self.custom_required_message:
            self.error_messages["required"] = self.custom_required_message
        if self.custom_blank_message:
            self.error_messages["invalid"] = self.custom_blank_message
            self.error_messages["null"] = self.custom_blank_message

    def run_validation(self, data=serializers.empty):
        if data in ['', None] and self.custom_blank_message:
            raise ValidationError(self.custom_blank_message)
        return super().run_validation(data)
    
class CustomDecimalField(serializers.DecimalField):
    def __init__(self, blank_message=None, required_message=None, **kwargs):
        error_messages = kwargs.get("error_messages", {})

        if required_message:
            error_messages["required"] = required_message
        if blank_message:
            error_messages["invalid"] = blank_message
            error_messages["null"] = blank_message

        kwargs["error_messages"] = error_messages
        super().__init__(**kwargs)

    def run_validation(self, data=serializers.empty):
        if data in ['', None] and self.custom_blank_message:
            raise ValidationError(self.custom_blank_message)
        return super().run_validation(data)

    
class CustomEmailField(serializers.EmailField):

    def __init__(self, blank_message, required_message, **kwargs):
 
        self.custom_blank_message = blank_message
        self.custom_required_message = required_message

        # Set allow_blank to True only if blank_message is provided
        if blank_message:
            kwargs["allow_blank"] = True

        super().__init__(**kwargs)

        # Inject custom error messages
        if self.custom_required_message:
            self.error_messages["required"] = self.custom_required_message
        if self.custom_blank_message:
            self.error_messages["blank"] = self.custom_blank_message

    def run_validation(self, data=serializers.empty):
        if data == '' and self.blank_message:
            raise_validation(self.blank_message)
        return super().run_validation(data)
    
    def get_error_messages(self):
        messages = super().get_error_messages()
        if self.required_message:
            messages["required"] = self.required_message
        return messages


class CustomBooleanField(serializers.BooleanField):

    def __init__(self, blank_message, required_message, **kwargs):
 
        self.custom_blank_message = blank_message
        self.custom_required_message = required_message

        # Set allow_blank to True only if blank_message is provided
        if blank_message:
            kwargs["allow_blank"] = True

        super().__init__(**kwargs)

        # Inject custom error messages
        if self.custom_required_message:
            self.error_messages["required"] = self.custom_required_message
        if self.custom_blank_message:
            self.error_messages["blank"] = self.custom_blank_message

    def run_validation(self, data=serializers.empty):
        if data == '' and self.blank_message:
            raise_validation(self.blank_message)
        return super().run_validation(data)
    
    def get_error_messages(self):
        messages = super().get_error_messages()
        if self.required_message:
            messages["required"] = self.required_message
        return messages



def send_password_to_email(
    subject=None,
    message=None,
    recipient_list=None,
    generated_password=None,
    login_url="https://qwb-inventory.vercel.app/auth/login"
):
    email = EmailMultiAlternatives(
        subject=subject,
        body=message,
        to=recipient_list,
    )

    html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background-color: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h2 style="color: #333;">Your Generated Password</h2>          
                <p>Hello, <strong>{{ recipient_email }}</strong></p>  
                <p>{{ message }}</p>
                <p style="font-size: 24px; font-weight: bold; color: #1A2D6B;">{{ generated_password }}</p>
                <a href="{{ login_url }}" style="display: inline-block; margin-top: 20px; padding: 12px 20px; background-color: #1A2D6B; color: white; text-decoration: none; border-radius: 6px;">Log In to Your Account</a>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="font-size: 12px; color: #888;">Thank you,<br>Quantumways Builder Team</p>
            </div>
        </body>
        </html>
    """)
    # <p>For your security, please log in and change your password as soon as possible.</p>
    context = Context({'generated_password': generated_password, 'recipient_email': recipient_list[0], 'login_url': login_url, 'message': message})
    html_content = html_template.render(context)

    email.attach_alternative(html_content, "text/html")

    email.send(fail_silently=False)


def get_user_from_token(request, user):

    #get the 'Authorization' from the header
    auth_header = request.headers.get('Authorization', None)

    #check if the 'Authorization' header is missing or doesn't start with Bearer
    if not auth_header or not auth_header.startswith('Bearer '):
        return response_message_utils(
            errors="Missing or invalid Authorization header",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Extract the token part from the Authorization header
        auth_header_token = auth_header.split(' ')[1]
    except IndexError:
        return response_message_utils(
            message="Malformed Authorization header",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        #parse the token using AccessToken
        access_token = AccessToken(auth_header_token)

        #extract the user_id claim, convert to string and remove hyphens
        return str(access_token["user_id"])
    except TokenError as e:
        #handle invalid or expired tokens by returning a 401 Unauthorized
        return response_message_utils(
            errors="Expired or invalid token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):

        # Handle none, null or empty string
        if data in (None, ""):
            return None

        if isinstance(data, six.string_types) and data.startswith(("https://")):
            try:

                response = requests.get(data, timeout=10)
                response.raise_for_status()

                buffer = BytesIO(response.content)

                # Use Pillow to validate the image
                ImageFile.LOAD_TRUNCATED_IMAGES = True
                image = Image.open(buffer)
                image.load()

                # Get the extension
                extension = image.format.lower()
                # Check the allowed extension
                extension = "jpg" if extension == "jpeg" else extension
                # Image file name
                file_name = f"{uuid.uuid4().hex[:12]}.{extension}"

                # Reset the pointer to read at the start again
                buffer.seek(0)
                return ContentFile(buffer.read(), name=file_name)

            except Exception as e:
                self.fail("Invalid image")

        if isinstance(data, six.string_types):
            # Debug: Print first 100 chars of input
            print(f"Input data (first 100 chars): {data[:100]}...")

            # Handle data URI
            if ';base64,' in data:
                header, data = data.split(';base64,')
                print(f"Extracted header: {header}")

            try:
                # Decoded base64
                decoded_file = base64.b64decode(data)
                print("Base64 decoded successfully")
                
                # Use a more forgiving image parser
                ImageFile.LOAD_TRUNCATED_IMAGES = True
                buffer = BytesIO(decoded_file)
                
                # Try to open the image
                try:
                    image = Image.open(buffer)
                    print(f"Image format detected: {image.format}")
                    
                    # Verify without closing
                    image.load()
                    print("Image loaded and verified")
                    
                    # Get extension
                    extension = image.format.lower()
                    extension = 'jpg' if extension == 'jpeg' else extension
                    print(f"Using extension: {extension}")
                    
                    # Reset buffer
                    buffer.seek(0)
                    file_name = f"{uuid.uuid4().hex[:12]}.{extension}"
                    return ContentFile(buffer.read(), name=file_name)
                    
                except Exception as e:
                    print(f"Image opening failed: {str(e)}")
                    self.fail('invalid_image')
                    
            except (ValueError, TypeError, binascii.Error) as e:
                print(f"Base64 decoding failed: {str(e)}")
                self.fail('invalid_image')

        return super().to_internal_value(data)
    

def decode_base64_image_from_csv(data):
    if not data:
        return None

    # Clean up any extra whitespace/newlines from CSV
    data = data.strip().replace("\n", "").replace("\r", "")

    # Handle full data URI
    if 'base64,' in data:
        try:
            _, data = data.split('base64,', 1)
        except ValueError:
            raise serializers.ValidationError("Invalid base64 image format.")

    # Fix padding
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)

    try:
        decoded = base64.b64decode(data)
    except (base64.binascii.Error, ValueError, TypeError):
        raise serializers.ValidationError("Base64 decoding failed.")

    try:
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        buffer = BytesIO(decoded)
        image = Image.open(buffer)
        image.load()

        extension = image.format.lower() if image.format else "png"
        extension = 'jpg' if extension == 'jpeg' else extension

        buffer.seek(0)
        file_name = f"{uuid.uuid4().hex[:12]}.{extension}"
        return ContentFile(buffer.read(), name=file_name)

    except Exception as e:
        print("BAD IMAGE BASE64:", data[:100])
        raise serializers.ValidationError(f"Invalid image file: {e}")
           


def split_ids_and_slugs(ids_or_no):
    valid_uuids = []
    valid_slugs = []

    for val in ids_or_no:
            try:
                valid_uuids.append(uuid.UUID(str(val)))
            except (ValueError, TypeError, AttributeError):
                valid_slugs.append(val)

    return valid_uuids, valid_slugs


def to_snake_case(name):
    # Inserts underscore before each capital letter (except the first one)
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
