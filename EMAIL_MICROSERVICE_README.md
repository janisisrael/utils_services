# 📧 Email Microservice - Port 8001

A standalone email microservice for all phases of the Lotto Command Center with SendGrid integration, free tier monitoring, and automatic fallback capabilities.

## 🚀 Quick Start

### 1. **Run Setup Script**
```bash
cd Utils_services
python setup_email_microservice.py
```

### 2. **Configure Environment**
```bash
# Edit .env with your SendGrid API key
nano .env
```

### 3. **Start the Service**
```bash
# Option 1: Manual start
./start_email_microservice.sh

# Option 2: Systemd service
sudo systemctl enable email-microservice
sudo systemctl start email-microservice
```

### 4. **Integrate with Phase 1**
```python
# Replace Phase 1 email imports
from utils_services.email_microservice_client import send_email
```

## 🌐 Port Configuration

| Service | Port | Description |
|---------|------|-------------|
| **Email Microservice** | **8001** | Standalone email service |
| Phase 1 (Main App) | 6001 | Lottery processing |
| Frontend | 8080 | Vue.js application |

## ✨ Features

### **📊 Free Tier Monitoring**
- **Daily tracking** - Counts emails sent per day
- **Warning system** - Alerts at 80%, 90%, 95% usage
- **Automatic fallback** - Switches to Phase 1 at 100% limit
- **Admin notifications** - Email alerts for critical warnings
- **Usage analytics** - Track daily and total email usage

### **🔄 Automatic Fallback**
- **Seamless switching** - Falls back to Phase 1 email system
- **Zero downtime** - No interruption to email service
- **Error handling** - Handles SendGrid API failures gracefully
- **Dual service** - Uses both SendGrid and Phase 1 as backup

### **📈 Professional Email Templates**
- **HTML emails** - Professional, responsive design
- **Plain text fallback** - For email clients that don't support HTML
- **Branded templates** - Consistent Lotto Command Center branding
- **Mobile-friendly** - Responsive design for all devices

## 🔧 Configuration

### **Environment Variables (.env)**
```bash
# Required
SENDGRID_API_KEY=your-sendgrid-api-key-here
SENDER_EMAIL=noreply@thesantris.com
SENDER_NAME=Lotto Command Center

# Optional
SENDGRID_FALLBACK_TO_PHASE1=true
ADMIN_EMAIL=admin@thesantris.com
SENDGRID_DAILY_LIMIT=100
SENDGRID_WARNING_THRESHOLDS=80,90,95
```

### **SendGrid Setup**
1. **Sign up** at https://sendgrid.com
2. **Create API key** in SendGrid dashboard
3. **Verify sender email** in SendGrid settings
4. **Add API key** to .env file

## 📊 API Endpoints

### **Health Check**
```bash
GET http://localhost:8001/health
```
**Response:**
```json
{
  "status": "healthy",
  "service": "email_microservice",
  "sendgrid_available": true,
  "usage_status": {...},
  "api_key_configured": true,
  "port": 8001
}
```

### **Usage Status**
```bash
GET http://localhost:8001/usage
```
**Response:**
```json
{
  "current_date": "2025-01-06",
  "emails_sent_today": 45,
  "daily_limit": 100,
  "remaining": 55,
  "percentage_used": 45.0,
  "can_send_more": true,
  "total_emails_sent": 1250,
  "warnings_sent_today": 0
}
```

### **Send Email**
```bash
POST http://localhost:8001/send
Content-Type: application/json

{
  "recipient": "user@example.com",
  "subject": "Test Email",
  "html_content": "<h1>Hello World</h1>",
  "plain_text": "Hello World",
  "tracking_id": "optional-tracking-id"
}
```

### **Send Winner Notification**
```bash
POST http://localhost:8001/send-winner
Content-Type: application/json

{
  "user_email": "winner@example.com",
  "user_name": "John Doe",
  "game": "Lotto 6/49",
  "draw_date": "2025-01-06",
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
```

## 🔄 Integration Examples

### **Phase 1 Integration**
```python
from utils_services.email_microservice_client import send_email

# Same interface as Phase 1
result = {
    "user_email": "winner@example.com",
    "user_name": "John Doe",
    "game": "Lotto 6/49",
    "winners": {...}
}

success = send_email(result)
```

### **Direct API Integration**
```python
import requests

# Send winner notification
response = requests.post('http://localhost:8001/send-winner', json=result)
if response.status_code == 200:
    print("Email sent successfully")
```

### **Usage Monitoring**
```python
from utils_services.email_microservice_client import get_email_usage

usage = get_email_usage()
if usage['percentage_used'] > 80:
    print("⚠️ Approaching daily limit!")
```

