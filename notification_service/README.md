# 📬 Notification Service

**Port:** 7002  
**Type:** Microservice  
**Status:** Ready for deployment

---

## Purpose

Dedicated push notification service with WebSocket support for real-time notifications.

---

## Features

✅ In-app notifications  
✅ WebSocket delivery (real-time)  
✅ Database storage  
✅ Queue management  
✅ Retry logic  
✅ Priority handling  
✅ Rate limiting  
✅ RESTful API

---

## API Endpoints

```
GET  /health                              - Health check
POST /send-notification                   - Send new notification
GET  /notifications/<user_id>             - Get user notifications
PUT  /notifications/<id>/mark-read        - Mark as read
GET  /metrics                             - Service metrics
GET  /config                              - Service configuration
```

---

## Configuration

Environment variables:

```bash
DATABASE_URL=mysql://user:pass@localhost/lotto_cc
WEBSOCKET_ENABLED=true
MAX_NOTIFICATIONS_PER_MINUTE=100
NOTIFICATION_RETENTION_DAYS=30
```

---

## Running Locally

```bash
cd Utils_services/notification_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

**Access:** http://localhost:7002

---

## Dependencies

- Flask
- Flask-CORS
- Flask-SocketIO (for WebSocket)
- MySQL connector
- Queue manager (shared module)

---

## Deployment

### Option 1: Standalone Service
Deploy as separate microservice on port 7002.

### Option 2: Integrate into Phase1
Merge features into Phase1's existing notification system.

**Current Recommendation:** Deploy standalone for WebSocket real-time features.

---

## Integration with Phase1

Phase1 can call this service via HTTP:

```python
import requests

# Send notification
response = requests.post('http://localhost:7002/send-notification', json={
    'user_id': 123,
    'title': 'New Draw Results',
    'message': 'Check your tickets!',
    'type': 'info',
    'priority': 'high'
})
```

---

**Last Updated:** 2025-10-12  
**Port:** 7002 (standardized)  
**Status:** ⏸️ Not deployed (ready when needed)
