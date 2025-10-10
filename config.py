"""
Configuration file for Utils_services Email Integration
This file contains the configuration settings for the email service integration.
"""

import os
from typing import Dict, Any

def get_email_config() -> Dict[str, Any]:
    """
    Get email service configuration from environment variables
    
    Returns:
        dict: Email service configuration
    """
    return {
        # SMTP Configuration
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'smtp_username': os.getenv('SMTP_USERNAME'),
        'smtp_password': os.getenv('SMTP_PASSWORD'),
        'sender_email': os.getenv('SENDER_EMAIL'),
        'sender_name': os.getenv('SENDER_NAME', 'Lotto Command Center'),
        'use_tls': os.getenv('USE_TLS', 'true').lower() == 'true',
        
        # Rate Limiting
        'max_emails_per_minute': int(os.getenv('MAX_EMAILS_PER_MINUTE', 60)),
        
        # Queue Configuration
        'queue_max_size': int(os.getenv('EMAIL_QUEUE_MAX_SIZE', 1000)),
        'queue_retry_attempts': int(os.getenv('EMAIL_QUEUE_RETRY_ATTEMPTS', 3)),
        'queue_retry_delay': int(os.getenv('EMAIL_QUEUE_RETRY_DELAY', 60)),  # seconds
        
        # Monitoring
        'enable_tracking': os.getenv('EMAIL_ENABLE_TRACKING', 'true').lower() == 'true',
        'tracking_retention_days': int(os.getenv('EMAIL_TRACKING_RETENTION_DAYS', 7)),
        
        # Fallback Configuration
        'fallback_to_phase1': os.getenv('EMAIL_FALLBACK_TO_PHASE1', 'true').lower() == 'true',
        'fallback_on_error': os.getenv('EMAIL_FALLBACK_ON_ERROR', 'true').lower() == 'true'
    }

def get_notification_config() -> Dict[str, Any]:
    """
    Get notification service configuration
    
    Returns:
        dict: Notification service configuration
    """
    return {
        # WebSocket Configuration
        'websocket_enabled': os.getenv('WEBSOCKET_ENABLED', 'true').lower() == 'true',
        'websocket_port': int(os.getenv('WEBSOCKET_PORT', 8002)),
        
        # Push Notification Configuration
        'push_enabled': os.getenv('PUSH_NOTIFICATIONS_ENABLED', 'false').lower() == 'true',
        'fcm_server_key': os.getenv('FCM_SERVER_KEY'),
        
        # Database Configuration
        'notification_storage': os.getenv('NOTIFICATION_STORAGE', 'database'),
        'redis_enabled': os.getenv('REDIS_ENABLED', 'false').lower() == 'true',
        'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379')
    }

# Default configuration for development
DEFAULT_CONFIG = {
    'email': get_email_config(),
    'notification': get_notification_config()
}

# Production configuration template
PRODUCTION_CONFIG_TEMPLATE = """
# Production Environment Variables for Utils_services Email Integration

# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=noreply@thesantris.com
SENDER_NAME=Lotto Command Center

# Email Service Configuration
MAX_EMAILS_PER_MINUTE=100
EMAIL_QUEUE_MAX_SIZE=5000
EMAIL_QUEUE_RETRY_ATTEMPTS=5
EMAIL_QUEUE_RETRY_DELAY=30

# Tracking and Monitoring
EMAIL_ENABLE_TRACKING=true
EMAIL_TRACKING_RETENTION_DAYS=30

# Fallback Configuration
EMAIL_FALLBACK_TO_PHASE1=true
EMAIL_FALLBACK_ON_ERROR=true

# TLS Configuration
USE_TLS=true
"""




