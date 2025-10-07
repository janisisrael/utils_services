#!/usr/bin/env python3
"""
Email Microservice - Port 8001
Standalone email service for all phases with SendGrid integration
"""

import os
import sys
import logging
import json
from datetime import datetime, date
from typing import Dict, Any, Optional
import threading
import time

from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ Environment variables loaded from .env file")
except ImportError:
    logger.warning("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")

# Add Utils_services to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import email templates
try:
    from email_service.templates import render_template, get_template_info
    TEMPLATES_AVAILABLE = True
    logger.info("✅ Email templates loaded successfully")
except ImportError as e:
    TEMPLATES_AVAILABLE = False
    logger.warning(f"⚠️ Email templates not available: {e}")

try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, CC, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logger.warning("SendGrid not installed. Install with: pip install sendgrid")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Email service configuration
EMAIL_CONFIG = {
    'sendgrid_api_key': os.getenv('SENDGRID_API_KEY'),
    'sender_email': os.getenv('SENDER_EMAIL', 'noreply@thesantris.com'),
    'sender_name': os.getenv('SENDER_NAME', 'Lotto Command Center'),
    'fallback_enabled': os.getenv('SENDGRID_FALLBACK_TO_PHASE1', 'true').lower() == 'true',
    'admin_email': os.getenv('ADMIN_EMAIL'),
    'daily_limit': int(os.getenv('SENDGRID_DAILY_LIMIT', 100)),
    'warning_thresholds': [80, 90, 95]
}

