# Notification Microservice v2

## Overview

The Notification Microservice v2 is a standalone service that provides real-time WebSocket notifications and REST API endpoints for the Lotto Command Center. It runs on **port 7002** and is completely separate from the existing working code to ensure no interference.

## ✅ **No Static/Dummy Data**

The notification system is **100% dynamic** and uses real user data:

- **User IDs**: Retrieved from actual database queries
- **Email Addresses**: Fetched from the `users` table
- **User Names**: Retrieved from the `profile` table
- **Notification Content**: Generated from real ticket and draw data
- **No Hardcoded Values**: All data comes from the database

## Features

### 🔌 **WebSocket Real-time Notifications**
- Real-time notifications via WebSocket connections
- User-specific notification rooms
- Offline notification queuing
- Automatic reconnection handling

### 🌐 **REST API Endpoints**
- Send notifications to specific users
- Broadcast notifications to multiple users
- Health and status monitoring
- Connection management
- Queue management

### 🎯 **Phase 1 Integration**
- Direct integration with Phase 1 winner notifications
- Automatic winner notification handling
- Seamless email + notification flow

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Phase 1       │    │  Notification    │    │   Frontend      │
│   Backend       │───▶│  Microservice    │───▶│   (WebSocket)   │
│                 │    │  (Port 7002)     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Database      │    │   Email Service  │    │   Mobile App    │
│   (Users/       │    │   (Port 7001)    │    │   (WebSocket)   │
│   Notifications)│    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Installation & Setup

### 1. **Start the Service**
```bash
cd Utils_services
./start_notification_microservice_v2.sh
```

### 2. **Test the Service**
```bash
python3 test_notification_microservice_v2.py
```

### 3. **Check Service Status**
```bash
curl http://localhost:7002/health
```

## API Endpoints

### **Health & Status**
- `GET /health` - Health check
- `GET /status` - Detailed service status
- `GET /connections` - Active WebSocket connections

### **Notifications**
- `POST /send` - Send notification to specific user
- `POST /broadcast` - Broadcast notification to multiple users
- `POST /phase1/winner` - Handle winner notifications from Phase 1

### **Queue Management**
- `GET /queue/<user_id>` - Get queued notifications for user
- `DELETE /queue/<user_id>` - Clear queued notifications for user

## WebSocket Events

### **Client Events**
- `join_user` - Join user's notification room
- `leave_user` - Leave user's notification room

### **Server Events**
- `new_notification` - New notification received
- `queued_notifications` - Queued notifications when user reconnects
- `connected` - Connection established
- `disconnected` - Connection closed

## Usage Examples

### **Send Notification to User**
```bash
curl -X POST http://localhost:7002/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 8,
    "title": "🎉 You Won!",
    "body": "Congratulations! Your ticket won $50,000!",
    "type": "success",
    "icon": "trophy",
    "url": "/tickets/77"
  }'
```

### **Broadcast Notification**
```bash
curl -X POST http://localhost:7002/broadcast \
  -H "Content-Type: application/json" \
  -d '{
    "title": "System Maintenance",
    "body": "Scheduled maintenance in 30 minutes",
    "type": "warning",
    "icon": "maintenance"
  }'
```

### **Winner Notification from Phase 1**
```bash
curl -X POST http://localhost:7002/phase1/winner \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 8,
    "game": "Lotto 6/49",
    "draw_date": "2025-10-06",
    "ticket_number": "TEST-123456",
    "prize_amount": "$50,000",
    "ticket_id": "77"
  }'
```

## WebSocket Client Example

```javascript
// Connect to notification service
const socket = io('http://localhost:7002');

// Join user's notification room
socket.emit('join_user', { user_id: 8 });

// Listen for notifications
socket.on('new_notification', (data) => {
    console.log('New notification:', data);
    // Display notification to user
    showNotification(data.title, data.body, data.type);
});

// Handle queued notifications
socket.on('queued_notifications', (data) => {
    console.log('Queued notifications:', data.notifications);
    // Display all queued notifications
    data.notifications.forEach(notification => {
        showNotification(notification.title, notification.body, notification.type);
    });
});
```

## Integration with Phase 1

The notification service integrates seamlessly with Phase 1:

1. **Winner Detection**: Phase 1 detects winning tickets
2. **Email + Notification**: Both email and notification are sent
3. **Real-time Updates**: Users get instant notifications
4. **Offline Support**: Notifications are queued for offline users

## Monitoring & Logs

### **Service Logs**
```bash
tail -f Utils_services/notification_microservice_v2.log
```

### **Health Monitoring**
```bash
curl http://localhost:7002/health
```

### **Connection Status**
```bash
curl http://localhost:7002/connections
```

## Security Features

- **CORS Protection**: Configurable allowed origins
- **Input Validation**: All inputs are validated
- **Error Handling**: Comprehensive error handling
- **Rate Limiting**: Built-in protection against abuse
- **Queue Limits**: Maximum 50 notifications per user

## Performance

- **Scalable**: Handles multiple concurrent connections
- **Efficient**: Minimal memory footprint
- **Fast**: Sub-second notification delivery
- **Reliable**: Automatic reconnection and queuing

## Troubleshooting

### **Service Won't Start**
1. Check if port 7002 is available
2. Verify Python dependencies are installed
3. Check the log file for errors

### **WebSocket Connection Issues**
1. Verify CORS settings
2. Check firewall settings
3. Ensure client is using correct URL

### **Notifications Not Received**
1. Check if user is connected via WebSocket
2. Verify user_id is correct
3. Check notification queue for offline users

## Development

### **Adding New Notification Types**
1. Update the notification templates
2. Add new endpoints if needed
3. Update the test script
4. Test thoroughly

### **Customizing Notifications**
1. Modify the notification data structure
2. Update the WebSocket payload
3. Update the frontend client code

## Support

For issues or questions:
1. Check the service logs
2. Run the test script
3. Verify all dependencies are installed
4. Check the health endpoint

---

**🎉 The Notification Microservice v2 is ready for production use!**

