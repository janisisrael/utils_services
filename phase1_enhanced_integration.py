"""
Enhanced Email Service Integration for Phase 1
This module provides a drop-in replacement for Phase 1's email system with:
- Advanced threading with ThreadPoolExecutor
- Professional email service integration (SendGrid/Mailgun/AWS SES)
- Anti-spam measures and rate limiting
- Delivery guarantees with retry logic
- Comprehensive tracking and monitoring
"""

import os
import sys
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Add Utils_services to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from advanced_email_reliability import EmailServiceWithLibraries, RECOMMENDED_CONFIG
    ENHANCED_EMAIL_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Enhanced email service not available: {e}")
    ENHANCED_EMAIL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Global email service instance
_enhanced_email_service = None

def get_enhanced_email_service() -> Optional[EmailServiceWithLibraries]:
    """Get or initialize the enhanced email service"""
    global _enhanced_email_service
    
    if not ENHANCED_EMAIL_AVAILABLE:
        logger.warning("Enhanced email service not available")
        return None
    
    if _enhanced_email_service is None:
        try:
            # Merge with environment variables
            config = RECOMMENDED_CONFIG.copy()
            config.update({
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.getenv('SMTP_PORT', 587)),
                'smtp_username': os.getenv('SMTP_USERNAME'),
                'smtp_password': os.getenv('SMTP_PASSWORD'),
                'sender_email': os.getenv('SENDER_EMAIL'),
                'sender_name': os.getenv('SENDER_NAME', 'Lotto Command Center'),
                'max_emails_per_minute': int(os.getenv('MAX_EMAILS_PER_MINUTE', 20)),
                'max_emails_per_hour': int(os.getenv('MAX_EMAILS_PER_HOUR', 200)),
                'min_delay_between_emails': int(os.getenv('MIN_DELAY_BETWEEN_EMAILS', 3)),
                'sendgrid_api_key': os.getenv('SENDGRID_API_KEY'),
                'mailgun_api_key': os.getenv('MAILGUN_API_KEY'),
                'mailgun_domain': os.getenv('MAILGUN_DOMAIN'),
                'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
                'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
                'aws_region': os.getenv('AWS_REGION', 'us-east-1')
            })
            
            _enhanced_email_service = EmailServiceWithLibraries(config)
            logger.info("✅ Enhanced email service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing enhanced email service: {e}")
            _enhanced_email_service = None
    
    return _enhanced_email_service

def send_email_enhanced(result: Dict[str, Any], tracking_id: Optional[str] = None) -> bool:
    """
    Send email using enhanced reliability features
    
    Args:
        result: Winner result data (same format as Phase 1)
        tracking_id: Optional tracking ID
        
    Returns:
        bool: True if email was sent successfully
    """
    try:
        email_service = get_enhanced_email_service()
        
        if email_service is None:
            # Fallback to Phase 1 email system
            logger.info("Falling back to Phase 1 email system")
            return _fallback_to_phase1_email(result)
        
        # Extract email data from result
        email = result.get("user_email")
        if not email:
            logger.error("No email address found in result")
            return False
        
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
        
        # Generate professional email content
        subject = f'🎉 You Have a Winner in {game}!'
        html_content = _generate_professional_html_email(
            name, game, draw_date, ticket_number, matched_numbers, prize_amount, ticket_id
        )
        plain_text = _generate_plain_text_email(
            name, game, draw_date, ticket_number, matched_numbers, prize_amount
        )
        
        # Determine which service to use
        use_sendgrid = os.getenv('USE_SENDGRID', 'true').lower() == 'true'
        use_mailgun = os.getenv('USE_MAILGUN', 'false').lower() == 'true'
        use_aws_ses = os.getenv('USE_AWS_SES', 'false').lower() == 'true'
        
        # Send email using the best available service
        if use_sendgrid and email_service.config.get('sendgrid_api_key'):
            tracking_id = email_service.send_with_sendgrid(email, subject, html_content, plain_text)
        elif use_mailgun and email_service.config.get('mailgun_api_key'):
            tracking_id = email_service.send_with_mailgun(email, subject, html_content, plain_text)
        elif use_aws_ses and email_service.config.get('aws_access_key_id'):
            tracking_id = email_service.send_with_aws_ses(email, subject, html_content, plain_text)
        else:
            # Use enhanced SMTP with reliability features
            tracking_id = email_service.advanced_service.send_email_reliable(
                recipient=email,
                subject=subject,
                body_html=html_content,
                body_text=plain_text,
                priority="high"
            )
        
        logger.info(f"✅ Enhanced email sent to {email} (ID: {tracking_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error in enhanced send_email: {e}")
        logger.debug(f"Full error: {e}", exc_info=True)
        
        # Fallback to Phase 1 email system
        logger.info("Falling back to Phase 1 email system due to error")
        return _fallback_to_phase1_email(result)