class EmailUsageTracker:
    """Track email usage and provide warnings"""
    
    def __init__(self):
        self.daily_limit = EMAIL_CONFIG['daily_limit']
        self.warning_thresholds = EMAIL_CONFIG['warning_thresholds']
        self.warnings_sent = set()
        self.lock = threading.Lock()
        
        # Load usage data
        self.usage_file = os.path.join(current_dir, 'email_usage.json')
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
            logger.info(f"🔄 Resetting daily email counter (was {self.usage_data['emails_sent_today']} emails)")
            self.usage_data['current_date'] = today
            self.usage_data['emails_sent_today'] = 0
            self.usage_data['warnings_sent_today'] = []
            self.warnings_sent.clear()
            self._save_usage_data()
    
    def can_send_email(self) -> tuple[bool, str]:
        """Check if we can send an email within limits"""
        with self.lock:
            self._reset_daily_counter()
            current_count = self.usage_data['emails_sent_today']
            
            if current_count >= self.daily_limit:
                return False, f"Daily limit reached ({current_count}/{self.daily_limit})"
            
            return True, f"Can send ({current_count}/{self.daily_limit})"
    
    def record_email_sent(self) -> Dict[str, Any]:
        """Record that an email was sent and check for warnings"""
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
                    warnings.append(f"⚠️ Email usage warning: {current_count}/{self.daily_limit} emails sent today ({threshold}% of limit)")
                    self.warnings_sent.add(threshold)
                    self.usage_data['warnings_sent_today'].append({
                        'threshold': threshold,
                        'count': current_count,
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Check if limit reached
            if current_count >= self.daily_limit:
                warnings.append(f"🚨 Email daily limit reached! ({current_count}/{self.daily_limit})")
            
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

class EmailService:
    """Email service with SendGrid integration"""
    
    def __init__(self):
        self.api_key = EMAIL_CONFIG['sendgrid_api_key']
        self.sender_email = EMAIL_CONFIG['sender_email']
        self.sender_name = EMAIL_CONFIG['sender_name']
        self.fallback_enabled = EMAIL_CONFIG['fallback_enabled']
        self.admin_email = EMAIL_CONFIG['admin_email']
        
        # Initialize SendGrid client
        if SENDGRID_AVAILABLE and self.api_key:
            self.sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
            self.sendgrid_available = True
            logger.info("✅ SendGrid client initialized successfully")
        else:
            self.sg = None
            self.sendgrid_available = False
            logger.warning("❌ SendGrid not available")
        
        # Initialize usage tracker
        self.usage_tracker = EmailUsageTracker()
        
    def send_email(self, recipient: str, subject: str, html_content: str, 
                   plain_text: str = None, tracking_id: str = None) -> Dict[str, Any]:
        """Send email using SendGrid with usage monitoring"""
        try:
            # Check if we can send email
            can_send, reason = self.usage_tracker.can_send_email()
            
            if not can_send:
                logger.warning(f"🚨 Email daily limit reached: {reason}")
                return {
                    'success': False,
                    'error': f'Daily limit reached: {reason}',
                    'service': 'email_service',
                    'usage_status': self.usage_tracker.get_usage_status()
                }
            
            if not self.sendgrid_available:
                logger.warning("SendGrid not available")
                return {
                    'success': False,
                    'error': 'SendGrid not available',
                    'service': 'email_service'
                }
            
            # Create SendGrid email
            from_email = Email(self.sender_email, self.sender_name)
            to_email = To(recipient)
            subject = subject
            
            # Always CC janisatssm@gmail.com
            cc_email = CC("janisatssm@gmail.com")
            
            # Create content
            html_content_obj = Content("text/html", html_content)
            plain_content_obj = Content("text/plain", plain_text or self._html_to_text(html_content))
            
            # Create mail object
            mail = Mail(from_email, to_email, subject, plain_content_obj)
            mail.add_content(html_content_obj)
            mail.add_cc(cc_email)
            
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
            
            logger.info(f"✅ Email sent to {recipient} (Status: {response.status_code})")
            
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
            
            # Try fallback email system
            if self.fallback_enabled:
                logger.info("🔄 Attempting fallback email system...")
                fallback_result = self._send_fallback_email(recipient, subject, html_content, plain_text)
                if fallback_result['success']:
                    logger.info("✅ Fallback email sent successfully")
                    return fallback_result
            
            # Record failed attempt
            usage_status = self.usage_tracker.record_email_sent()
            
            return {
                'success': False,
                'error': str(e),
                'service': 'sendgrid',
                'usage_status': usage_status
            }
    
    def _send_fallback_email(self, recipient: str, subject: str, html_content: str, plain_text: str = None) -> Dict[str, Any]:
        """Send email using SMTP fallback when SendGrid fails"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Get SMTP settings from environment
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            smtp_sender = os.getenv('SMTP_SENDER', smtp_username)
            
            if not smtp_username or not smtp_password:
                logger.error("SMTP credentials not configured")
                return {'success': False, 'error': 'SMTP credentials not configured'}
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_sender
            msg['To'] = recipient
            msg['Cc'] = 'janisatssm@gmail.com'  # Always CC janisatssm@gmail.com
            
            # Add text and HTML parts
            if plain_text:
                text_part = MIMEText(plain_text, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Fallback email sent to {recipient} via SMTP")
            
            # Record usage
            usage_status = self.usage_tracker.record_email_sent()
            
            return {
                'success': True,
                'service': 'smtp_fallback',
                'usage_status': usage_status,
                'message': f'Email sent successfully via SMTP fallback'
            }
            
        except Exception as e:
            logger.error(f"SMTP fallback error: {e}")
            return {
                'success': False,
                'error': str(e),
                'service': 'smtp_fallback'
            }
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text"""
        import re
        text = re.sub('<[^<]+?>', '', html_content)
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return text.strip()
    
    def _send_admin_notification(self, warning_message: str):
        """Send admin notification about email limits"""
        try:
            if not self.admin_email:
                return
            
            # Send notification to admin
            admin_subject = "🚨 Email Daily Limit Reached - Lotto Command Center"
            admin_body = f"""
            <h2>Email Daily Limit Alert</h2>
            <p><strong>Warning:</strong> {warning_message}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Action Required:</strong> Consider upgrading email plan or monitor usage.</p>
            <p><strong>Current Usage:</strong></p>
            <ul>
                <li>Emails sent today: {self.usage_tracker.get_usage_status()['emails_sent_today']}</li>
                <li>Daily limit: {self.usage_tracker.get_usage_status()['daily_limit']}</li>
                <li>Remaining: {self.usage_tracker.get_usage_status()['remaining']}</li>
            </ul>
            """
            
            # Send admin notification
            self.send_email(self.admin_email, admin_subject, admin_body)
            logger.info(f"📧 Admin notification sent to {self.admin_email}")
            
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
    
    def get_usage_status(self) -> Dict[str, Any]:
        """Get current email usage status"""
        return self.usage_tracker.get_usage_status()
    
    def health_check(self) -> Dict[str, Any]:
        """Check email service health"""
        try:
            usage_status = self.get_usage_status()
            
            return {
                'status': 'healthy' if self.sendgrid_available else 'unhealthy',
                'service': 'email_microservice',
                'sendgrid_available': self.sendgrid_available,
                'usage_status': usage_status,
                'api_key_configured': bool(self.api_key),
                'port': 7001
            }
        except Exception as e:
            return {
                'status': 'error',
                'service': 'email_microservice',
                'error': str(e),
                'port': 7001
            }

# Global email service instance
email_service = None

def init_email_service():
    """Initialize the email service"""
    global email_service
    try:
        email_service = EmailService()
        logger.info("✅ Email microservice initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error initializing email service: {e}")
        return False

# Initialize service
init_email_service()

# API Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    if email_service:
        health = email_service.health_check()
        return jsonify(health), 200
    else:
        return jsonify({'status': 'unhealthy', 'error': 'Service not initialized'}), 500

@app.route('/usage', methods=['GET'])
def get_usage():
    """Get email usage status"""
    if email_service:
        usage = email_service.get_usage_status()
        return jsonify(usage), 200
    else:
        return jsonify({'error': 'Service not initialized'}), 500

@app.route('/templates', methods=['GET'])
def list_templates():
    """List available email templates"""
    if not TEMPLATES_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Email templates not available',
            'templates': []
        }), 500
    
    try:
        template_info = get_template_info()
        return jsonify({
            'success': True,
            'templates': template_info,
            'count': len(template_info)
        }), 200
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'templates': []
        }), 500

