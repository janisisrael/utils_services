"""
Utils_services - Separated Notification Architecture
Provides email and push notification services with queue management
"""

# Version
__version__ = "1.0.0"

# Make main classes available at package level
from .dispatcher.notification_dispatcher import NotificationDispatcher
from .email_service.email_service import EmailService, EmailTask
from .notification_service.notification_service import NotificationService, PushNotificationTask
from .shared.base_service import BaseNotificationService, NotificationTask, ServiceRegistry

# Convenience functions for easy integration
def create_dispatcher(email_config: dict, notification_config: dict) -> NotificationDispatcher:
    """Create and initialize a notification dispatcher"""
    dispatcher = NotificationDispatcher()
    
    if dispatcher.initialize(email_config, notification_config):
        return dispatcher
    else:
        raise RuntimeError("Failed to initialize notification dispatcher")

def send_winner_notification(winner_data: dict, 
                           email_config: dict = None, 
                           notification_config: dict = None) -> str:
    """Quick function to send a winner notification"""
    
    # Use provided configs or defaults
    if not email_config:
        email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'max_emails_per_minute': 60
        }
    
    if not notification_config:
        notification_config = {
            'store_in_database': True,
            'send_via_websocket': True,
            'max_notifications_per_user_per_hour': 100
        }
    
    dispatcher = create_dispatcher(email_config, notification_config)
    
    try:
        dispatch_id = dispatcher.dispatch_winner_notification(winner_data)
        return dispatch_id
    finally:
        dispatcher.shutdown()

# Package info
__all__ = [
    'NotificationDispatcher',
    'EmailService',
    'EmailTask', 
    'NotificationService',
    'PushNotificationTask',
    'BaseNotificationService',
    'NotificationTask',
    'ServiceRegistry',
    'create_dispatcher',
    'send_winner_notification'
]

