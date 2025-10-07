"""
Central Notification Dispatcher for Utils_services
Orchestrates email and push notification services
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

from ..shared.base_service import ServiceRegistry, ServiceStatus
from ..email_service.email_service import EmailService
from ..notification_service.notification_service import NotificationService

logger = logging.getLogger(__name__)

class NotificationDispatcher:
    """Central dispatcher for all notification services"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.service_registry = ServiceRegistry()
        self.delivery_tracker = DeliveryTracker()
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        self.logger = logging.getLogger(f"{__name__}.NotificationDispatcher")
        
        # Services
        self.email_service = None
        self.notification_service = None
        
        # Configuration
        self.retry_failed_notifications = config.get('retry_failed_notifications', True)
        self.max_concurrent_dispatches = config.get('max_concurrent_dispatches', 5)
        
    def initialize(self, email_config: Dict[str, Any], notification_config: Dict[str, Any]) -> bool:
        """Initialize all notification services"""
        try:
            # Initialize email service
            self.email_service = EmailService(email_config)
            if not self.service_registry.register_service(self.email_service):
                return False
            
            # Initialize notification service
            self.notification_service = NotificationService(notification_config)
            if not self.service_registry.register_service(self.notification_service):
                return False
            
            # Start all services
            start_results = self.service_registry.start_all_services()
            
            if all(start_results.values()):
                self.logger.info("All notification services started successfully")
                return True
            else:
                self.logger.error(f"Some services failed to start: {start_results}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize dispatcher: {e}")
            return False
    
    def dispatch_winner_notification(self, winner_data: Dict[str, Any]) -> str:
        """Dispatch winner notification to all channels"""
        dispatch_id = str(uuid.uuid4())
        
        try:
            self.logger.info(f"Dispatching winner notification {dispatch_id} for user {winner_data.get('user_id')}")
            
            # Track this dispatch
            self.delivery_tracker.start_tracking(dispatch_id, winner_data)
            
            # Submit tasks to thread pool
            futures = []
            
            # Email notification
            if self.email_service and self.email_service.status == ServiceStatus.ACTIVE:
                future = self.thread_pool.submit(
                    self._send_email_notification,
                    dispatch_id,
                    winner_data
                )
                futures.append(('email', future))
            
            # Push notification
            if self.notification_service and self.notification_service.status == ServiceStatus.ACTIVE:
                future = self.thread_pool.submit(
                    self._send_push_notification,
                    dispatch_id,
                    winner_data
                )
                futures.append(('notification', future))
            
            # Track futures for completion
            self._track_dispatch_completion(dispatch_id, futures)
            
            return dispatch_id
            
        except Exception as e:
            self.logger.error(f"Error dispatching winner notification: {e}")
            self.delivery_tracker.mark_failed(dispatch_id, str(e))
            return dispatch_id
    
    def _send_email_notification(self, dispatch_id: str, winner_data: Dict[str, Any]) -> bool:
        """Send email notification"""
        try:
            success = self.email_service.send_winner_notification(winner_data)
            self.delivery_tracker.update_channel_status(dispatch_id, 'email', success)
            return success
        except Exception as e:
            self.logger.error(f"Error sending email for dispatch {dispatch_id}: {e}")
            self.delivery_tracker.update_channel_status(dispatch_id, 'email', False, str(e))
            return False
    
    def _send_push_notification(self, dispatch_id: str, winner_data: Dict[str, Any]) -> bool:
        """Send push notification"""
        try:
            success = self.notification_service.send_winner_notification(winner_data)
            self.delivery_tracker.update_channel_status(dispatch_id, 'notification', success)
            return success
        except Exception as e:
            self.logger.error(f"Error sending notification for dispatch {dispatch_id}: {e}")
            self.delivery_tracker.update_channel_status(dispatch_id, 'notification', False, str(e))
            return False
    
    def _track_dispatch_completion(self, dispatch_id: str, futures: List):
        """Track completion of all dispatch tasks"""
        def completion_callback():
            try:
                # Wait for all futures to complete
                for channel, future in futures:
                    try:
                        future.result(timeout=30)  # 30 second timeout
                    except Exception as e:
                        self.logger.error(f"Future failed for {channel} in dispatch {dispatch_id}: {e}")
                
                # Mark dispatch as completed
                self.delivery_tracker.mark_completed(dispatch_id)
                self.logger.info(f"Dispatch {dispatch_id} completed")
                
            except Exception as e:
                self.logger.error(f"Error in completion callback for dispatch {dispatch_id}: {e}")
        
        # Submit completion tracking to thread pool
        self.thread_pool.submit(completion_callback)
    
    def dispatch_custom_notification(self, 
                                   user_id: int,
                                   title: str,
                                   body: str,
                                   channels: List[str] = None,
                                   priority: str = "normal",
                                   **kwargs) -> str:
        """Dispatch custom notification"""
        dispatch_id = str(uuid.uuid4())
        channels = channels or ['email', 'notification']
        
        try:
            notification_data = {
                'user_id': user_id,
                'title': title,
                'body': body,
                'priority': priority,
                **kwargs
            }
            
            self.delivery_tracker.start_tracking(dispatch_id, notification_data)
            
            futures = []
            
            # Email channel
            if 'email' in channels and self.email_service:
                # Custom email implementation would go here
                pass
            
            # Push notification channel
            if 'notification' in channels and self.notification_service:
                future = self.thread_pool.submit(
                    self._send_custom_push_notification,
                    dispatch_id,
                    notification_data
                )
                futures.append(('notification', future))
            
            self._track_dispatch_completion(dispatch_id, futures)
            
            return dispatch_id
            
        except Exception as e:
            self.logger.error(f"Error dispatching custom notification: {e}")
            self.delivery_tracker.mark_failed(dispatch_id, str(e))
            return dispatch_id
    
    def _send_custom_push_notification(self, dispatch_id: str, notification_data: Dict[str, Any]) -> bool:
        """Send custom push notification"""
        try:
            from ..notification_service.notification_service import PushNotificationTask
            
            task = PushNotificationTask(
                user_id=notification_data['user_id'],
                title=notification_data['title'],
                body=notification_data['body'],
                notification_type=notification_data.get('type', 'info'),
                priority=notification_data.get('priority', 'normal')
            )
            
            success = self.notification_service.send_notification(task)
            self.delivery_tracker.update_channel_status(dispatch_id, 'notification', success)
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending custom notification for dispatch {dispatch_id}: {e}")
            self.delivery_tracker.update_channel_status(dispatch_id, 'notification', False, str(e))
            return False
    
    def get_dispatch_status(self, dispatch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a dispatch"""
        return self.delivery_tracker.get_status(dispatch_id)
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all services"""
        return self.service_registry.health_check_all()
    
    def get_dispatcher_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics"""
        return {
            'active_services': len(self.service_registry.get_active_services()),
            'total_services': len(self.service_registry.services),
            'delivery_stats': self.delivery_tracker.get_stats(),
            'thread_pool_stats': {
                'active_threads': self.thread_pool._threads.__len__() if hasattr(self.thread_pool, '_threads') else 0,
                'max_workers': self.thread_pool._max_workers
            }
        }
    
    def shutdown(self):
        """Shutdown dispatcher and all services"""
        try:
            self.logger.info("Shutting down notification dispatcher")
            
            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True, timeout=30)
            
            # Stop all services
            self.service_registry.stop_all_services()
            
            self.logger.info("Notification dispatcher shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during dispatcher shutdown: {e}")

class DeliveryTracker:
    """Tracks delivery status across multiple notification channels"""
    
    def __init__(self):
        self.dispatches: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(f"{__name__}.DeliveryTracker")
    
    def start_tracking(self, dispatch_id: str, data: Dict[str, Any]):
        """Start tracking a dispatch"""
        with self.lock:
            self.dispatches[dispatch_id] = {
                'dispatch_id': dispatch_id,
                'data': data,
                'status': 'pending',
                'channels': {},
                'created_at': datetime.now(),
                'completed_at': None,
                'error_message': None
            }
        self.logger.debug(f"Started tracking dispatch {dispatch_id}")
    
    def update_channel_status(self, dispatch_id: str, channel: str, success: bool, error_message: str = None):
        """Update status of a specific channel"""
        with self.lock:
            if dispatch_id in self.dispatches:
                self.dispatches[dispatch_id]['channels'][channel] = {
                    'success': success,
                    'timestamp': datetime.now(),
                    'error_message': error_message
                }
        self.logger.debug(f"Updated channel {channel} status for dispatch {dispatch_id}: {success}")
    
    def mark_completed(self, dispatch_id: str):
        """Mark dispatch as completed"""
        with self.lock:
            if dispatch_id in self.dispatches:
                dispatch = self.dispatches[dispatch_id]
                dispatch['status'] = 'completed'
                dispatch['completed_at'] = datetime.now()
                
                # Determine overall success
                channels = dispatch['channels']
                if channels:
                    overall_success = any(channel['success'] for channel in channels.values())
                    dispatch['overall_success'] = overall_success
        
        self.logger.debug(f"Marked dispatch {dispatch_id} as completed")
    
    def mark_failed(self, dispatch_id: str, error_message: str):
        """Mark dispatch as failed"""
        with self.lock:
            if dispatch_id in self.dispatches:
                self.dispatches[dispatch_id]['status'] = 'failed'
                self.dispatches[dispatch_id]['error_message'] = error_message
                self.dispatches[dispatch_id]['completed_at'] = datetime.now()
        
        self.logger.error(f"Marked dispatch {dispatch_id} as failed: {error_message}")
    
    def get_status(self, dispatch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a dispatch"""
        with self.lock:
            return self.dispatches.get(dispatch_id, {}).copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get delivery statistics"""
        with self.lock:
            total = len(self.dispatches)
            completed = sum(1 for d in self.dispatches.values() if d['status'] == 'completed')
            failed = sum(1 for d in self.dispatches.values() if d['status'] == 'failed')
            pending = total - completed - failed
            
            return {
                'total_dispatches': total,
                'completed': completed,
                'failed': failed,
                'pending': pending,
                'success_rate': (completed / total * 100) if total > 0 else 0
            }
    
    def cleanup_old_dispatches(self, max_age_hours: int = 24):
        """Remove old dispatch records"""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        
        with self.lock:
            to_remove = [
                dispatch_id for dispatch_id, dispatch in self.dispatches.items()
                if dispatch['created_at'].timestamp() < cutoff
            ]
            
            for dispatch_id in to_remove:
                del self.dispatches[dispatch_id]
        
        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} old dispatch records")

