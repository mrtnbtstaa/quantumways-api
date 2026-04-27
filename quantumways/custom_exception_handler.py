from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled, PermissionDenied
from rest_framework import status
from quantumways.utils import response_message_utils
from rest_framework.exceptions import ParseError
#custom exception handler
def custom_exception_handler(exc, context):

    if isinstance(exc, Throttled):
        return response_message_utils(
            message="You are sending too many requests. Please try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    if isinstance(exc, ParseError):
        return response_message_utils(
            message="Invalid JSON format in request body",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    response = exception_handler(exc, context)

    if response and isinstance(response.data, dict):
        data = response.data
        # Prioritize non_field_errors if present
        if "non_field_errors" in data and isinstance(data["non_field_errors"], list):
            response.data = {"message": data["non_field_errors"][0]} #flatten the error
        else:
            for key, value in data.items():
                if isinstance(value, list) and len(value) == 1:
                    response.data = {"message": value[0]} #flatten the error
                    break
        return response
    
    # If nothing matched treat the error as 500 server error
    return response_message_utils(
        message=f"Something went wrong while processing your request: {exc}",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

