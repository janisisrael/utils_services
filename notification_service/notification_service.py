"""
Dedicated Push Notification Service for Utils_services
Handles in-app notifications, WebSocket delivery, and database storage
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import threading
import uuid

from ..shared.base_service import BaseNotificationService, NotificationTask, DeliveryStatus
from ..shared.queue_manager import QueueManager, QueueTask, QueuePriority

logger = logging.getLogger(__name__)

class PushNotificationTask(NotificationTask):
    """Push notification specific task"""
    
    def __init__(self,
                 user_id: int,
                 title: str,
                 body: str,
                 notification_type: str = "info",
                 action_url: str = None,
                 action_text: str = None,
                 platform: str = "phase1",
                 module: str = "general",
                 category: str = "notification",
                 priority: str = "normal",
                 max_retries: int = 3):
        
        super().__init__(
            task_type="push_notification",
            recipient=str(user_id),
            data={
                'user_id': user_id,
                'title': title,
                'body': body,
                'type': notification_type,
                'action_url': action_url,
                'action_text': action_text,
                'platform': platform,
                'module': module,
                'category': category,
                'icon': self._get_icon_for_type(notification_type),
                'timestamp': datetime.now().isoformat()
            },
            priority=priority,
            max_retries=max_retries
        )
    
    @staticmethod
    def _get_icon_for_type(notification_type: str) -> str:
        """Get appropriate icon for notification type"""
        icon_map = {
            'success': 'check-circle',
            'info': 'info-circle',
            'warning': 'exclamation-triangle',
            'error': 'times-circle',
            'alert': 'bell',
            'trophy': 'trophy',
            'message': 'envelope'
        }
        return icon_map.get(notification_type, 'bell')

class DatabaseConnector:
    """Database connector for notification storage"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.logger = logging.getLogger(f"{__name__}.DatabaseConnector")
    
    def get_connection(self):
        """Get database connection (to be implemented based on Phase1's connection)"""
        # This will be implemented to use Phase1's database connection
        # For now, we'll use a mock implementation
        pass
    
    def store_notification(self, notification_data: Dict[str, Any]) -> Optional[int]:
        """Store notification in database"""
        try:
            # Mock implementation - in real implementation, this would use Phase1's database
            notification_id = hash(str(notification_data)) % 1000000
            self.logger.info(f"Stored notification with ID: {notification_id}")
            return notification_id
        except Exception as e:
            self.logger.error(f"Error storing notification: {e}")
            return None
    
    def mark_as_delivered(self, notification_id: int) -> bool:
        """Mark notification as delivered"""
        try:
            # Mock implementation
            self.logger.info(f"Marked notification {notification_id} as delivered")
            return True
        except Exception as e:
            self.logger.error(f"Error marking notification as delivered: {e}")
            return False
    
    def get_user_notifications(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user notifications from database"""
        try:
            # Mock implementation
            return []
        except Exception as e:
            self.logger.error(f"Error getting user notifications: {e}")
            return []

class WebSocketManager:
    """WebSocket manager for real-time notifications"""
    
    def __init__(self):
        self.active_connections: Dict[int, List[str]] = {}  # user_id -> [socket_ids]
        self.socket_users: Dict[str, int] = {}  # socket_id -> user_id
        self.lock = threading.Lock()
        self.logger = logging.getLogger(f"{__name__}.WebSocketManager")
    
    def add_connection(self, user_id: int, socket_id: str):
        """Add user socket connection"""
        with self.lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(socket_id)
            self.socket_users[socket_id] = user_id
        self.logger.debug(f"Added connection for user {user_id}: {socket_id}")
    
    def remove_connection(self, socket_id: str):
        """Remove socket connection"""
        with self.lock:
            if socket_id in self.socket_users:
                user_id = self.socket_users[socket_id]
                if user_id in self.active_connections:
                    if socket_id in self.active_connections[user_id]:
                        self.active_connections[user_id].remove(socket_id)
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
                del self.socket_users[socket_id]
        self.logger.debug(f"Removed connection: {socket_id}")
    
    def get_user_sockets(self, user_id: int) -> List[str]:
        """Get all socket connections for a user"""
        with self.lock:
            return self.active_connections.get(user_id, []).copy()
    
    def send_to_user(self, user_id: int, message: Dict[str, Any]) -> bool:
        """Send message to all user's connected sockets"""
        socket_ids = self.get_user_sockets(user_id)
        if not socket_ids:
            self.logger.debug(f"No active connections for user {user_id}")
            return False
        
        sent_count = 0
        for socket_id in socket_ids:
            try:
                # Mock implementation - in real implementation, this would use SocketIO
                self.logger.debug(f"Sending notification to socket {socket_id}: {message}")
                sent_count += 1
            except Exception as e:
                self.logger.error(f"Error sending to socket {socket_id}: {e}")
        
        return sent_count > 0
    
    def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """Broadcast message to all connected users"""
        sent_count = 0
        with self.lock:
            for user_id in self.active_connections.keys():
                if self.send_to_user(user_id, message):
                    sent_count += 1
        return sent_count

class NotificationService(BaseNotificationService):
    """Dedicated push notification service"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("NotificationService", config)
        
        # Database configuration
        self.db_connector = DatabaseConnector(config.get('database', {}))
        
        # WebSocket manager
        self.websocket_manager = WebSocketManager()
        
        # Queue management
        self.queue_manager = QueueManager()
        self.notification_queue = self.queue_manager.create_queue('notifications')
        self.notification_processor = None
        
        # Configuration
        self.store_in_database = config.get('store_in_database', True)
        self.send_via_websocket = config.get('send_via_websocket', True)
        self.max_notifications_per_user_per_hour = config.get('max_notifications_per_user_per_hour', 100)
        
        # Rate limiting
        self.user_notification_counts = {}  # user_id -> [timestamps]
        self.rate_limit_lock = threading.Lock()
    
    def initialize(self) -> bool:
        """Initialize the notification service"""
        try:
            # Create queue processor
            self.notification_processor = self.queue_manager.create_processor(
                name="notification_processor",
                queue_name="notifications",
                processor_func=self._process_notification_task,
                max_workers=5
            )
            
            # Start queue processing
            self.notification_processor.start()
            
            self.logger.info("Notification service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize notification service: {e}")
            return False
    
    def send_notification(self, task: NotificationTask) -> bool:
        """Queue notification for processing"""
        try:
            # Rate limiting check
            user_id = int(task.recipient)
            if not self._check_rate_limit(user_id):
                self.logger.warning(f"Rate limit exceeded for user {user_id}")
                return False
            
            # Convert to queue task
            queue_task = QueueTask(
                task_id=task.id,
                data=task.to_dict(),
                priority=self._get_queue_priority(task.priority),
                max_retries=task.max_retries
            )
            
            return self.notification_queue.add(queue_task)
            
        except Exception as e:
            self.logger.error(f"Error queuing notification: {e}")
            return False
    
    def _get_queue_priority(self, priority: str) -> QueuePriority:
        """Convert priority string to queue priority"""
        priority_map = {
            'low': QueuePriority.LOW,
            'normal': QueuePriority.NORMAL,
            'high': QueuePriority.HIGH,
            'urgent': QueuePriority.URGENT
        }
        return priority_map.get(priority, QueuePriority.NORMAL)
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """Check if user is within rate limits"""
        with self.rate_limit_lock:
            now = datetime.now()
            if user_id not in self.user_notification_counts:
                self.user_notification_counts[user_id] = []
            
            # Remove timestamps older than 1 hour
            hour_ago = now.timestamp() - 3600
            self.user_notification_counts[user_id] = [
                ts for ts in self.user_notification_counts[user_id] if ts > hour_ago
            ]
            
            if len(self.user_notification_counts[user_id]) >= self.max_notifications_per_user_per_hour:
                return False
            
            self.user_notification_counts[user_id].append(now.timestamp())
            return True
    
    def _process_notification_task(self, queue_task: QueueTask) -> bool:
        """Process notification task from queue"""
        try:
            task_data = queue_task.data
            notification_data = task_data.get('data', {})
            
            user_id = notification_data.get('user_id')
            notification_id = None
            
            # Store in database if enabled
            if self.store_in_database:
                notification_id = self.db_connector.store_notification(notification_data)
                if notification_id:
                    notification_data['notification_id'] = notification_id
            
            # Send via WebSocket if enabled
            websocket_sent = False
            if self.send_via_websocket:
                websocket_sent = self.websocket_manager.send_to_user(user_id, notification_data)
            
            # Mark as delivered if sent via any channel
            if notification_id and (websocket_sent or not self.send_via_websocket):
                self.db_connector.mark_as_delivered(notification_id)
            
            success = notification_id is not None or websocket_sent
            self.update_metrics(success)
            
            if success:
                self.logger.info(f"Notification sent to user {user_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error processing notification task: {e}")
            self.update_metrics(False, str(e))
            return False
    
    def send_winner_notification(self, winner_data: Dict[str, Any]) -> bool:
        """Send winner notification"""
        try:
            # Extract winner information
            user_id = winner_data.get('user_id')
            game = winner_data.get('game', 'Lottery')
            ticket_number = winner_data.get('ticket_number', 'N/A')
            draw_date = winner_data.get('draw_date', 'Unknown')
            match_count = winner_data.get('classic_draw', {}).get('match', 0)
            prize_category = winner_data.get('classic_draw', {}).get('prize_category', 'Win')
            ticket_id = winner_data.get('ticket_id', 0)
            
            # Create notification task
            notification_task = PushNotificationTask(
                user_id=user_id,
                title=f"🎉 You've Won in {game}!",
                body=f"Your ticket ({ticket_number}) for {game} on {draw_date} matched {match_count} number(s). Prize Category: {prize_category}",
                notification_type="success",
                action_url=f"/tickets/{ticket_id}",
                action_text="View Ticket",
                platform="phase1",
                module="tickets",
                category="winner",
                priority="high"
            )
            
            return self.send_notification(notification_task)
            
        except Exception as e:
            self.logger.error(f"Error sending winner notification: {e}")
            return False
    
    def add_websocket_connection(self, user_id: int, socket_id: str):
        """Add WebSocket connection for user"""
        self.websocket_manager.add_connection(user_id, socket_id)
    
    def remove_websocket_connection(self, socket_id: str):
        """Remove WebSocket connection"""
        self.websocket_manager.remove_connection(socket_id)
    
    def get_user_notifications(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user notifications"""
        return self.db_connector.get_user_notifications(user_id, limit)
    
    def health_check(self) -> Dict[str, Any]:
        """Check notification service health"""
        try:
            # Get queue stats
            queue_stats = self.notification_queue.get_stats() if self.notification_queue else {}
            
            # Get WebSocket stats
            websocket_stats = {
                'active_connections': len(self.websocket_manager.socket_users),
                'active_users': len(self.websocket_manager.active_connections)
            }
            
            return {
                'status': 'healthy',
                'queue_stats': queue_stats,
                'websocket_stats': websocket_stats,
                'metrics': self.get_metrics(),
                'rate_limiting': {
                    'max_per_hour': self.max_notifications_per_user_per_hour,
                    'active_rate_limits': len(self.user_notification_counts)
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def stop(self) -> bool:
        """Stop the notification service"""
        try:
            if self.notification_processor:
                self.notification_processor.stop()
            return super().stop()
        except Exception as e:
            self.logger.error(f"Error stopping notification service: {e}")
            return False

