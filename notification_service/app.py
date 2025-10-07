#!/usr/bin/env python3
"""
Notification Service API - Port 8002
Independent notification microservice with REST API
"""

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Notification service configuration
NOTIFICATION_CONFIG = {
    'database_url': os.getenv('DATABASE_URL', 'sqlite:///notifications.db'),
    'websocket_enabled': os.getenv('WEBSOCKET_ENABLED', 'true').lower() == 'true',
    'max_notifications_per_minute': int(os.getenv('MAX_NOTIFICATIONS_PER_MINUTE', 100)),
    'retention_days': int(os.getenv('NOTIFICATION_RETENTION_DAYS', 30))
}

# Global notification service instance
notification_service = None

def init_notification_service():
    """Initialize the notification service"""
    global notification_service
    try:
        from .notification_service import NotificationService
        notification_service = NotificationService(NOTIFICATION_CONFIG)
        success = notification_service.start()
        if success:
            logger.info("✅ Notification service initialized successfully")
        else:
            logger.error("❌ Failed to initialize notification service")
        return success
    except Exception as e:
        logger.error(f"❌ Error initializing notification service: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if notification_service:
            health = notification_service.health_check()
            return jsonify({
                'status': 'success',
                'service': 'notification_service',
                'port': 8002,
                'health': health,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'service': 'notification_service',
                'port': 8002,
                'error': 'Notification service not initialized',
                'timestamp': datetime.now().isoformat()
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'service': 'notification_service',
            'port': 8002,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/send-notification', methods=['POST'])
def send_notification():
    """Send notification endpoint"""
    try:
        if not notification_service:
            return jsonify({
                'status': 'error',
                'message': 'Notification service not available'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['user_id', 'title', 'message']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Create notification task
        from .notification_service import NotificationTask
        notification_task = NotificationTask(
            user_id=data['user_id'],
            title=data['title'],
            message=data['message'],
            notification_type=data.get('type', 'info'),
            priority=data.get('priority', 'normal'),
            platform=data.get('platform', 'web'),
            module=data.get('module', 'system'),
            action_url=data.get('action_url'),
            action_text=data.get('action_text'),
            meta_data=data.get('meta_data', {})
        )
        
        # Send notification
        success = notification_service.send_notification(notification_task)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Notification sent',
                'notification_id': notification_task.id,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send notification',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Error in send_notification endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/notifications/<user_id>', methods=['GET'])
def get_user_notifications(user_id):
    """Get notifications for a specific user"""
    try:
        if not notification_service:
            return jsonify({
                'status': 'error',
                'message': 'Notification service not available'
            }), 503
        
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        # Get notifications
        notifications = notification_service.get_user_notifications(
            user_id=user_id,
            limit=limit,
            offset=offset,
            unread_only=unread_only
        )
        
        return jsonify({
            'status': 'success',
            'notifications': notifications,
            'user_id': user_id,
            'limit': limit,
            'offset': offset,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting user notifications: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/notifications/<notification_id>/mark-read', methods=['PUT'])
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        if not notification_service:
            return jsonify({
                'status': 'error',
                'message': 'Notification service not available'
            }), 503
        
        success = notification_service.mark_as_read(notification_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Notification marked as read',
                'notification_id': notification_id,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to mark notification as read',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get notification service metrics"""
    try:
        if notification_service:
            metrics = notification_service.get_metrics()
            return jsonify({
                'status': 'success',
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Notification service not available'
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/config', methods=['GET'])
def get_config():
    """Get notification service configuration (non-sensitive)"""
    try:
        safe_config = {
            'service_name': 'notification_service',
            'port': 8002,
            'websocket_enabled': NOTIFICATION_CONFIG['websocket_enabled'],
            'max_notifications_per_minute': NOTIFICATION_CONFIG['max_notifications_per_minute'],
            'retention_days': NOTIFICATION_CONFIG['retention_days']
        }
        return jsonify({
            'status': 'success',
            'config': safe_config,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Notification Service on port 8002...")
    print("=" * 50)
    
    # Initialize notification service
    if init_notification_service():
        print("✅ Notification service ready")
        print("📡 API Endpoints:")
        print("   POST /send-notification")
        print("   GET  /notifications/<user_id>")
        print("   PUT  /notifications/<id>/mark-read")
        print("   GET  /health")
        print("   GET  /metrics")
        print("   GET  /config")
        print("")
        print("🌐 Access: http://localhost:8002")
        print("=" * 50)
        
        # Run Flask app
        app.run(
            host='0.0.0.0',
            port=8002,
            debug=False,
            threaded=True
        )
    else:
        print("❌ Failed to start notification service")
        exit(1)

