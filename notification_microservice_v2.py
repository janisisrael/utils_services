#!/usr/bin/env python3
"""
Notification Microservice v2 - Standalone Service
Port: 7002

This is a separate notification service that doesn't touch any existing working code.
It provides real-time WebSocket notifications and REST API endpoints.
"""

import os
import sys
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'notification-microservice-secret-key')
CORS(app, supports_credentials=True, origins=["*"])

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global storage for active connections
active_connections = {}  # {socket_id: user_id}
user_sockets = {}        # {user_id: [socket_ids]}
notification_queue = {}  # {user_id: [notifications]}

# Service configuration
SERVICE_PORT = 7002
SERVICE_NAME = "notification_microservice_v2"

class NotificationService:
    """Core notification service class"""
    
    def __init__(self):
        self.service_status = {
            'is_running': True,
            'started_at': time.time(),
            'port': SERVICE_PORT,
            'active_connections': 0,
            'notifications_sent': 0
        }
        logger.info(f"🚀 {SERVICE_NAME} initialized on port {SERVICE_PORT}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        self.service_status['active_connections'] = len(active_connections)
        return self.service_status
    
    def send_notification(self, user_id: int, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification to user"""
        try:
            # Store notification in queue if user is offline
            if user_id not in user_sockets or not user_sockets[user_id]:
                self._queue_notification(user_id, notification_data)
                return {
                    'success': True,
                    'message': 'Notification queued for offline user',
                    'user_id': user_id,
                    'queued': True
                }
            
            # Send to all user's active connections
            sent_count = 0
            for socket_id in user_sockets[user_id]:
                try:
                    socketio.emit('new_notification', notification_data, to=socket_id)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error sending notification to socket {socket_id}: {e}")
            
            self.service_status['notifications_sent'] += sent_count
            
            return {
                'success': True,
                'message': f'Notification sent to {sent_count} device(s)',
                'user_id': user_id,
                'sent_count': sent_count
            }
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id
            }
    
    def broadcast_notification(self, notification_data: Dict[str, Any], user_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Broadcast notification to multiple users"""
        try:
            if user_ids:
                target_users = user_ids
            else:
                target_users = list(user_sockets.keys())
            
            sent_count = 0
            for user_id in target_users:
                result = self.send_notification(user_id, notification_data)
                if result['success']:
                    sent_count += 1
            
            return {
                'success': True,
                'message': f'Broadcast sent to {sent_count} users',
                'total_users': len(target_users),
                'sent_count': sent_count
            }
            
        except Exception as e:
            logger.error(f"Error broadcasting notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _queue_notification(self, user_id: int, notification_data: Dict[str, Any]):
        """Queue notification for offline user"""
        if user_id not in notification_queue:
            notification_queue[user_id] = []
        
        notification_data['queued_at'] = datetime.now().isoformat()
        notification_queue[user_id].append(notification_data)
        
        # Keep only last 50 notifications per user
        if len(notification_queue[user_id]) > 50:
            notification_queue[user_id] = notification_queue[user_id][-50:]
    
    def get_queued_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        """Get queued notifications for user"""
        return notification_queue.get(user_id, [])
    
    def clear_queued_notifications(self, user_id: int) -> int:
        """Clear queued notifications for user"""
        if user_id in notification_queue:
            count = len(notification_queue[user_id])
            del notification_queue[user_id]
            return count
        return 0

# Initialize service
notification_service = NotificationService()

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to notification service'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    socket_id = request.sid
    if socket_id in active_connections:
        user_id = active_connections[socket_id]
        
        # Remove from user_sockets
        if user_id in user_sockets:
            if socket_id in user_sockets[user_id]:
                user_sockets[user_id].remove(socket_id)
            if not user_sockets[user_id]:
                del user_sockets[user_id]
        
        # Remove from active_connections
        del active_connections[socket_id]
        
        logger.info(f"User {user_id} disconnected from socket {socket_id}")
    
    emit('disconnected', {'message': 'Disconnected from notification service'})

@socketio.on('join_user')
def handle_join_user(data):
    """Handle user joining their notification room"""
    try:
        user_id = int(data.get('user_id'))
        socket_id = request.sid
        
        # Add to active connections
        active_connections[socket_id] = user_id
        
        # Add to user_sockets
        if user_id not in user_sockets:
            user_sockets[user_id] = []
        user_sockets[user_id].append(socket_id)
        
        # Join user room
        join_room(f"user_{user_id}")
        
        # Send queued notifications
        queued_notifications = notification_service.get_queued_notifications(user_id)
        if queued_notifications:
            emit('queued_notifications', {
                'notifications': queued_notifications,
                'count': len(queued_notifications)
            })
            # Clear queued notifications after sending
            notification_service.clear_queued_notifications(user_id)
        
        logger.info(f"User {user_id} joined notification room via socket {socket_id}")
        emit('joined', {'user_id': user_id, 'message': 'Successfully joined notification room'})
        
    except Exception as e:
        logger.error(f"Error joining user: {e}")
        emit('error', {'message': f'Error joining user: {str(e)}'})

@socketio.on('leave_user')
def handle_leave_user(data):
    """Handle user leaving their notification room"""
    try:
        user_id = int(data.get('user_id'))
        socket_id = request.sid
        
        # Remove from user_sockets
        if user_id in user_sockets and socket_id in user_sockets[user_id]:
            user_sockets[user_id].remove(socket_id)
            if not user_sockets[user_id]:
                del user_sockets[user_id]
        
        # Remove from active_connections
        if socket_id in active_connections:
            del active_connections[socket_id]
        
        # Leave user room
        leave_room(f"user_{user_id}")
        
        logger.info(f"User {user_id} left notification room via socket {socket_id}")
        emit('left', {'user_id': user_id, 'message': 'Successfully left notification room'})
        
    except Exception as e:
        logger.error(f"Error leaving user: {e}")
        emit('error', {'message': f'Error leaving user: {str(e)}'})

# REST API Endpoints
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': SERVICE_NAME,
        'port': SERVICE_PORT,
        'uptime': time.time() - notification_service.service_status['started_at'],
        'active_connections': len(active_connections),
        'notifications_sent': notification_service.service_status['notifications_sent']
    }), 200

@app.route('/status', methods=['GET'])
def get_status():
    """Get detailed service status"""
    return jsonify(notification_service.get_status()), 200

@app.route('/send', methods=['POST'])
def send_notification():
    """Send notification to specific user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'title', 'body']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        user_id = int(data['user_id'])
        notification_data = {
            'title': data['title'],
            'body': data['body'],
            'type': data.get('type', 'info'),
            'icon': data.get('icon'),
            'url': data.get('url'),
            'timestamp': datetime.now().isoformat(),
            'data': data.get('data', {})
        }
        
        result = notification_service.send_notification(user_id, notification_data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in send_notification endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/broadcast', methods=['POST'])
def broadcast_notification():
    """Broadcast notification to multiple users"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'body']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        notification_data = {
            'title': data['title'],
            'body': data['body'],
            'type': data.get('type', 'info'),
            'icon': data.get('icon'),
            'url': data.get('url'),
            'timestamp': datetime.now().isoformat(),
            'data': data.get('data', {})
        }
        
        user_ids = data.get('user_ids')  # Optional list of user IDs
        result = notification_service.broadcast_notification(notification_data, user_ids)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in broadcast_notification endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/connections', methods=['GET'])
