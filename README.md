# 🛠️ Utils_services - Separated Notification Architecture

## 📁 Directory Structure

```
Utils_services/
├── shared/                    # Shared utilities and base classes
│   ├── base_service.py       # Base service interface
│   ├── queue_manager.py      # Generic queue management
│   ├── retry_policies.py     # Retry logic implementations
│   ├── rate_limiter.py       # Rate limiting utilities
│   └── monitoring.py         # Service monitoring and metrics
├── email_service/            # Dedicated email service
│   ├── email_service.py      # Main email service class
│   ├── email_queue.py        # Email-specific queue
│   ├── email_templates.py    # Email template management
│   ├── smtp_client.py        # SMTP client wrapper
│   └── config.py             # Email service configuration
├── notification_service/     # Dedicated push notification service
│   ├── notification_service.py  # Main notification service
│   ├── notification_queue.py    # Notification queue
│   ├── websocket_manager.py     # WebSocket handling
│   ├── database_storage.py      # Database notification storage
│   └── config.py                # Notification service configuration
├── dispatcher/               # Central notification orchestrator
│   ├── notification_dispatcher.py  # Main dispatcher
│   ├── delivery_tracker.py         # Track delivery across services
│   └── config.py                   # Dispatcher configuration
└── README.md                 # This file
```

## 🎯 Purpose

This directory contains the **new separated notification architecture** that runs alongside the existing Phase1 notification system without breaking it.

## 🔄 Migration Strategy

1. **Phase 1**: Build and test new services in Utils_services
2. **Phase 2**: Create adapter layer to connect to Phase1
3. **Phase 3**: Gradually migrate Phase1 to use new services
4. **Phase 4**: Deprecate old coupled system

## 🚀 Benefits

- **Non-breaking**: Existing system continues to work
- **Testable**: New architecture can be thoroughly tested
- **Scalable**: Services can be scaled independently
- **Future-proof**: Easy to add new notification channels

## 🔗 Integration

The new services will be accessible from Phase1 via:
```python
from Utils_services.dispatcher.notification_dispatcher import NotificationDispatcher

dispatcher = NotificationDispatcher()
dispatcher.dispatch_winner_notification(winner_data)
```