## 🚨 Warning System

### **Warning Thresholds**
- **80%** (80 emails) - First warning
- **90%** (90 emails) - Second warning  
- **95%** (95 emails) - Final warning
- **100%** (100 emails) - Automatic fallback to Phase 1

### **Warning Messages**
```
⚠️ Email usage warning: 80/100 emails sent today (80% of limit)
⚠️ Email usage warning: 90/100 emails sent today (90% of limit)
⚠️ Email usage warning: 95/100 emails sent today (95% of limit)
🚨 Email daily limit reached! (100/100)
```

### **Admin Notifications**
When the daily limit is reached, an email is sent to `ADMIN_EMAIL` with:
- Current usage statistics
- Time of limit reached
- Recommended actions
- Usage history

## 🔄 Fallback System

### **Automatic Fallback Triggers**
1. **Daily limit reached** (100 emails)
2. **SendGrid API failure**
3. **SendGrid service unavailable**
4. **Configuration errors**

### **Fallback Process**
1. **Log warning** about fallback
2. **Switch to Phase 1** email system
3. **Continue processing** emails normally
4. **Track usage** for monitoring

## 📁 File Structure

```
Utils_services/
├── email_microservice.py              # Main microservice (Port 8001)
├── email_microservice_client.py       # Client library for Phase 1
├── setup_email_microservice.py        # Setup script
├── start_email_microservice.sh        # Startup script
├── email-microservice.service         # Systemd service file
├── sendgrid_env_template.txt          # Environment template
├── email_usage.json                   # Usage tracking (auto-created)
└── README.md                          # This file
```

## 🛠️ Service Management

### **Manual Start/Stop**
```bash
# Start
./start_email_microservice.sh

# Stop
pkill -f email_microservice.py
```

### **Systemd Service**
```bash
# Enable service
sudo systemctl enable email-microservice

# Start service
sudo systemctl start email-microservice

# Stop service
sudo systemctl stop email-microservice

# Check status
sudo systemctl status email-microservice

# View logs
journalctl -u email-microservice -f
```

### **Service Status**
```bash
# Check if running
ps aux | grep email_microservice

# Check port
netstat -tuln | grep 8001

# Health check
curl http://localhost:8001/health
```

## 📈 Expected Results

### **Before Integration:**
- ❌ 70-80% delivery rate
- ❌ High spam folder placement
- ❌ SMTP server overload
- ❌ No delivery tracking
- ❌ No usage monitoring

### **After Integration:**
- ✅ 99.9% delivery rate (SendGrid)
- ✅ Inbox placement
- ✅ Reliable delivery
- ✅ Full usage tracking
- ✅ Professional templates
- ✅ Automatic fallback
- ✅ Zero downtime
- ✅ Separate microservice architecture

## 🔧 Troubleshooting

### **Common Issues**

#### **1. Service Not Starting**
```
Error: Cannot connect to email microservice
```
**Solution**: Check if service is running on port 8001

#### **2. SendGrid Not Available**
```
Error: SendGrid not available
```
**Solution**: Check .env file and API key configuration

#### **3. Port Already in Use**
```
Error: Port 8001 is already in use
```
**Solution**: Stop existing service or change port

#### **4. Permission Denied**
```
Error: Permission denied
```
**Solution**: Check file permissions and user ownership

### **Debug Mode**
```bash
# Run in debug mode
python email_microservice.py

# Check logs
tail -f email_microservice.log

# Systemd logs
journalctl -u email-microservice -f
```

## 📞 Support

### **Monitoring Endpoints**
```bash
# Health check
curl http://localhost:8001/health

# Usage status
curl http://localhost:8001/usage
```

### **Log Files**
- **Service logs**: `email_microservice.log`
- **Systemd logs**: `journalctl -u email-microservice`
- **Usage tracking**: `email_usage.json`

## 🎯 Next Steps

1. **Test integration** with a few emails
2. **Monitor usage** for a few days
3. **Set up admin notifications**
4. **Consider upgrading** SendGrid plan if needed
5. **Implement additional monitoring** if required

## 🌐 Multi-Phase Support

This microservice is designed to support **all phases** of the Lotto Command Center:

- **Phase 1**: Lottery processing and winner notifications
- **Phase 2**: Additional features and services
- **Phase 3**: Future enhancements and integrations

Each phase can use the same email microservice by calling the API endpoints or using the client library.

---

**Note**: This microservice is designed to be completely backward compatible. If anything goes wrong, the system automatically falls back to Phase 1's original email system.