def get_connections():
    """Get active connections info"""
    return jsonify({
        'active_connections': len(active_connections),
        'connected_users': len(user_sockets),
        'connections': {
            'socket_to_user': active_connections,
            'user_to_sockets': user_sockets
        }
    }), 200

@app.route('/queue/<int:user_id>', methods=['GET'])
def get_user_queue(user_id):
    """Get queued notifications for user"""
    notifications = notification_service.get_queued_notifications(user_id)
    return jsonify({
        'user_id': user_id,
        'queued_count': len(notifications),
        'notifications': notifications
    }), 200

@app.route('/queue/<int:user_id>', methods=['DELETE'])
def clear_user_queue(user_id):
    """Clear queued notifications for user"""
    cleared_count = notification_service.clear_queued_notifications(user_id)
    return jsonify({
        'user_id': user_id,
        'cleared_count': cleared_count,
        'message': f'Cleared {cleared_count} queued notifications'
    }), 200

# Integration with Phase 1
@app.route('/phase1/winner', methods=['POST'])
def handle_winner_notification():
    """Handle winner notification from Phase 1"""
    try:
        data = request.get_json()
        
        # Extract winner data
        user_id = data.get('user_id')
        game = data.get('game', 'Lottery')
        draw_date = data.get('draw_date', 'Unknown')
        ticket_number = data.get('ticket_number', 'N/A')
        prize_amount = data.get('prize_amount', 'N/A')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Missing user_id'
            }), 400
        
        # Create winner notification
        notification_data = {
            'title': f'🎉 You Won in {game}!',
            'body': f'Congratulations! Your ticket {ticket_number} won ${prize_amount} in the {draw_date} draw.',
            'type': 'success',
            'icon': 'trophy',
            'url': f'/tickets/{data.get("ticket_id", "")}',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'game': game,
                'draw_date': draw_date,
                'ticket_number': ticket_number,
                'prize_amount': prize_amount,
                'ticket_id': data.get('ticket_id')
            }
        }
        
        result = notification_service.send_notification(int(user_id), notification_data)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Error handling winner notification: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == "__main__":
    logger.info(f"🚀 Starting {SERVICE_NAME} on port {SERVICE_PORT}")
    try:
        socketio.run(app, host='0.0.0.0', port=SERVICE_PORT, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        logger.info(f"🛑 Stopping {SERVICE_NAME}")
    except Exception as e:
        logger.error(f"❌ Error starting {SERVICE_NAME}: {e}")
