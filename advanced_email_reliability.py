"""
Enhanced Email Service with Advanced Reliability Features
This module provides comprehensive email reliability improvements including:
- Advanced threading with ThreadPoolExecutor
- Email delivery guarantees with retry mechanisms
- Anti-spam measures and best practices
- Professional email libraries integration
- Delivery tracking and monitoring
"""

import smtplib
import logging
import time
import threading
import queue
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
from email.utils import formataddr, make_msgid
import dns.resolver
import socket
import ssl
import re

logger = logging.getLogger(__name__)

class EmailReliabilityManager:
    """
    Advanced email reliability manager with anti-spam measures and delivery guarantees
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # SMTP Configuration
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.smtp_username = config.get('smtp_username')
        self.smtp_password = config.get('smtp_password')
        self.sender_email = config.get('sender_email', self.smtp_username)
        self.sender_name = config.get('sender_name', 'Lotto Command Center')
        self.use_tls = config.get('use_tls', True)
        
        # Threading Configuration
        self.max_workers = config.get('max_email_workers', 5)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.email_queue = queue.PriorityQueue()
        
        # Rate Limiting (Anti-spam measures)
        self.max_emails_per_minute = config.get('max_emails_per_minute', 30)  # Conservative limit
        self.max_emails_per_hour = config.get('max_emails_per_hour', 500)
        self.min_delay_between_emails = config.get('min_delay_between_emails', 2)  # seconds
        self.email_timestamps = []
        self.rate_limit_lock = threading.Lock()
        
        # Retry Configuration
        self.max_retries = config.get('max_email_retries', 5)
        self.retry_delays = [1, 2, 5, 10, 30]  # Progressive delays in seconds
        self.dead_letter_queue = []
        
        # Delivery Tracking
        self.delivery_tracking = {}
        self.tracking_lock = threading.Lock()
        
        # Anti-spam Configuration
        self.enable_spf_check = config.get('enable_spf_check', True)
        self.enable_dkim_signing = config.get('enable_dkim_signing', False)
        self.dkim_private_key = config.get('dkim_private_key')
        self.dkim_selector = config.get('dkim_selector', 'default')
        
        # Email Content Validation
        self.max_subject_length = 78  # RFC 2822 recommendation
        self.max_body_length = 1000000  # 1MB limit
        self.blocked_domains = config.get('blocked_domains', [])
        self.required_headers = ['From', 'To', 'Subject', 'Date', 'Message-ID']
        
        # Start background processors
        self._start_background_processors()
        
    def _start_background_processors(self):
        """Start background threads for email processing"""
        # Email queue processor
        self.queue_processor_thread = threading.Thread(
            target=self._process_email_queue,
            daemon=True
        )
        self.queue_processor_thread.start()
        
        # Retry processor
        self.retry_processor_thread = threading.Thread(
            target=self._process_retry_queue,
            daemon=True
        )
        self.retry_processor_thread.start()
        
        # Cleanup processor
        self.cleanup_processor_thread = threading.Thread(
            target=self._cleanup_old_tracking,
            daemon=True
        )
        self.cleanup_processor_thread.start()
        
        logger.info("✅ Email reliability background processors started")

class AdvancedEmailService:
    """
    Advanced email service with comprehensive reliability features
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.reliability_manager = EmailReliabilityManager(config)
        self.config = config
        
    def send_email_reliable(self, 
                          recipient: str,
                          subject: str,
                          body_html: str,
                          body_text: str = None,
                          priority: str = "normal",
                          tracking_id: str = None) -> str:
        """
        Send email with advanced reliability features
        
        Args:
            recipient: Email recipient
            subject: Email subject
            body_html: HTML email body
            body_text: Plain text email body
            priority: Email priority (low, normal, high, urgent)
            tracking_id: Optional tracking ID
            
        Returns:
            str: Tracking ID for the email
        """
        
        # Generate tracking ID if not provided
        if not tracking_id:
            tracking_id = self._generate_tracking_id(recipient)
        
        # Validate email content
        validation_result = self._validate_email_content(recipient, subject, body_html)
        if not validation_result['valid']:
            logger.error(f"Email validation failed: {validation_result['error']}")
            self._track_delivery(tracking_id, 'validation_failed', validation_result['error'])
            return tracking_id
        
        # Create email task
        email_task = {
            'tracking_id': tracking_id,
            'recipient': recipient,
            'subject': subject,
            'body_html': body_html,
            'body_text': body_text or self._html_to_text(body_html),
            'priority': priority,
            'created_at': datetime.now(),
            'attempts': 0,
            'status': 'queued'
        }
        
        # Add to queue with priority
        priority_value = self._get_priority_value(priority)
        self.reliability_manager.email_queue.put((priority_value, email_task))
        
        # Track initial status
        self._track_delivery(tracking_id, 'queued', 'Email added to processing queue')
        
        logger.info(f"📧 Email queued for {recipient} (ID: {tracking_id})")
        return tracking_id
    
    def _validate_email_content(self, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        """Validate email content for anti-spam compliance"""
        
        # Check recipient format
        if not self._is_valid_email(recipient):
            return {'valid': False, 'error': f'Invalid email format: {recipient}'}
        
        # Check blocked domains
        domain = recipient.split('@')[1].lower()
        if domain in self.reliability_manager.blocked_domains:
            return {'valid': False, 'error': f'Blocked domain: {domain}'}
        
        # Check subject length
        if len(subject) > self.reliability_manager.max_subject_length:
            return {'valid': False, 'error': f'Subject too long: {len(subject)} characters'}
        
        # Check body length
        if len(body) > self.reliability_manager.max_body_length:
            return {'valid': False, 'error': f'Body too long: {len(body)} characters'}
        
        # Check for spam keywords
        spam_keywords = ['free', 'winner', 'congratulations', 'urgent', 'limited time']
        subject_lower = subject.lower()
        body_lower = body.lower()
        
        spam_count = sum(1 for keyword in spam_keywords 
                        if keyword in subject_lower or keyword in body_lower)
        
        if spam_count > 2:  # Allow some keywords but not too many
            return {'valid': False, 'error': 'Too many spam keywords detected'}
        
        # Check for proper HTML structure
        if '<html>' in body and '</html>' not in body:
            return {'valid': False, 'error': 'Malformed HTML structure'}
        
        return {'valid': True}
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _generate_tracking_id(self, recipient: str) -> str:
        """Generate unique tracking ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        recipient_hash = hashlib.md5(recipient.encode()).hexdigest()[:8]
        return f"email_{timestamp}_{recipient_hash}"
    
    def _get_priority_value(self, priority: str) -> int:
        """Get numeric priority value for queue ordering"""
        priorities = {
            'low': 3,
            'normal': 2,
            'high': 1,
            'urgent': 0
        }
        return priorities.get(priority, 2)
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text"""
        import re
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html_content)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return text.strip()
    
    def _track_delivery(self, tracking_id: str, status: str, message: str = None):
        """Track email delivery status"""
        with self.reliability_manager.tracking_lock:
            self.reliability_manager.delivery_tracking[tracking_id] = {
                'status': status,
                'message': message,
                'timestamp': datetime.now(),
                'updated_at': datetime.now()
            }
    
    def get_delivery_status(self, tracking_id: str) -> Dict[str, Any]:
        """Get email delivery status"""
        with self.reliability_manager.tracking_lock:
            return self.reliability_manager.delivery_tracking.get(tracking_id, {
                'status': 'not_found',
                'message': 'Tracking ID not found',
                'timestamp': None
            })
    
    def _process_email_queue(self):
        """Process emails from the queue"""
        while True:
            try:
                # Get next email from queue (blocking)
                priority, email_task = self.reliability_manager.email_queue.get(timeout=1)
                
                # Check rate limits
                if not self._check_rate_limits():
                    # Put email back in queue with lower priority
                    self.reliability_manager.email_queue.put((priority + 1, email_task))
                    time.sleep(1)
                    continue
                
                # Process email
                self._send_email_with_retry(email_task)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing email queue: {e}")
                time.sleep(5)
    
    def _check_rate_limits(self) -> bool:
        """Check if we're within rate limits"""
        with self.reliability_manager.rate_limit_lock:
            now = time.time()
            
            # Remove old timestamps
            self.reliability_manager.email_timestamps = [
                ts for ts in self.reliability_manager.email_timestamps 
                if now - ts < 3600  # Keep last hour
            ]
            
            # Check hourly limit
            if len(self.reliability_manager.email_timestamps) >= self.reliability_manager.max_emails_per_hour:
                return False
            
            # Check recent emails (last minute)
            recent_emails = [
                ts for ts in self.reliability_manager.email_timestamps 
                if now - ts < 60
            ]
            
            if len(recent_emails) >= self.reliability_manager.max_emails_per_minute:
                return False
            
            # Add current timestamp
            self.reliability_manager.email_timestamps.append(now)
            return True
    
    def _send_email_with_retry(self, email_task: Dict[str, Any]):
        """Send email with retry logic"""
        tracking_id = email_task['tracking_id']
        recipient = email_task['recipient']
        
        for attempt in range(self.reliability_manager.max_retries):
            try:
                # Update attempt count
                email_task['attempts'] = attempt + 1
                self._track_delivery(tracking_id, 'attempting', f'Attempt {attempt + 1}')
                
                # Send email
                success = self._send_single_email(email_task)
                
                if success:
                    self._track_delivery(tracking_id, 'delivered', 'Email sent successfully')
                    logger.info(f"✅ Email delivered to {recipient} (ID: {tracking_id})")
                    return
                
            except Exception as e:
                logger.error(f"Email attempt {attempt + 1} failed for {recipient}: {e}")
                
                # Wait before retry
                if attempt < self.reliability_manager.max_retries - 1:
                    delay = self.reliability_manager.retry_delays[min(attempt, len(self.reliability_manager.retry_delays) - 1)]
                    time.sleep(delay)
        
        # All retries failed
        self._track_delivery(tracking_id, 'failed', 'All retry attempts failed')
        self.reliability_manager.dead_letter_queue.append(email_task)
        logger.error(f"❌ Email failed permanently for {recipient} (ID: {tracking_id})")
    
    def _send_single_email(self, email_task: Dict[str, Any]) -> bool:
        """Send a single email"""
        try:
            # Create message
            msg = MimeMultipart('alternative')
            msg['From'] = formataddr((self.reliability_manager.sender_name, self.reliability_manager.sender_email))
            msg['To'] = email_task['recipient']
            msg['Subject'] = email_task['subject']
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            msg['Message-ID'] = make_msgid()
            
            # Add headers for anti-spam
            msg['X-Mailer'] = 'Lotto Command Center Email Service'
            msg['X-Priority'] = '3'  # Normal priority
            msg['MIME-Version'] = '1.0'
            
            # Add plain text part
            text_part = MimeText(email_task['body_text'], 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Add HTML part
            html_part = MimeText(email_task['body_html'], 'html', 'utf-8')
            msg.attach(html_part)
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.reliability_manager.smtp_server, self.reliability_manager.smtp_port)
            
            if self.reliability_manager.use_tls:
                server.starttls()
            
            # Authenticate
            server.login(self.reliability_manager.smtp_username, self.reliability_manager.smtp_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            # Add delay between emails
            time.sleep(self.reliability_manager.min_delay_between_emails)
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False
    
    def _process_retry_queue(self):
        """Process failed emails for retry"""
        while True:
            try:
                if self.reliability_manager.dead_letter_queue:
                    # Process dead letter queue periodically
                    failed_emails = self.reliability_manager.dead_letter_queue.copy()
                    self.reliability_manager.dead_letter_queue.clear()
                    
                    for email_task in failed_emails:
                        # Reset attempt count and requeue
                        email_task['attempts'] = 0
                        email_task['status'] = 'requeued'
                        priority = self._get_priority_value(email_task['priority'])
                        self.reliability_manager.email_queue.put((priority, email_task))
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error processing retry queue: {e}")
                time.sleep(60)
    
    def _cleanup_old_tracking(self):
        """Clean up old tracking data"""
        while True:
            try:
                cutoff_time = datetime.now() - timedelta(days=7)
                
                with self.reliability_manager.tracking_lock:
                    old_tracking_ids = [
                        tracking_id for tracking_id, data in self.reliability_manager.delivery_tracking.items()
                        if data['timestamp'] < cutoff_time
                    ]
                    
                    for tracking_id in old_tracking_ids:
                        del self.reliability_manager.delivery_tracking[tracking_id]
                
                logger.info(f"Cleaned up {len(old_tracking_ids)} old tracking records")
                time.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                logger.error(f"Error cleaning up tracking data: {e}")
                time.sleep(300)

# Recommended Libraries Integration
class EmailServiceWithLibraries:
    """
    Email service using professional libraries for maximum reliability
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.advanced_service = AdvancedEmailService(config)
        
    def send_with_sendgrid(self, recipient: str, subject: str, body_html: str, body_text: str = None) -> str:
        """
        Send email using SendGrid (recommended for production)
        
        Install: pip install sendgrid
        """
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            sg = sendgrid.SendGridAPIClient(api_key=self.config.get('sendgrid_api_key'))
            
            from_email = Email(self.config.get('sender_email'))
            to_email = To(recipient)
            subject = subject
            content_html = Content("text/html", body_html)
            content_text = Content("text/plain", body_text or self.advanced_service._html_to_text(body_html))
            
            mail = Mail(from_email, to_email, subject, content_text)
            mail.add_content(content_html)
            
            response = sg.send(mail)
            
            tracking_id = self.advanced_service._generate_tracking_id(recipient)
            self.advanced_service._track_delivery(tracking_id, 'delivered', f'SendGrid response: {response.status_code}')
            
            return tracking_id
            
        except ImportError:
            logger.error("SendGrid not installed. Install with: pip install sendgrid")
            return self.advanced_service.send_email_reliable(recipient, subject, body_html, body_text)
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return self.advanced_service.send_email_reliable(recipient, subject, body_html, body_text)
    
    def send_with_mailgun(self, recipient: str, subject: str, body_html: str, body_text: str = None) -> str:
        """
        Send email using Mailgun (alternative to SendGrid)
        
        Install: pip install requests
        """
        try:
            import requests
            
            mailgun_domain = self.config.get('mailgun_domain')
            mailgun_api_key = self.config.get('mailgun_api_key')
            
            response = requests.post(
                f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
                auth=("api", mailgun_api_key),
                data={
                    "from": f"{self.config.get('sender_name')} <{self.config.get('sender_email')}>",
                    "to": recipient,
                    "subject": subject,
                    "text": body_text or self.advanced_service._html_to_text(body_html),
                    "html": body_html
                }
            )
            
            tracking_id = self.advanced_service._generate_tracking_id(recipient)
            
            if response.status_code == 200:
                self.advanced_service._track_delivery(tracking_id, 'delivered', f'Mailgun response: {response.status_code}')
            else:
                self.advanced_service._track_delivery(tracking_id, 'failed', f'Mailgun error: {response.text}')
            
            return tracking_id
            
        except Exception as e:
            logger.error(f"Mailgun error: {e}")
            return self.advanced_service.send_email_reliable(recipient, subject, body_html, body_text)
    
    def send_with_aws_ses(self, recipient: str, subject: str, body_html: str, body_text: str = None) -> str:
        """
        Send email using AWS SES (for AWS deployments)
        
        Install: pip install boto3
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            ses_client = boto3.client(
                'ses',
                aws_access_key_id=self.config.get('aws_access_key_id'),
                aws_secret_access_key=self.config.get('aws_secret_access_key'),
                region_name=self.config.get('aws_region', 'us-east-1')
            )
            
            response = ses_client.send_email(
                Source=f"{self.config.get('sender_name')} <{self.config.get('sender_email')}>",
                Destination={'ToAddresses': [recipient]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': body_text or self.advanced_service._html_to_text(body_html), 'Charset': 'UTF-8'},
                        'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                    }
                }
            )
            
            tracking_id = self.advanced_service._generate_tracking_id(recipient)
            self.advanced_service._track_delivery(tracking_id, 'delivered', f'AWS SES MessageId: {response["MessageId"]}')
            
            return tracking_id
            
        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            return self.advanced_service.send_email_reliable(recipient, subject, body_html, body_text)
        except ClientError as e:
            logger.error(f"AWS SES error: {e}")
            return self.advanced_service.send_email_reliable(recipient, subject, body_html, body_text)

# Configuration for maximum reliability
RECOMMENDED_CONFIG = {
    # SMTP Configuration
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'smtp_username': 'your-email@gmail.com',
    'smtp_password': 'your-app-password',  # Use App Password, not regular password
    'sender_email': 'noreply@thesantris.com',
    'sender_name': 'Lotto Command Center',
    'use_tls': True,
    
    # Threading Configuration
    'max_email_workers': 3,  # Conservative for SMTP limits
    
    # Rate Limiting (Anti-spam)
    'max_emails_per_minute': 20,  # Conservative limit
    'max_emails_per_hour': 200,
    'min_delay_between_emails': 3,  # 3 seconds between emails
    
    # Retry Configuration
    'max_email_retries': 5,
    
    # Anti-spam Configuration
    'enable_spf_check': True,
    'enable_dkim_signing': False,  # Requires DKIM setup
    'blocked_domains': ['tempmail.org', '10minutemail.com'],  # Add known spam domains
    
    # Professional Service APIs (recommended for production)
    'sendgrid_api_key': 'your-sendgrid-api-key',
    'mailgun_domain': 'your-mailgun-domain',
    'mailgun_api_key': 'your-mailgun-api-key',
    'aws_access_key_id': 'your-aws-access-key',
    'aws_secret_access_key': 'your-aws-secret-key',
    'aws_region': 'us-east-1'
}