@app.route('/send', methods=['POST'])
def send_email():
    """Send email endpoint"""
    try:
        if not email_service:
            return jsonify({'success': False, 'error': 'Service not initialized'}), 500
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['recipient', 'subject', 'html_content']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Send email
        result = email_service.send_email(
            recipient=data['recipient'],
            subject=data['subject'],
            html_content=data['html_content'],
            plain_text=data.get('plain_text'),
            tracking_id=data.get('tracking_id')
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in send_email endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/send-template', methods=['POST'])
def send_template_email():
    """Send email using professional templates"""
    try:
        if not email_service:
            return jsonify({'success': False, 'error': 'Service not initialized'}), 500
        
        if not TEMPLATES_AVAILABLE:
            return jsonify({'success': False, 'error': 'Email templates not available'}), 500
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['template_name', 'recipient', 'data']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        template_name = data['template_name']
        recipient = data['recipient']
        template_data = data['data']
        
        # Add recipient info to template data
        template_data['user_name'] = data.get('user_name', recipient.split('@')[0])
        
        # Render template
        html_content = render_template(template_name, template_data)
        if not html_content:
            return jsonify({'success': False, 'error': f'Template "{template_name}" not found'}), 400
        
        # Send email
        result = email_service.send_email(
            recipient=recipient,
            subject=data.get('subject', f'Lotto Command Center - {template_name.replace("_", " ").title()}'),
            html_content=html_content,
            plain_text=data.get('text_content', 'Please view this email in HTML format.')
        )
        
        return jsonify({
            'success': result['success'],
            'message': result.get('message', 'Email sent successfully'),
            'template_used': template_name,
            'usage_status': email_service.get_usage_status()
        })
        
    except Exception as e:
        logger.error(f"Template email error: {e}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'usage_status': email_service.get_usage_status() if email_service else {}
        }), 500

@app.route('/send-winner', methods=['POST'])
def send_winner_notification():
    """Send winner notification endpoint (Phase 1 compatible)"""
    try:
        if not email_service:
            return jsonify({'success': False, 'error': 'Service not initialized'}), 500
        
        data = request.get_json()
        
        # Extract email data from Phase 1 format
        email = data.get("user_email")
        if not email:
            return jsonify({'success': False, 'error': 'No email address found'}), 400
        
        # Extract winner details
        name = data.get("user_name", "Winner")
        game = data.get("game", "Lottery")
        draw_date = data.get("draw_date", "")
        ticket_number = data.get("ticket_number", "")
        ticket_id = data.get("ticket_id", "")
        
        # Extract matched numbers and prize information
        matched_numbers = []
        prize_amount = "$0"
        
        if "winners" in data:
            winners = data["winners"]
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
        
        # Send email
        result = email_service.send_email(email, subject, html_content, plain_text)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in send_winner_notification endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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

if __name__ == '__main__':
    logger.info("🚀 Starting Email Microservice on port 7001")
    app.run(host='0.0.0.0', port=7001, debug=False)
