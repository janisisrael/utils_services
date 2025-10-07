"""
Dedicated Email Service for Utils_services
Handles all email notifications with queue management, retry logic, and rate limiting
"""

import smtplib
import logging
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
from datetime import datetime
from typing import Dict, Any, Optional, List
import time
import threading

from ..shared.base_service import BaseNotificationService, NotificationTask, DeliveryStatus
from ..shared.queue_manager import QueueManager, QueueTask, QueuePriority

logger = logging.getLogger(__name__)

class EmailTask(NotificationTask):
    """Email-specific notification task"""
    
    def __init__(self, 
                 recipient_email: str,
                 subject: str,
                 body_html: str,
                 body_text: str = None,
                 sender_email: str = None,
                 template_name: str = None,
                 template_data: Dict[str, Any] = None,
                 priority: str = "normal",
                 max_retries: int = 3):
        
        super().__init__(
            task_type="email",
            recipient=recipient_email,
            data={
                'subject': subject,
                'body_html': body_html,
                'body_text': body_text or self._html_to_text(body_html),
                'sender_email': sender_email,
                'template_name': template_name,
                'template_data': template_data or {}
            },
            priority=priority,
            max_retries=max_retries
        )
    
    @staticmethod
    def _html_to_text(html_content: str) -> str:
        """Convert HTML to plain text (basic implementation)"""
        import re
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html_content)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

