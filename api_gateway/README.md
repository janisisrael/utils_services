# API Gateway Service

**Port:** 8000  
**Purpose:** Route traffic to microservices to reduce Phase1 load  
**Architecture:** Request proxy/load balancer

---

## Overview

The API Gateway acts as a single entry point for all microservices, routing requests to appropriate services based on URL prefixes.

```
Frontend → API Gateway (8000) → Microservices
```

---

## Route Mapping

| Prefix | Target Service | Port | Example |
|--------|---------------|------|---------|
| `/notif/*` | Notification Service | 7002 | `/notif/list` |
| `/email/*` | Email Service | 7001 | `/email/send` |
| `/pred/*` | Prediction Service | 7000 | `/pred/generate` |
| `/monitor/*` | Monitoring Service | 7003 | `/monitor/health` |
| `/p1/*` | Phase1 Backend (legacy) | 5001/6001 | `/p1/auth/login` |

---

## Installation

### Local Development

```bash
cd Utils_services/api_gateway

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

**Access:** http://localhost:8000

---

## Deployment (Production)

### 1. Upload to Server

```bash
# From local
rsync -avz --exclude 'venv' \
  Utils_services/api_gateway/ \
  ubuntu@thesantris.com:/home/ubuntu/utils_services/api_gateway/
```

### 2. Setup on Server

```bash
ssh ubuntu@thesantris.com

cd /home/ubuntu/utils_services/api_gateway

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install
pip install -r requirements.txt

# Copy production env
cp .env.production .env
```

### 3. Run in Screen

```bash
screen -S api-gateway
source venv/bin/activate
python app.py

# Detach: Ctrl+A then D
# Reattach: screen -r api-gateway
```

### 4. Configure Nginx

Add to `/etc/nginx/sites-available/lottoapp`:

```nginx
# API Gateway
location /api/ {
    proxy_pass http://localhost:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Timeouts
    proxy_connect_timeout 30s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;
}
```

Reload Nginx:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

### 5. Open Port (AWS Security Group)

Add inbound rule: `Port 8000, TCP, Source: 0.0.0.0/0`

---

## Testing

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "API Gateway",
  "version": "1.0.0",
  "services": {
    "phase1": "http://localhost:5001",
    "notification": "http://localhost:7002"
  }
}
```

### List Routes

```bash
curl http://localhost:8000/routes
```

### Test Notification Proxy

```bash
# Via Gateway
curl http://localhost:8000/notif/health

# Direct (compare)
curl http://localhost:7002/notification/health
```

---

## Environment Variables

### `.env` (Development)
```env
GATEWAY_PORT=8000
DEBUG=True
NOTIFICATION_URL=http://localhost:7002
EMAIL_URL=http://localhost:7001
PHASE1_URL=http://localhost:5001
```

### `.env.production` (Production)
```env
GATEWAY_PORT=8000
DEBUG=False
NOTIFICATION_URL=http://localhost:7002
EMAIL_URL=http://localhost:7001
PHASE1_URL=http://localhost:5001
ALLOWED_ORIGINS=https://www.thesantris.com
```

---

## Usage Examples

### Frontend Migration

**Before (Direct to Phase1):**
```javascript
axios.get('https://thesantris.com/p1/notification/list')
```

**After (Via Gateway):**
```javascript
axios.get('https://thesantris.com/api/notif/list')
```

**Benefits:**
- Reduced Phase1 load
- Service independence
- Easy to scale notifications separately

---

## Monitoring

### Check Gateway Logs

```bash
screen -r api-gateway
# View logs in real-time
```

### Check Service Health

```bash
curl http://localhost:8000/health
```

### Monitor Traffic

```bash
# Check access logs
tail -f /var/log/nginx/access.log | grep "/api/"
```

---

## Features

- [check_circle] Request proxying to microservices
- [check_circle] CORS handling
- [check_circle] Error handling (503, 504)
- [check_circle] Request/response logging
- [check_circle] Health checks
- [check_circle] Service registry
- [schedule] Rate limiting (future)
- [schedule] Authentication middleware (future)
- [schedule] Request caching (future)
- [schedule] Circuit breaker (future)

---

## Architecture Benefits

1. **Load Distribution** - Offload traffic from Phase1
2. **Service Independence** - Services can scale separately
3. **Easy Maintenance** - Change service ports without frontend updates
4. **Future-Proof** - Foundation for Phase2, mobile, web push
5. **Monitoring** - Centralized request logging

---

## Troubleshooting

### Service Unavailable (503)

**Cause:** Target service is down

**Fix:**
```bash
# Check if service is running
curl http://localhost:7002/health

# Restart service
screen -r notification-service
```

### Gateway Timeout (504)

**Cause:** Service taking too long to respond

**Fix:**
- Increase timeout in `app.py` (currently 30s)
- Check service logs for slow queries

### CORS Errors

**Cause:** Origin not in ALLOWED_ORIGINS

**Fix:** Update `.env` and restart gateway

---

## Port Allocation

| Service | Port |
|---------|------|
| Phase1 Backend | 5001/6001 |
| Prediction Scheduler | 7000 |
| Email Service | 7001 |
| Notification Service | 7002 |
| Monitoring | 7003 |
| Port Watcher | 7004 |
| **API Gateway** | **8000** |

---

**Status:** [schedule] Ready for deployment  
**Version:** 1.0.0  
**Created:** 2025-10-12

---
*API Gateway by Agimat v1.5 - Swordfish Project*
