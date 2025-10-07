#!/usr/bin/env python3
"""
Notification Microservice - Port 7002
Standalone notification service for all phases
"""

import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import threading
import time

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class NotificationService:
    """Notification service for real-time notifications"""
    
    def __init__(self):
        self.active_connections = {}
        self.user_rooms = {}
        self.notification_queue = []
        self.notification_history = []
        
    def add_connection(self, user_id: str, socket_id: str):
        """Add a new WebSocket connection"""
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(socket_id)
        logger.info(f"✅ User {user_id} connected (socket: {socket_id})")
    
    def remove_connection(self, user_id: str, socket_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            if socket_id in self.active_connections[user_id]:
                self.active_connections[user_id].remove(socket_id)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"❌ User {user_id} disconnected (socket: {socket_id})")
    
    def send_notification(self, user_id: str, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification to a specific user"""
        try:
            notification_id = f"notif_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(user_id)}"
            
            notification_data = {
                'notification_id': notification_id,
                'user_id': user_id,
                'title': notification.get('title', 'Notification'),
                'body': notification.get('body', ''),
                'type': notification.get('type', 'info'),
                'icon': notification.get('icon'),
                'url': notification.get('url'),
                'timestamp': datetime.now().isoformat(),
                'status': 'sent'
            }
            
            # Send via WebSocket if user is connected
            if user_id in self.active_connections:
                for socket_id in self.active_connections[user_id]:
                    try:
                        socketio.emit('notification', notification_data, to=socket_id)
                        notification_data['status'] = 'delivered'
                    except Exception as e:
                        logger.error(f"Failed to send notification to socket {socket_id}: {e}")
                        notification_data['status'] = 'failed'
            else:
                notification_data['status'] = 'queued'
                self.notification_queue.append(notification_data)
            
            # Add to history
            self.notification_history.append(notification_data)
            
            logger.info(f"📧 Notification sent to user {user_id}: {notification_data['title']}")
            
            return {
                'success': True,
                'notification_id': notification_id,
                'status': notification_data['status'],
                'message': 'Notification sent successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to send notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def broadcast_notification(self, notification: Dict[str, Any], user_ids: List[str] = None) -> Dict[str, Any]:
        """Broadcast notification to multiple users"""
        try:
            results = []
            
            if user_ids:
                # Send to specific users
                for user_id in user_ids:
                    result = self.send_notification(user_id, notification)
                    results.append(result)
            else:
                # Broadcast to all connected users
                notification_data = {
                    'notification_id': f"broadcast_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'title': notification.get('title', 'Broadcast'),
                    'body': notification.get('body', ''),
                    'type': notification.get('type', 'info'),
                    'icon': notification.get('icon'),
                    'url': notification.get('url'),
                    'timestamp': datetime.now().isoformat(),
                    'broadcast': True
                }
                
                socketio.emit('broadcast', notification_data)
                
                results.append({
                    'success': True,
                    'message': f'Broadcast sent to {len(self.active_connections)} users'
                })
            
            return {
                'success': True,
                'results': results,
                'message': 'Broadcast completed'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to broadcast notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_connections(self, user_id: str) -> Dict[str, Any]:
        """Get user's active connections"""
        connections = self.active_connections.get(user_id, [])
        return {
            'user_id': user_id,
            'active_connections': len(connections),
            'socket_ids': connections
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get notification service status"""
        return {
            'service': 'notification_microservice',
            'active_users': len(self.active_connections),
            'total_connections': sum(len(conns) for conns in self.active_connections.values()),
            'queued_notifications': len(self.notification_queue),
            'total_notifications_sent': len(self.notification_history),
            'port': 7002
        }

# Global notification service instance
notification_service = NotificationService()

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_user_room')
def handle_join_user_room(data):
    """Handle user joining their room"""
    try:
        user_id = data.get('user_id')
        if user_id:
            join_room(user_id)
            notification_service.add_connection(user_id, request.sid)
            emit('joined_room', {'user_id': user_id, 'status': 'success'})
            logger.info(f"User {user_id} joined room with socket {request.sid}")
    except Exception as e:
        logger.error(f"Error joining user room: {e}")
        emit('error', {'message': str(e)})

@socketio.on('leave_user_room')
def handle_leave_user_room(data):
    """Handle user leaving their room"""
    try:
        user_id = data.get('user_id')
        if user_id:
            leave_room(user_id)
            notification_service.remove_connection(user_id, request.sid)
            emit('left_room', {'user_id': user_id, 'status': 'success'})
            logger.info(f"User {user_id} left room with socket {request.sid}")
    except Exception as e:
        logger.error(f"Error leaving user room: {e}")
        emit('error', {'message': str(e)})

# API Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    status = notification_service.get_service_status()
    status['status'] = 'healthy'
    return jsonify(status), 200

@app.route('/status', methods=['GET'])
def get_status():
    """Get notification service status"""
    return jsonify(notification_service.get_service_status()), 200

@app.route('/send', methods=['POST'])
def send_notification():
    """Send notification to a specific user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'title']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Send notification
        result = notification_service.send_notification(
            user_id=data['user_id'],
            notification=data
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in send_notification endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/broadcast', methods=['POST'])
def broadcast_notification():
    """Broadcast notification to multiple users"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'title' not in data:
            return jsonify({'success': False, 'error': 'Missing required field: title'}), 400
        
        # Broadcast notification
        result = notification_service.broadcast_notification(
            notification=data,
            user_ids=data.get('user_ids')
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in broadcast_notification endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/connections/<user_id>', methods=['GET'])
def get_user_connections(user_id):
    """Get user's active connections"""
    try:
        result = notification_service.get_user_connections(user_id)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error getting user connections: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_notification_history():
    """Get notification history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        recent_history = notification_service.notification_history[-limit:] if notification_service.notification_history else []
        
        return jsonify({
            'total_notifications': len(notification_service.notification_history),
            'recent_notifications': recent_history
        }), 200
    except Exception as e:
        logger.error(f"Error getting notification history: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Notification Microservice on port 7002")
    try:
        socketio.run(app, host='0.0.0.0', port=7002, debug=False)
    except KeyboardInterrupt:
        logger.info("🛑 Stopping Notification Microservice")
    except Exception as e:
        logger.error(f"❌ Error starting Notification Microservice: {e}")


