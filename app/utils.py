"""
Utility functions for the Jiyash application
"""
import re
import html
from django.utils.html import escape
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import logging

logger = logging.getLogger(__name__)


def sanitize_input(text, max_length=None):
    """
    Sanitize user input to prevent XSS and other attacks
    """
    if not text:
        return ""
    
    # Convert to string and strip whitespace
    text = str(text).strip()
    
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    # HTML escape the content
    text = escape(text)
    
    return text


def validate_email_address(email):
    """
    Validate email address format
    """
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def clean_phone_number(phone):
    """
    Clean and validate phone number
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters except +
    phone = re.sub(r'[^\d+]', '', str(phone))
    
    # Basic validation - should be between 10-15 digits
    digits_only = re.sub(r'[^\d]', '', phone)
    if len(digits_only) < 10 or len(digits_only) > 15:
        raise ValidationError("Phone number must be between 10-15 digits")
    
    return phone


def log_security_event(event_type, user_id=None, ip_address=None, details=None):
    """
    Log security-related events
    """
    log_message = f"SECURITY EVENT: {event_type}"
    if user_id:
        log_message += f" | User: {user_id}"
    if ip_address:
        log_message += f" | IP: {ip_address}"
    if details:
        log_message += f" | Details: {details}"
    
    logger.warning(log_message)


def get_client_ip(request):
    """
    Get the client's IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def rate_limit_key(request, identifier):
    """
    Generate a rate limiting key based on IP and identifier
    """
    ip = get_client_ip(request)
    return f"rate_limit:{identifier}:{ip}"


class SecurityMixin:
    """
    Mixin class to add security features to views
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Log the request for security monitoring
        ip = get_client_ip(request)
        logger.info(f"Request: {request.method} {request.path} from {ip}")
        
        return super().dispatch(request, *args, **kwargs)
    
    def handle_security_error(self, request, error_type, details=None):
        """
        Handle security-related errors
        """
        ip = get_client_ip(request)
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        
        log_security_event(error_type, user_id, ip, details)
        
        # You can add additional security measures here like:
        # - Rate limiting
        # - IP blocking
        # - User account suspension
