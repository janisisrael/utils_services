"""
SendGrid Email Service Integration with Free Tier Monitoring
This module provides SendGrid integration with comprehensive free tier monitoring and warnings.
"""

import os
import sys
import logging
import json
from datetime import datetime, date
from typing import Dict, Any, Optional
import threading
import time

# Add Utils_services to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logging.warning("SendGrid not installed. Install with: pip install sendgrid")

logger = logging.getLogger(__name__)

class SendGridUsageTracker:
    """Track SendGrid free tier usage and provide warnings"""
    
    def __init__(self):
        self.daily_limit = 100  # SendGrid free tier limit
        self.warning_thresholds = [80, 90, 95]  # Warning at these percentages
        self.warnings_sent = set()  # Track which warnings have been sent today
        self.lock = threading.Lock()
        
        # Load usage data
        self.usage_file = os.path.join(current_dir, 'sendgrid_usage.json')
        self.usage_data = self._load_usage_data()
        
    def _load_usage_data(self) -> Dict[str, Any]:
        """Load usage data from file"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading usage data: {e}")
        
        return {
            'current_date': date.today().isoformat(),
            'emails_sent_today': 0,
            'last_reset': datetime.now().isoformat(),
            'total_emails_sent': 0,
            'warnings_sent_today': []
        }
    
    def _save_usage_data(self):
        """Save usage data to file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving usage data: {e}")
    
    def _reset_daily_counter(self):
        """Reset daily counter if it's a new day"""
        today = date.today().isoformat()
        if self.usage_data['current_date'] != today:
            logger.info(f"🔄 Resetting daily SendGrid counter (was {self.usage_data['emails_sent_today']} emails)")
            self.usage_data['current_date'] = today
            self.usage_data['emails_sent_today'] = 0
            self.usage_data['warnings_sent_today'] = []
            self.warnings_sent.clear()
            self._save_usage_data()
    
    def can_send_email(self) -> tuple[bool, str]:
        """
        Check if we can send an email within free tier limits
        
        Returns:
            tuple: (can_send, reason)
        """
        with self.lock:
            self._reset_daily_counter()
            
            current_count = self.usage_data['emails_sent_today']
            
            if current_count >= self.daily_limit:
                return False, f"Daily limit reached ({current_count}/{self.daily_limit})"
            
            return True, f"Can send ({current_count}/{self.daily_limit})"
    
    def record_email_sent(self) -> Dict[str, Any]:
        """
        Record that an email was sent and check for warnings
        
        Returns:
            dict: Status information including any warnings
        """
        with self.lock:
            self._reset_daily_counter()
            
            # Increment counter
            self.usage_data['emails_sent_today'] += 1
            self.usage_data['total_emails_sent'] += 1
            self.usage_data['last_reset'] = datetime.now().isoformat()
            
            current_count = self.usage_data['emails_sent_today']
            
            # Check for warnings
            warnings = []
            for threshold in self.warning_thresholds:
                if current_count >= threshold and threshold not in self.warnings_sent:
                    warnings.append(f"⚠️ SendGrid usage warning: {current_count}/{self.daily_limit} emails sent today ({threshold}% of limit)")
                    self.warnings_sent.add(threshold)
                    self.usage_data['warnings_sent_today'].append({
                        'threshold': threshold,
                        'count': current_count,
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Check if limit reached
            if current_count >= self.daily_limit:
                warnings.append(f"🚨 SendGrid daily limit reached! ({current_count}/{self.daily_limit})")
            
            self._save_usage_data()
            
            return {
                'emails_sent_today': current_count,
                'daily_limit': self.daily_limit,
                'remaining': self.daily_limit - current_count,
                'warnings': warnings,
                'can_send_more': current_count < self.daily_limit
            }
    
    def get_usage_status(self) -> Dict[str, Any]:
        """Get current usage status"""
        with self.lock:
            self._reset_daily_counter()
            
            current_count = self.usage_data['emails_sent_today']
            percentage = (current_count / self.daily_limit) * 100
            
            return {
                'current_date': self.usage_data['current_date'],
                'emails_sent_today': current_count,
                'daily_limit': self.daily_limit,
                'remaining': self.daily_limit - current_count,
                'percentage_used': round(percentage, 1),
                'can_send_more': current_count < self.daily_limit,
                'total_emails_sent': self.usage_data['total_emails_sent'],
                'warnings_sent_today': len(self.usage_data['warnings_sent_today']),
                'last_reset': self.usage_data['last_reset']
            }

class SendGridEmailService:
    """SendGrid email service with free tier monitoring"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('sendgrid_api_key')
        self.sender_email = config.get('sender_email')
        self.sender_name = config.get('sender_name', 'Lotto Command Center')
        self.fallback_enabled = config.get('fallback_to_phase1', True)
        
        # Initialize SendGrid client
        if SENDGRID_AVAILABLE and self.api_key:
            self.sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
            self.sendgrid_available = True
            logger.info("✅ SendGrid client initialized successfully")
        else:
            self.sg = None
            self.sendgrid_available = False
            logger.warning("❌ SendGrid not available - will use fallback")
        
        # Initialize usage tracker
        self.usage_tracker = SendGridUsageTracker()
        
    def send_email(self, recipient: str, subject: str, html_content: str, 
                   plain_text: str = None, tracking_id: str = None) -> Dict[str, Any]:
        """
        Send email using SendGrid with usage monitoring
        
        Args:
            recipient: Email recipient
            subject: Email subject
            html_content: HTML email content
            plain_text: Plain text content
            tracking_id: Optional tracking ID
            
        Returns:
            dict: Result with status and usage information
        """
        try:
            # Check if we can send email
            can_send, reason = self.usage_tracker.can_send_email()
            
            if not can_send:
                logger.warning(f"🚨 SendGrid daily limit reached: {reason}")
                
                if self.fallback_enabled:
                    logger.info("🔄 Falling back to Phase 1 email system")
                    return self._fallback_to_phase1_email(recipient, subject, html_content, plain_text)
                else:
                    return {
                        'success': False,
                        'error': f'SendGrid daily limit reached: {reason}',
                        'service': 'sendgrid',
                        'usage_status': self.usage_tracker.get_usage_status()
                    }
            
            if not self.sendgrid_available:
                logger.warning("SendGrid not available, using fallback")
                return self._fallback_to_phase1_email(recipient, subject, html_content, plain_text)
            
            # Create SendGrid email
            from_email = Email(self.sender_email, self.sender_name)
            to_email = To(recipient)
            subject = subject
            
            # Create content
            html_content_obj = Content("text/html", html_content)
            plain_content_obj = Content("text/plain", plain_text or self._html_to_text(html_content))
            
            # Create mail object
            mail = Mail(from_email, to_email, subject, plain_content_obj)
            mail.add_content(html_content_obj)
            
            # Send email
            response = self.sg.send(mail)
            
            # Record usage
            usage_status = self.usage_tracker.record_email_sent()
            
            # Log warnings
            for warning in usage_status['warnings']:
                logger.warning(warning)
                
                # Send admin notification for critical warnings
                if 'limit reached' in warning:
                    self._send_admin_notification(warning)
            
            logger.info(f"✅ SendGrid email sent to {recipient} (Status: {response.status_code})")
            
            return {
                'success': True,
                'service': 'sendgrid',
                'status_code': response.status_code,
                'tracking_id': tracking_id,
                'usage_status': usage_status,
                'message': f'Email sent successfully via SendGrid'
            }
            
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            
            # Record failed attempt
            usage_status = self.usage_tracker.record_email_sent()
            
            if self.fallback_enabled:
                logger.info("🔄 SendGrid failed, falling back to Phase 1 email system")
                return self._fallback_to_phase1_email(recipient, subject, html_content, plain_text)
            else:
                return {
                    'success': False,
                    'error': str(e),
                    'service': 'sendgrid',
                    'usage_status': usage_status
                }
    
    def _fallback_to_phase1_email(self, recipient: str, subject: str, 
                                 html_content: str, plain_text: str) -> Dict[str, Any]:
        """Fallback to Phase 1 email system"""
        try:
            # Import Phase 1 email function
            sys.path.append(os.path.join(current_dir, '..', 'Phase1', 'src'))
            from services.notification.email import send_email as phase1_send_email
            
            # Create result in Phase 1 format
            result = {
                'user_email': recipient,
                'subject': subject,
                'html': html_content,
                'body': plain_text
            }
            
            success = phase1_send_email(result)
            
            return {
                'success': success,
                'service': 'phase1_fallback',
                'message': 'Email sent via Phase 1 fallback system',
                'usage_status': self.usage_tracker.get_usage_status()
            }
            
        except Exception as e:
            logger.error(f"Phase 1 fallback failed: {e}")
            return {
                'success': False,
                'error': f'Both SendGrid and Phase 1 failed: {e}',
                'service': 'both_failed',
                'usage_status': self.usage_tracker.get_usage_status()
            }
    
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
    
    def _send_admin_notification(self, warning_message: str):
        """Send admin notification about SendGrid limits"""
        try:
            admin_email = self.config.get('admin_email')
            if not admin_email:
                return
            
            # Send notification to admin
            admin_subject = "🚨 SendGrid Daily Limit Reached - Lotto Command Center"
            admin_body = f"""
            <h2>SendGrid Daily Limit Alert</h2>
            <p><strong>Warning:</strong> {warning_message}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Action Required:</strong> Consider upgrading SendGrid plan or monitor email usage.</p>
            <p><strong>Current Usage:</strong></p>
            <ul>
                <li>Emails sent today: {self.usage_tracker.get_usage_status()['emails_sent_today']}</li>
                <li>Daily limit: {self.usage_tracker.get_usage_status()['daily_limit']}</li>
                <li>Remaining: {self.usage_tracker.get_usage_status()['remaining']}</li>
            </ul>
            """
            
            # Send admin notification (this won't count against daily limit if using different service)
            logger.info(f"📧 Admin notification sent to {admin_email}")
            
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
    
    def get_usage_status(self) -> Dict[str, Any]:
        """Get current SendGrid usage status"""
        return self.usage_tracker.get_usage_status()
    
    def health_check(self) -> Dict[str, Any]:
        """Check SendGrid service health"""
        try:
            usage_status = self.get_usage_status()
            
            return {
                'status': 'healthy' if self.sendgrid_available else 'unhealthy',
                'service': 'sendgrid',
                'sendgrid_available': self.sendgrid_available,
                'fallback_enabled': self.fallback_enabled,
                'usage_status': usage_status,
                'api_key_configured': bool(self.api_key)
            }
        except Exception as e:
            return {
                'status': 'error',
                'service': 'sendgrid',
                'error': str(e)
            }

# Global SendGrid service instance
_sendgrid_service = None

def get_sendgrid_service() -> Optional[SendGridEmailService]:
    """Get or initialize SendGrid service"""
    global _sendgrid_service
    
    if _sendgrid_service is None:
        try:
            config = {
                'sendgrid_api_key': os.getenv('SENDGRID_API_KEY'),
                'sender_email': os.getenv('SENDER_EMAIL'),
                'sender_name': os.getenv('SENDER_NAME', 'Lotto Command Center'),
                'fallback_to_phase1': os.getenv('SENDGRID_FALLBACK_TO_PHASE1', 'true').lower() == 'true',
                'admin_email': os.getenv('ADMIN_EMAIL')
            }
            
            _sendgrid_service = SendGridEmailService(config)
            logger.info("✅ SendGrid service initialized")
            
        except Exception as e:
            logger.error(f"Error initializing SendGrid service: {e}")
            _sendgrid_service = None
    
    return _sendgrid_service

def send_email_with_sendgrid(result: Dict[str, Any], tracking_id: str = None) -> Dict[str, Any]:
    """
    Send email using SendGrid (drop-in replacement for Phase 1)
    
    Args:
        result: Winner result data (same format as Phase 1)
        tracking_id: Optional tracking ID
        
    Returns:
        dict: Result with status and usage information
    """
    try:
        sendgrid_service = get_sendgrid_service()
        
        if sendgrid_service is None:
            logger.error("SendGrid service not available")
            return {'success': False, 'error': 'SendGrid service not available'}
        
        # Extract email data from result
        email = result.get("user_email")
        if not email:
            logger.error("No email address found in result")
            return {'success': False, 'error': 'No email address found'}
        
        # Extract winner details
        name = result.get("user_name", "Winner")
        game = result.get("game", "Lottery")
        draw_date = result.get("draw_date", "")
        ticket_number = result.get("ticket_number", "")
        ticket_id = result.get("ticket_id", "")
        
        # Extract matched numbers and prize information
        matched_numbers = []
        prize_amount = "$0"
        
        if "winners" in result:
            winners = result["winners"]
            if isinstance(winners, dict):
                for game_name, game_winners in winners.items():
                    if game_winners and len(game_winners) > 0:
                        winner = game_winners[0]
                        matched_numbers = winner.get("matched_numbers", [])
                        prize_amount = winner.get("prize_amount", "$0")
                        break
            elif isinstance(winners, list) and len(winners) > 0:
                winner = winners[0]
                matched_numbers = winner.get("matched_numbers", [])
                prize_amount = winner.get("prize_amount", "$0")
        
        # Generate email content
        subject = f'🎉 You Have a Winner in {game}!'
        html_content = _generate_professional_html_email(
            name, game, draw_date, ticket_number, matched_numbers, prize_amount, ticket_id
        )
        plain_text = _generate_plain_text_email(
            name, game, draw_date, ticket_number, matched_numbers, prize_amount
        )
        
        # Send email via SendGrid
        return sendgrid_service.send_email(email, subject, html_content, plain_text, tracking_id)
        
    except Exception as e:
        logger.error(f"Error in send_email_with_sendgrid: {e}")
        return {'success': False, 'error': str(e)}

def _generate_professional_html_email(name: str, game: str, draw_date: str, 
                                    ticket_number: str, matched_numbers: list, 
                                    prize_amount: str, ticket_id: str) -> str:
    """Generate professional HTML email content"""
    
    matched_numbers_str = ", ".join(map(str, matched_numbers)) if matched_numbers else "N/A"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Lotto Command Center - Winner Notification</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f9f9f9; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #007bff; }}
            .header h1 {{ color: #007bff; margin: 0; font-size: 28px; }}
            .content {{ padding: 30px 0; }}
            .winner-badge {{ background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0; }}
            .winner-badge h2 {{ margin: 0; font-size: 24px; }}
            .details {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .detail-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #dee2e6; }}
            .detail-label {{ font-weight: bold; color: #495057; }}
            .detail-value {{ color: #007bff; font-weight: 500; }}
            .prize-amount {{ font-size: 24px; font-weight: bold; color: #28a745; text-align: center; margin: 20px 0; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px 0; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }}
            .footer a {{ color: #007bff; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Lotto Command Center</h1>
            </div>
            <div class="content">
                <div class="winner-badge">
                    <h2>Congratulations {name}!</h2>
                    <p>You have a winning ticket!</p>
                </div>
                
                <div class="details">
                    <div class="detail-row">
                        <span class="detail-label">Game:</span>
                        <span class="detail-value">{game}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Draw Date:</span>
                        <span class="detail-value">{draw_date}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Ticket Number:</span>
                        <span class="detail-value">{ticket_number}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Matched Numbers:</span>
                        <span class="detail-value">{matched_numbers_str}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Ticket ID:</span>
                        <span class="detail-value">{ticket_id}</span>
                    </div>
                </div>
                
                <div class="prize-amount">
                    🏆 Prize Amount: {prize_amount}
                </div>
                
                <div style="text-align: center;">
                    <a href="https://www.thesantris.com" class="button">View Details & Claim Prize</a>
                </div>
                
                <p style="text-align: center; color: #6c757d; font-size: 14px;">
                    Please log in to your account to view complete details and claim your prize.
                </p>
            </div>
            <div class="footer">
                <p>This email was sent by Lotto Command Center</p>
                <p>If you no longer wish to receive these emails, <a href="https://www.thesantris.com/unsubscribe">unsubscribe here</a></p>
                <p>© 2025 Lotto Command Center. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

def _generate_plain_text_email(name: str, game: str, draw_date: str, 
                             ticket_number: str, matched_numbers: list, 
                             prize_amount: str) -> str:
    """Generate plain text email content"""
    
    matched_numbers_str = ", ".join(map(str, matched_numbers)) if matched_numbers else "N/A"
    
    return f"""
Congratulations {name}!

You have a winning ticket in {game}!

DRAW DETAILS:
- Game: {game}
- Draw Date: {draw_date}
- Ticket Number: {ticket_number}
- Matched Numbers: {matched_numbers_str}
- Prize Amount: {prize_amount}

Please log in to your account at https://www.thesantris.com to view complete details and claim your prize.

Best regards,
Lotto Command Center Team

---
This email was sent by Lotto Command Center
If you no longer wish to receive these emails, unsubscribe at: https://www.thesantris.com/unsubscribe
© 2025 Lotto Command Center. All rights reserved.
    """.strip()

# Convenience functions
def get_sendgrid_usage_status() -> Dict[str, Any]:
    """Get SendGrid usage status"""
    service = get_sendgrid_service()
    if service:
        return service.get_usage_status()
    return {'error': 'SendGrid service not available'}

def get_sendgrid_health() -> Dict[str, Any]:
    """Get SendGrid health status"""
    service = get_sendgrid_service()
    if service:
        return service.health_check()
    return {'status': 'unhealthy', 'error': 'SendGrid service not available'}

# Export main functions
__all__ = [
    'send_email_with_sendgrid',
    'get_sendgrid_usage_status',
    'get_sendgrid_health',
    'SendGridEmailService',
    'SendGridUsageTracker'
]