class EmailTemplateManager:
    """Manages email templates"""
    
    def __init__(self):
        self.templates = {
            'winner_notification': {
                'subject': '🎉 Congratulations! You Have a Winning Ticket!',
                'html': '''
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white;">
                        <h1 style="margin: 0; font-size: 28px;">🎉 Congratulations!</h1>
                        <p style="margin: 10px 0 0 0; font-size: 18px;">You have a winning ticket!</p>
                    </div>
                    
                    <div style="padding: 30px; background-color: #f9f9f9;">
                        <h2 style="color: #333; margin-top: 0;">Winner Details</h2>
                        
                        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Game:</strong></td>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{game}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Ticket Number:</strong></td>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{ticket_number}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Draw Date:</strong></td>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{draw_date}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Matched Numbers:</strong></td>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{match_count}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Prize Category:</strong></td>
                                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{prize_category}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{frontend_url}/tickets/{ticket_id}" 
                               style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                View Your Winning Ticket
                            </a>
                        </div>
                        
                        <p style="color: #666; font-size: 14px; margin-top: 30px;">
                            Thank you for playing with Lotto Command Center! 
                            Please check your account for more details and claim instructions.
                        </p>
                    </div>
                </body>
                </html>
                ''',
                'text': '''
🎉 Congratulations! You Have a Winning Ticket!

Winner Details:
- Game: {game}
- Ticket Number: {ticket_number}
- Draw Date: {draw_date}
- Matched Numbers: {match_count}
- Prize Category: {prize_category}

View your winning ticket: {frontend_url}/tickets/{ticket_id}

Thank you for playing with Lotto Command Center!
                '''
            }
        }
    
    def get_template(self, template_name: str) -> Optional[Dict[str, str]]:
        """Get template by name"""
        return self.templates.get(template_name)
    
    def render_template(self, template_name: str, data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Render template with data"""
        template = self.get_template(template_name)
        if not template:
            return None
        
        try:
            return {
                'subject': template['subject'].format(**data),
                'html': template['html'].format(**data),
                'text': template['text'].format(**data)
            }
        except KeyError as e:
            logger.error(f"Missing template data: {e}")
            return None

class EmailService(BaseNotificationService):
    """Dedicated email notification service"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("EmailService", config)
        
        # SMTP Configuration
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.smtp_username = config.get('smtp_username')
        self.smtp_password = config.get('smtp_password')
        self.use_tls = config.get('use_tls', True)
        self.sender_email = config.get('sender_email', self.smtp_username)
        self.sender_name = config.get('sender_name', 'Lotto Command Center')
        
        # Rate limiting
        self.max_emails_per_minute = config.get('max_emails_per_minute', 60)
        self.email_timestamps = []
        self.rate_limit_lock = threading.Lock()
        
        # Queue management
        self.queue_manager = QueueManager()
        self.email_queue = self.queue_manager.create_queue('emails')
        self.email_processor = None
        
        # Template manager
        self.template_manager = EmailTemplateManager()
        
    def initialize(self) -> bool:
        """Initialize the email service"""
        try:
            # Test SMTP connection
            if not self._test_smtp_connection():
                return False
            
            # Create queue processor
            self.email_processor = self.queue_manager.create_processor(
                name="email_processor",
                queue_name="emails",
                processor_func=self._process_email_task,
                max_workers=3
            )
            
            # Start queue processing
            self.email_processor.start()
            
            self.logger.info("Email service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize email service: {e}")
            return False
    
    def _test_smtp_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            server.quit()
            self.logger.info("SMTP connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"SMTP connection test failed: {e}")
            return False
    
    def send_notification(self, task: NotificationTask) -> bool:
        """Queue email for sending"""
        try:
            # Convert to queue task
            queue_task = QueueTask(
                task_id=task.id,
                data=task.to_dict(),
                priority=self._get_queue_priority(task.priority),
                max_retries=task.max_retries
            )
            
            return self.email_queue.add(queue_task)
            
        except Exception as e:
            self.logger.error(f"Error queuing email: {e}")
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
    
    def _process_email_task(self, queue_task: QueueTask) -> bool:
        """Process email task from queue"""
        try:
            # Rate limiting check
            if not self._check_rate_limit():
                self.logger.warning("Rate limit exceeded, delaying email")
                time.sleep(1)
                return False
            
            # Extract email data
            task_data = queue_task.data
            email_data = task_data.get('data', {})
            
            recipient = task_data.get('recipient')
            subject = email_data.get('subject')
            body_html = email_data.get('body_html')
            body_text = email_data.get('body_text')
            
            # Send the email
            success = self._send_email_smtp(
                recipient=recipient,
                subject=subject,
                body_html=body_html,
                body_text=body_text
            )
            
            self.update_metrics(success)
            return success
            
        except Exception as e:
            self.logger.error(f"Error processing email task: {e}")
            self.update_metrics(False, str(e))
            return False
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        with self.rate_limit_lock:
            now = time.time()
            # Remove timestamps older than 1 minute
            self.email_timestamps = [ts for ts in self.email_timestamps if now - ts < 60]
            
            if len(self.email_timestamps) >= self.max_emails_per_minute:
                return False
            
            self.email_timestamps.append(now)
            return True
    
    def _send_email_smtp(self, 
                        recipient: str,
                        subject: str,
                        body_html: str,
                        body_text: str) -> bool:
        """Send email via SMTP"""
        try:
            # Create message
            msg = MimeMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Add text and HTML parts
            if body_text:
                part1 = MimeText(body_text, 'plain')
                msg.attach(part1)
            
            if body_html:
                part2 = MimeText(body_html, 'html')
                msg.attach(part2)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email to {recipient}: {e}")
            return False
    
    def send_winner_notification(self, winner_data: Dict[str, Any]) -> bool:
        """Send winner notification email using template"""
        try:
            # Render template
            rendered = self.template_manager.render_template('winner_notification', winner_data)
            if not rendered:
                self.logger.error("Failed to render winner notification template")
                return False
            
            # Create email task
            email_task = EmailTask(
                recipient_email=winner_data.get('user_email'),
                subject=rendered['subject'],
                body_html=rendered['html'],
                body_text=rendered['text'],
                template_name='winner_notification',
                template_data=winner_data,
                priority='high'
            )
            
            return self.send_notification(email_task)
            
        except Exception as e:
            self.logger.error(f"Error sending winner notification: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check email service health"""
        try:
            # Test SMTP connection
            smtp_healthy = self._test_smtp_connection()
            
            # Get queue stats
            queue_stats = self.email_queue.get_stats() if self.email_queue else {}
            
            return {
                'status': 'healthy' if smtp_healthy else 'unhealthy',
                'smtp_connection': 'ok' if smtp_healthy else 'failed',
                'queue_stats': queue_stats,
                'metrics': self.get_metrics(),
                'rate_limit_status': {
                    'emails_sent_last_minute': len(self.email_timestamps),
                    'rate_limit': self.max_emails_per_minute
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def stop(self) -> bool:
        """Stop the email service"""
        try:
            if self.email_processor:
                self.email_processor.stop()
            return super().stop()
        except Exception as e:
            self.logger.error(f"Error stopping email service: {e}")
            return False

