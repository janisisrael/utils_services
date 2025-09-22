"""
Base Service Interface for Utils_services
Provides common functionality for all notification services
"""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class DeliveryStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"

class NotificationTask:
    """Base class for all notification tasks"""
    
    def __init__(self, 
                 task_type: str,
                 recipient: str,
                 data: Dict[str, Any],
                 priority: str = "normal",
                 max_retries: int = 3):
        self.id = str(uuid.uuid4())
        self.task_type = task_type
        self.recipient = recipient
        self.data = data
        self.priority = priority
        self.max_retries = max_retries
        self.retry_count = 0
        self.status = DeliveryStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.error_message = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for storage/transmission"""
        return {
            'id': self.id,
            'task_type': self.task_type,
            'recipient': self.recipient,
            'data': self.data,
            'priority': self.priority,
            'max_retries': self.max_retries,
            'retry_count': self.retry_count,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationTask':
        """Create task from dictionary"""
        task = cls(
            task_type=data['task_type'],
            recipient=data['recipient'],
            data=data['data'],
            priority=data.get('priority', 'normal'),
            max_retries=data.get('max_retries', 3)
        )
        task.id = data['id']
        task.retry_count = data.get('retry_count', 0)
        task.status = DeliveryStatus(data.get('status', 'pending'))
        task.created_at = datetime.fromisoformat(data['created_at'])
        task.updated_at = datetime.fromisoformat(data['updated_at'])
        task.error_message = data.get('error_message')
        return task

class BaseNotificationService(ABC):
    """Abstract base class for all notification services"""
    
    def __init__(self, service_name: str, config: Dict[str, Any] = None):
        self.service_name = service_name
        self.config = config or {}
        self.status = ServiceStatus.INACTIVE
        self.metrics = {
            'messages_sent': 0,
            'messages_failed': 0,
            'last_activity': None,
            'service_start_time': datetime.now()
        }
        self.logger = logging.getLogger(f"{__name__}.{service_name}")
        
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the service"""
        pass
    
    @abstractmethod
    def send_notification(self, task: NotificationTask) -> bool:
        """Send a notification"""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        pass
    
    def start(self) -> bool:
        """Start the service"""
        try:
            if self.initialize():
                self.status = ServiceStatus.ACTIVE
                self.logger.info(f"{self.service_name} service started successfully")
                return True
            else:
                self.status = ServiceStatus.ERROR
                self.logger.error(f"Failed to start {self.service_name} service")
                return False
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.logger.error(f"Error starting {self.service_name} service: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the service"""
        try:
            self.status = ServiceStatus.INACTIVE
            self.logger.info(f"{self.service_name} service stopped")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping {self.service_name} service: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        return {
            'service_name': self.service_name,
            'status': self.status.value,
            'metrics': self.metrics,
            'uptime_seconds': (datetime.now() - self.metrics['service_start_time']).total_seconds()
        }
    
    def update_metrics(self, success: bool, error_message: str = None):
        """Update service metrics"""
        if success:
            self.metrics['messages_sent'] += 1
        else:
            self.metrics['messages_failed'] += 1
            if error_message:
                self.logger.error(f"Service error: {error_message}")
        
        self.metrics['last_activity'] = datetime.now()

class ServiceRegistry:
    """Registry to manage all notification services"""
    
    def __init__(self):
        self.services: Dict[str, BaseNotificationService] = {}
        self.logger = logging.getLogger(f"{__name__}.ServiceRegistry")
    
    def register_service(self, service: BaseNotificationService) -> bool:
        """Register a notification service"""
        try:
            self.services[service.service_name] = service
            self.logger.info(f"Registered service: {service.service_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register service {service.service_name}: {e}")
            return False
    
    def get_service(self, service_name: str) -> Optional[BaseNotificationService]:
        """Get a service by name"""
        return self.services.get(service_name)
    
    def get_active_services(self) -> Dict[str, BaseNotificationService]:
        """Get all active services"""
        return {
            name: service for name, service in self.services.items()
            if service.status == ServiceStatus.ACTIVE
        }
    
    def start_all_services(self) -> Dict[str, bool]:
        """Start all registered services"""
        results = {}
        for name, service in self.services.items():
            results[name] = service.start()
        return results
    
    def stop_all_services(self) -> Dict[str, bool]:
        """Stop all registered services"""
        results = {}
        for name, service in self.services.items():
            results[name] = service.stop()
        return results
    
    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Run health check on all services"""
        health_status = {}
        for name, service in self.services.items():
            try:
                health_status[name] = service.health_check()
            except Exception as e:
                health_status[name] = {
                    'status': 'error',
                    'error': str(e)
                }
        return health_status
