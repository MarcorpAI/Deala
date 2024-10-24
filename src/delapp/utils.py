import re
from django.core.exceptions import ValidationError

def sanitize_input(query):
    # Remove any potential HTML or script tags
    sanitized = re.sub(r'<[^>]*?>', '', query)
    # Remove any non-alphanumeric characters except spaces and common punctuation
    sanitized = re.sub(r'[^\w\s.,?!-]', '', sanitized)
    return sanitized.strip()

def validate_query(query):
    if not query:
        raise ValidationError("Query cannot be empty.")
    if len(query) > 500:  # Adjust max length as needed
        raise ValidationError("Query is too long. Please limit to 500 characters.")