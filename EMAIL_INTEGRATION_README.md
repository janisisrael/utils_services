# 📧 Utils_services Email Integration for Phase 1

This directory contains a **drop-in replacement** for Phase 1's email system that provides enhanced features without requiring any changes to Phase 1 code.

## 🚀 Quick Start

### 1. Environment Setup

Set these environment variables in your Phase 1 `.env` file:

```bash
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=noreply@thesantris.com
SENDER_NAME=Lotto Command Center

# Optional Configuration
MAX_EMAILS_PER_MINUTE=100
EMAIL_ENABLE_TRACKING=true
EMAIL_FALLBACK_TO_PHASE1=true
```

### 2. Integration Options

#### Option A: Use the Adapter (Recommended)
Copy `email_adapter.py` to `Phase1/src/services/notification/` and update your imports:

```python
# In your Phase 1 code, replace:
from services.notification.email import send_email

# With:
from services.notification.email_adapter import send_email
```

#### Option B: Direct Integration
Import directly from Utils_services:

```python
import sys
sys.path.append('../Utils_services')
from phase1_integration import send_email, send_email_async
```

## ✨ Features

### Enhanced Email Service
- **Queue Management**: Automatic email queuing with retry logic
- **Rate Limiting**: Prevents email spam and respects SMTP limits
- **Tracking**: Track email delivery status and failures
- **Templates**: Professional HTML email templates
- **Async Processing**: Non-blocking email sending
- **Fallback**: Automatic fallback to Phase 1 email system

### Compatibility
- **Same Interface**: Uses the exact same data format as Phase 1
- **No Code Changes**: Drop-in replacement for existing functions
- **Backward Compatible**: Falls back to Phase 1 if Utils_services fails
- **Zero Downtime**: Can be deployed without stopping Phase 1

## 📁 File Structure

```
Utils_services/
├── phase1_integration.py      # Main integration layer
├── email_adapter.py           # Simple adapter for Phase 1
├── config.py                 # Configuration management
├── phase1_integration_example.py  # Usage examples
└── README.md                 # This file
```

## 🔧 Usage Examples

### Basic Winner Notification

```python
from phase1_integration import send_email

# Same data format as Phase 1
winner_data = {
    "user_email": "winner@example.com",
    "user_name": "John Doe",
    "game": "Lotto 6/49",
    "draw_date": "2025-10-06",
    "ticket_number": "123456789",
    "ticket_id": "12345",
    "winners": {
        "Lotto 6/49": [{
            "matched_numbers": [1, 2, 3, 4, 5, 6],
            "prize_amount": "$5,000",
            "prize_category": "3 of 6"
        }]
    }
}

# Send email (same interface as Phase 1)
success = send_email(winner_data)
```

### Async Email with Tracking

```python
from phase1_integration import send_email_async, get_email_status

# Send email asynchronously
tracking_id = send_email_async(winner_data)

# Check status later
status = get_email_status(tracking_id)
print(f"Email status: {status['status']}")
```

### New Draw Results Notification

```python
from phase1_integration import send_new_draw_notification

success = send_new_draw_notification(
    user_email="player@example.com",
    game="Lotto Max",
    draw_date="2025-10-06",
    winning_numbers="01, 15, 23, 31, 42, 47, 49",
    jackpot_amount="$50,000,000"
)
```

## 🔍 Monitoring and Health Checks

### Check Service Status

```python
from phase1_integration import health_check

health = health_check()
print(f"Email service status: {health['status']}")
```

### Service Status Response

```json
{
    "status": "healthy",
    "service": "Utils_services",
    "email_service": true,
    "fallback": "Phase 1 email system"
}
```

## 🛠️ Configuration Options

### Email Service Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_SERVER` | smtp.gmail.com | SMTP server hostname |
| `SMTP_PORT` | 587 | SMTP server port |
| `SMTP_USERNAME` | - | SMTP username |
| `SMTP_PASSWORD` | - | SMTP password/app password |
| `SENDER_EMAIL` | - | From email address |
| `SENDER_NAME` | Lotto Command Center | From name |
| `MAX_EMAILS_PER_MINUTE` | 60 | Rate limiting |
| `EMAIL_ENABLE_TRACKING` | true | Enable delivery tracking |
| `EMAIL_FALLBACK_TO_PHASE1` | true | Fallback to Phase 1 |

### Queue Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `EMAIL_QUEUE_MAX_SIZE` | 1000 | Maximum queue size |
| `EMAIL_QUEUE_RETRY_ATTEMPTS` | 3 | Retry attempts |
| `EMAIL_QUEUE_RETRY_DELAY` | 60 | Retry delay (seconds) |

## 🔄 Migration Strategy

### Phase 1: Test Integration
1. Set up environment variables
2. Copy `email_adapter.py` to Phase 1
3. Test with a few emails
4. Monitor logs and performance

### Phase 2: Gradual Rollout
1. Update imports in non-critical email functions
2. Monitor email delivery rates
3. Compare performance with Phase 1 system
4. Gradually migrate all email functions

### Phase 3: Full Migration
1. Replace all Phase 1 email calls
2. Remove old email system dependencies
3. Optimize configuration for production

## 🚨 Troubleshooting

### Common Issues

#### 1. Utils_services Not Available
```
Error: Utils_services not available, falling back to Phase 1 email
```
**Solution**: Check that Utils_services is in the correct path and all dependencies are installed.

#### 2. SMTP Authentication Failed
```
Error: Failed to initialize Utils_services email service
```
**Solution**: Verify SMTP credentials and ensure app passwords are used for Gmail.

#### 3. Email Queue Full
```
Error: Email queue is full
```
**Solution**: Increase `EMAIL_QUEUE_MAX_SIZE` or check for email processing issues.

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('utils_services').setLevel(logging.DEBUG)
```

### Health Check Endpoint

Add this to your Phase 1 app for monitoring:

```python
@app.route('/email-health', methods=['GET'])
def email_health():
    from utils_services.phase1_integration import health_check
    return jsonify(health_check())
```

## 📊 Performance Benefits

- **Faster Processing**: Async email sending doesn't block ticket processing
- **Better Reliability**: Automatic retry logic and fallback mechanisms
- **Rate Limiting**: Prevents SMTP server overload
- **Tracking**: Monitor email delivery success rates
- **Professional Templates**: Better-looking emails for users

## 🔒 Security Features

- **App Passwords**: Uses app-specific passwords for Gmail
- **TLS Encryption**: All emails sent over encrypted connections
- **Rate Limiting**: Prevents email abuse
- **Error Handling**: Secure error logging without exposing sensitive data

## 📞 Support

For issues or questions:
1. Check the logs for error messages
2. Verify environment variables are set correctly
3. Test with the example scripts in `phase1_integration_example.py`
4. Check the health status endpoint

## 🎯 Next Steps

1. **Test the integration** with your current Phase 1 setup
2. **Set up monitoring** to track email delivery rates
3. **Configure production settings** for optimal performance
4. **Plan the migration** timeline based on your needs

---

**Note**: This integration is designed to be completely backward compatible. If anything goes wrong, the system will automatically fall back to Phase 1's original email system.

