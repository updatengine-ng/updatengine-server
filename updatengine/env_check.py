import os
import sys
import logging

logger = logging.getLogger(__name__)

def check_required_settings(settings):
    """
    Validates that critical environment variables are set and provides warnings for security.
    """
    required_vars = [
        'SECRET_KEY',
        'ALLOWED_HOSTS',
        'DATABASES',
    ]
    
    missing = []
    for var in required_vars:
        if not hasattr(settings, var) or not getattr(settings, var):
            missing.append(var)
            
    if missing:
        error_msg = f"CRITICAL: Missing required settings in environment: {', '.join(missing)}"
        print(error_msg, file=sys.stderr)
        # We don't exit here to allow migrations or other management commands that might not need full settings
        # but in production wsgi this should be treated as a failure.

    # Security warnings
    if getattr(settings, 'DEBUG', False):
        logger.warning("SECURITY WARNING: DEBUG mode is enabled. Do not use this in production!")
        
    if getattr(settings, 'SECRET_KEY', '') == '${SECRET_KEY}' or 'django-insecure' in getattr(settings, 'SECRET_KEY', ''):
        logger.warning("SECURITY WARNING: SECRET_KEY is using a placeholder or insecure value!")

    # Database check
    db_config = getattr(settings, 'DATABASES', {}).get('default', {})
    if db_config.get('ENGINE') == 'django.db.backends.mysql':
        if db_config.get('PASSWORD') == '${DB_PASSWORD}':
             logger.warning("DATABASE WARNING: Using placeholder DB_PASSWORD!")
