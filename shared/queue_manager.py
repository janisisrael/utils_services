"""
Generic Queue Manager for Utils_services
Handles queuing, processing, and retry logic for all notification services
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from collections import deque
import logging

logger = logging.getLogger(__name__)

class QueuePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class QueueTask:
    """Generic queue task"""
    
    def __init__(self, 
                 task_id: str,
                 data: Dict[str, Any],
                 priority: QueuePriority = QueuePriority.NORMAL,
                 max_retries: int = 3,
                 retry_delay: int = 60):
        self.task_id = task_id
        self.data = data
        self.priority = priority
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_count = 0
        self.created_at = datetime.now()
        self.scheduled_at = datetime.now()
        self.last_attempt_at = None
        self.error_message = None
        self.status = "pending"

class InMemoryQueue:
    """In-memory queue implementation with priority support"""
    
    def __init__(self, name: str):
        self.name = name
        self.queues = {
            QueuePriority.URGENT: deque(),
            QueuePriority.HIGH: deque(),
            QueuePriority.NORMAL: deque(),
            QueuePriority.LOW: deque()
        }
        self.failed_queue = deque()
        self.retry_queue = deque()
        self.lock = threading.Lock()
        self.metrics = {
            'total_added': 0,
            'total_processed': 0,
            'total_failed': 0,
            'total_retried': 0
        }
    
    def add(self, task: QueueTask) -> bool:
        """Add task to queue"""
        try:
            with self.lock:
                self.queues[task.priority].append(task)
                self.metrics['total_added'] += 1
            logger.debug(f"Added task {task.task_id} to {self.name} queue")
            return True
        except Exception as e:
            logger.error(f"Error adding task to queue {self.name}: {e}")
            return False
    
    def get_next(self) -> Optional[QueueTask]:
        """Get next task with highest priority"""
        with self.lock:
            # Check retry queue first
            if self.retry_queue:
                for i, task in enumerate(list(self.retry_queue)):
                    if datetime.now() >= task.scheduled_at:
                        self.retry_queue.remove(task)
                        return task
            
            # Check priority queues
            for priority in [QueuePriority.URGENT, QueuePriority.HIGH, 
                           QueuePriority.NORMAL, QueuePriority.LOW]:
                if self.queues[priority]:
                    return self.queues[priority].popleft()
            
            return None
    
    def mark_processed(self, task: QueueTask):
        """Mark task as successfully processed"""
        with self.lock:
            self.metrics['total_processed'] += 1
        logger.debug(f"Task {task.task_id} processed successfully")
    
    def mark_failed(self, task: QueueTask, error_message: str):
        """Mark task as failed and handle retry logic"""
        task.error_message = error_message
        task.last_attempt_at = datetime.now()
        task.retry_count += 1
        
        with self.lock:
            if task.retry_count < task.max_retries:
                # Schedule for retry
                task.scheduled_at = datetime.now() + timedelta(seconds=task.retry_delay * task.retry_count)
                task.status = "retrying"
                self.retry_queue.append(task)
                self.metrics['total_retried'] += 1
                logger.info(f"Task {task.task_id} scheduled for retry {task.retry_count}/{task.max_retries}")
            else:
                # Move to failed queue
                task.status = "failed"
                self.failed_queue.append(task)
                self.metrics['total_failed'] += 1
                logger.error(f"Task {task.task_id} failed permanently: {error_message}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self.lock:
            return {
                'name': self.name,
                'pending_counts': {
                    'urgent': len(self.queues[QueuePriority.URGENT]),
                    'high': len(self.queues[QueuePriority.HIGH]),
                    'normal': len(self.queues[QueuePriority.NORMAL]),
                    'low': len(self.queues[QueuePriority.LOW])
                },
                'retry_count': len(self.retry_queue),
                'failed_count': len(self.failed_queue),
                'metrics': self.metrics
            }

class QueueProcessor:
    """Generic queue processor that handles task execution"""
    
    def __init__(self, 
                 name: str,
                 queue: InMemoryQueue,
                 processor_func: Callable[[QueueTask], bool],
                 max_workers: int = 5,
                 poll_interval: int = 1):
        self.name = name
        self.queue = queue
        self.processor_func = processor_func
        self.max_workers = max_workers
        self.poll_interval = poll_interval
        self.running = False
        self.workers = []
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def start(self):
        """Start queue processing"""
        if self.running:
            return
        
        self.running = True
        self.logger.info(f"Starting queue processor {self.name} with {self.max_workers} workers")
        
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, args=(i,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
    
    def stop(self):
        """Stop queue processing"""
        self.running = False
        self.logger.info(f"Stopping queue processor {self.name}")
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        self.workers.clear()
    
    def _worker_loop(self, worker_id: int):
        """Worker loop that processes queue tasks"""
        self.logger.debug(f"Worker {worker_id} started for {self.name}")
        
        while self.running:
            try:
                task = self.queue.get_next()
                if task is None:
                    time.sleep(self.poll_interval)
                    continue
                
                self.logger.debug(f"Worker {worker_id} processing task {task.task_id}")
                
                # Process the task
                try:
                    success = self.processor_func(task)
                    if success:
                        self.queue.mark_processed(task)
                    else:
                        self.queue.mark_failed(task, "Processor function returned False")
                except Exception as e:
                    self.queue.mark_failed(task, str(e))
                    
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
                time.sleep(self.poll_interval)
        
        self.logger.debug(f"Worker {worker_id} stopped for {self.name}")

class QueueManager:
    """Central manager for all queues"""
    
    def __init__(self):
        self.queues: Dict[str, InMemoryQueue] = {}
        self.processors: Dict[str, QueueProcessor] = {}
        self.logger = logging.getLogger(f"{__name__}.QueueManager")
    
    def create_queue(self, name: str) -> InMemoryQueue:
        """Create a new queue"""
        if name in self.queues:
            return self.queues[name]
        
        queue = InMemoryQueue(name)
        self.queues[name] = queue
        self.logger.info(f"Created queue: {name}")
        return queue
    
    def create_processor(self, 
                        name: str,
                        queue_name: str,
                        processor_func: Callable[[QueueTask], bool],
                        max_workers: int = 5) -> QueueProcessor:
        """Create a queue processor"""
        if name in self.processors:
            return self.processors[name]
        
        if queue_name not in self.queues:
            raise ValueError(f"Queue {queue_name} does not exist")
        
        processor = QueueProcessor(
            name=name,
            queue=self.queues[queue_name],
            processor_func=processor_func,
            max_workers=max_workers
        )
        self.processors[name] = processor
        self.logger.info(f"Created processor: {name} for queue: {queue_name}")
        return processor
    
    def start_all_processors(self):
        """Start all queue processors"""
        for name, processor in self.processors.items():
            processor.start()
            self.logger.info(f"Started processor: {name}")
    
    def stop_all_processors(self):
        """Stop all queue processors"""
        for name, processor in self.processors.items():
            processor.stop()
            self.logger.info(f"Stopped processor: {name}")
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all queues"""
        stats = {}
        for name, queue in self.queues.items():
            stats[name] = queue.get_stats()
        return stats
    
    def add_task(self, 
                queue_name: str,
                task_id: str,
                data: Dict[str, Any],
                priority: QueuePriority = QueuePriority.NORMAL) -> bool:
        """Add task to specified queue"""
        if queue_name not in self.queues:
            self.logger.error(f"Queue {queue_name} does not exist")
            return False
        
        task = QueueTask(task_id, data, priority)
        return self.queues[queue_name].add(task)