def send_email_async_enhanced(result: Dict[str, Any]) -> str:
    """
    Send email asynchronously using enhanced reliability features
    
    Args:
        result: Winner result data
        
    Returns:
        str: Tracking ID for the email
    """
    try:
        email_service = get_enhanced_email_service()
        
        if email_service is None:
            # Fallback to Phase 1 email system
            logger.info("Falling back to Phase 1 email system for async")
            return _fallback_to_phase1_email_async(result)
        
        # Generate tracking ID
        email = result.get("user_email", "unknown")
        tracking_id = f"enhanced_email_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(email)}"
        
        # Use the enhanced service for async sending
        success = send_email_enhanced(result, tracking_id)
        
        if success:
            logger.info(f"📧 Enhanced async email queued for {email} (ID: {tracking_id})")
        else:
            logger.error(f"❌ Enhanced async email failed for {email} (ID: {tracking_id})")
        
        return tracking_id
        
    except Exception as e:
        logger.error(f"Error in enhanced send_email_async: {e}")
        return _fallback_to_phase1_email_async(result)

def get_email_delivery_status(tracking_id: str) -> Dict[str, Any]:
    """
    Get email delivery status with enhanced tracking
    
    Args:
        tracking_id: Email tracking ID
        
    Returns:
        dict: Status information
    """
    try:
        email_service = get_enhanced_email_service()
        
        if email_service is None:
            return {"status": "service_unavailable", "error": "Enhanced email service not available"}
        
        # Get status from enhanced service
        status = email_service.advanced_service.get_delivery_status(tracking_id)
        
        return {
            "tracking_id": tracking_id,
            "status": status.get("status", "unknown"),
            "message": status.get("message"),
            "timestamp": status.get("timestamp"),
            "service": "enhanced_email_service"
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced email status: {e}")
        return {"status": "error", "error": str(e)}

def get_email_analytics() -> Dict[str, Any]:
    """
    Get email delivery analytics
    
    Returns:
        dict: Analytics information
    """
    try:
        email_service = get_enhanced_email_service()
        
        if email_service is None:
            return {"status": "service_unavailable", "error": "Enhanced email service not available"}
        
        # Get analytics from enhanced service
        analytics = {
            "service": "enhanced_email_service",
            "delivery_stats": email_service.advanced_service.reliability_manager.delivery_tracking,
            "queue_size": email_service.advanced_service.reliability_manager.email_queue.qsize(),
            "dead_letter_queue_size": len(email_service.advanced_service.reliability_manager.dead_letter_queue),
            "rate_limit_status": {
                "emails_last_hour": len([
                    ts for ts in email_service.advanced_service.reliability_manager.email_timestamps
                    if datetime.now().timestamp() - ts < 3600
                ]),
                "emails_last_minute": len([
                    ts for ts in email_service.advanced_service.reliability_manager.email_timestamps
                    if datetime.now().timestamp() - ts < 60
                ])
            }
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting email analytics: {e}")
        return {"status": "error", "error": str(e)}

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

def _fallback_to_phase1_email(result: Dict[str, Any]) -> bool:
    """Fallback to Phase 1 email system"""
    try:
        from services.notification.email import send_email as phase1_send_email
        return phase1_send_email(result)
    except Exception as e:
        logger.error(f"Phase 1 email fallback failed: {e}")
        return False

def _fallback_to_phase1_email_async(result: Dict[str, Any]) -> str:
    """Fallback to Phase 1 async email system"""
    try:
        from services.notification.email_enhanced import send_email_async as phase1_send_email_async
        return phase1_send_email_async(result)
    except Exception as e:
        logger.error(f"Phase 1 async email fallback failed: {e}")
        return f"fallback_error_{datetime.now().strftime('%Y%m%d%H%M%S')}"

# Convenience functions for easy integration
def send_winner_notification_enhanced(result: Dict[str, Any]) -> bool:
    """Send winner notification using enhanced email service"""
    return send_email_enhanced(result)

def send_winner_notification_async_enhanced(result: Dict[str, Any]) -> str:
    """Send winner notification asynchronously using enhanced email service"""
    return send_email_async_enhanced(result)

# Export main functions
__all__ = [
    'send_email_enhanced',
    'send_email_async_enhanced',
    'send_winner_notification_enhanced',
    'send_winner_notification_async_enhanced',
    'get_email_delivery_status',
    'get_email_analytics'
]


