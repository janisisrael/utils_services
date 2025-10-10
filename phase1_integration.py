"""
Phase 1 Integration Layer for Utils_services Email Service
This module provides a drop-in replacement for Phase 1's email functionality
without requiring any changes to Phase 1 code.

Usage in Phase 1:
    from utils_services.phase1_integration import send_email, send_email_async
    
    # Replace existing send_email calls
    send_email(result)  # Same interface as Phase 1
    
    # Or use async version for better performance
    tracking_id = send_email_async(result)
"""

import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import traceback

# Add Utils_services to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from email_service.email_service import EmailService, EmailTask
    from email_service.templates import get_winning_notification_template, get_new_draw_results_template
    from shared.base_service import DeliveryStatus
    UTILS_SERVICES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Utils_services not available: {e}")
    UTILS_SERVICES_AVAILABLE = False

logger = logging.getLogger(__name__)

# Global email service instance
_email_service = None

def get_email_service() -> Optional[EmailService]:
    """Get or initialize the email service instance"""
    global _email_service
    
    if not UTILS_SERVICES_AVAILABLE:
        logger.warning("Utils_services not available, falling back to Phase 1 email")
        return None
    
    if _email_service is None:
        try:
            # Email service configuration
            email_config = {
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.getenv('SMTP_PORT', 587)),
                'smtp_username': os.getenv('SMTP_USERNAME'),
                'smtp_password': os.getenv('SMTP_PASSWORD'),
                'sender_email': os.getenv('SENDER_EMAIL'),
                'sender_name': os.getenv('SENDER_NAME', 'Lotto Command Center'),
                'use_tls': os.getenv('USE_TLS', 'true').lower() == 'true',
                'max_emails_per_minute': int(os.getenv('MAX_EMAILS_PER_MINUTE', 60))
            }
            
            _email_service = EmailService(email_config)
            if not _email_service.initialize():
                logger.error("Failed to initialize Utils_services email service")
                _email_service = None
                return None
                
            logger.info("✅ Utils_services email service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Utils_services email service: {e}")
            _email_service = None
    
    return _email_service

def send_email(result: Dict[str, Any], tracking_id: Optional[str] = None) -> bool:
    """
    Send email using Utils_services (drop-in replacement for Phase 1)
    
    Args:
        result: Winner result data (same format as Phase 1)
        tracking_id: Optional tracking ID for async operations
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        email_service = get_email_service()
        
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
                # Handle grouped winners
                for game_name, game_winners in winners.items():
                    if game_winners and len(game_winners) > 0:
                        winner = game_winners[0]  # Get first winner
                        matched_numbers = winner.get("matched_numbers", [])
                        prize_amount = winner.get("prize_amount", "$0")
                        break
            elif isinstance(winners, list) and len(winners) > 0:
                # Handle list of winners
                winner = winners[0]
                matched_numbers = winner.get("matched_numbers", [])
                prize_amount = winner.get("prize_amount", "$0")
        
        # Build template data
        template_data = {
            "user_name": name,
            "game": game,
            "draw_date": draw_date,
            "ticket_number": ticket_number,
            "matched_numbers": matched_numbers,
            "prize_amount": prize_amount,
            "ticket_id": ticket_id
        }
        
        # Generate HTML content using Utils_services template
        html_content = get_winning_notification_template(**template_data)
        
        # Generate plain text content
        plain_text = _build_plain_text_email(result)
        
        # Create email task
        subject = f'You Have a Winner in {game}!'
        
        email_task = EmailTask(
            recipient_email=email,
            subject=subject,
            body_html=html_content,
            body_text=plain_text,
            template_name="winning_notification",
            template_data=template_data,
            priority="high"  # Winner notifications are high priority
        )
        
        # Send email
        delivery_result = email_service.send_notification(email_task)
        
        if delivery_result.status == DeliveryStatus.DELIVERED:
            logger.info(f"✅ Email sent successfully to {email} via Utils_services")
            return True
        else:
            logger.error(f"❌ Failed to send email to {email}: {delivery_result.error}")
            return False
            
    except Exception as e:
        logger.error(f"Error in Utils_services send_email: {e}")
        logger.debug(traceback.format_exc())
        
        # Fallback to Phase 1 email system
        logger.info("Falling back to Phase 1 email system due to error")
        return _fallback_to_phase1_email(result)

def send_email_async(result: Dict[str, Any]) -> str:
    """
    Send email asynchronously using Utils_services
    
    Args:
        result: Winner result data
        
    Returns:
        str: Tracking ID for the email
    """
    try:
        email_service = get_email_service()
        
        if email_service is None:
            # Fallback to Phase 1 email system
            logger.info("Falling back to Phase 1 email system for async")
            return _fallback_to_phase1_email_async(result)
        
        # Generate tracking ID
        email = result.get("user_email", "unknown")
        tracking_id = f"utils_email_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(email)}"
        
        # Extract email data (same as send_email)
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
        
        # Build template data
        template_data = {
            "user_name": name,
            "game": game,
            "draw_date": draw_date,
            "ticket_number": ticket_number,
            "matched_numbers": matched_numbers,
            "prize_amount": prize_amount,
            "ticket_id": ticket_id
        }
        
        # Generate HTML content
        html_content = get_winning_notification_template(**template_data)
        plain_text = _build_plain_text_email(result)
        
        # Create email task with tracking
        subject = f'You Have a Winner in {game}!'
        
        email_task = EmailTask(
            recipient_email=email,
            subject=subject,
            body_html=html_content,
            body_text=plain_text,
            template_name="winning_notification",
            template_data=template_data,
            priority="high"
        )
        
        # Set tracking ID
        email_task.tracking_id = tracking_id
        
        # Queue email for async processing
        email_service.queue_notification(email_task)
        
        logger.info(f"📧 Email queued for async delivery to {email} (ID: {tracking_id})")
        return tracking_id
        
    except Exception as e:
        logger.error(f"Error in Utils_services send_email_async: {e}")
        logger.debug(traceback.format_exc())
        
        # Fallback to Phase 1 email system
        return _fallback_to_phase1_email_async(result)

def _build_plain_text_email(result: Dict[str, Any]) -> str:
    """Build plain text email content"""
    name = result.get("user_name", "Winner")
    game = result.get("game", "Lottery")
    draw_date = result.get("draw_date", "")
    ticket_number = result.get("ticket_number", "")
    
    plain_text = f"""
Congratulations {name}!

You have a winning ticket in {game}!

Draw Date: {draw_date}
Ticket Number: {ticket_number}

Please check your account at https://www.thesantris.com for more details.

Best regards,
Lotto Command Center Team
"""
    return plain_text.strip()

def _fallback_to_phase1_email(result: Dict[str, Any]) -> bool:
    """Fallback to Phase 1 email system"""
    try:
        # Import Phase 1 email function
        from services.notification.email import send_email as phase1_send_email
        return phase1_send_email(result)
    except Exception as e:
        logger.error(f"Phase 1 email fallback failed: {e}")
        return False

def _fallback_to_phase1_email_async(result: Dict[str, Any]) -> str:
    """Fallback to Phase 1 async email system"""
    try:
        # Import Phase 1 async email function
        from services.notification.email_enhanced import send_email_async as phase1_send_email_async
        return phase1_send_email_async(result)
    except Exception as e:
        logger.error(f"Phase 1 async email fallback failed: {e}")
        return f"fallback_error_{datetime.now().strftime('%Y%m%d%H%M%S')}"

def get_email_status(tracking_id: str) -> Dict[str, Any]:
    """
    Get the status of an email by tracking ID
    
    Args:
        tracking_id: Email tracking ID
        
    Returns:
        dict: Status information
    """
    try:
        email_service = get_email_service()
        
        if email_service is None:
            return {"status": "service_unavailable", "error": "Utils_services not available"}
        
        # Get status from email service
        status = email_service.get_delivery_status(tracking_id)
        
        return {
            "tracking_id": tracking_id,
            "status": status.status.value if status else "unknown",
            "error": status.error if status else None,
            "timestamp": status.timestamp if status else None
        }
        
    except Exception as e:
        logger.error(f"Error getting email status: {e}")
        return {"status": "error", "error": str(e)}

def health_check() -> Dict[str, Any]:
    """
    Check the health of the Utils_services email system
    
    Returns:
        dict: Health status information
    """
    try:
        email_service = get_email_service()
        
        if email_service is None:
            return {
                "status": "unhealthy",
                "service": "Utils_services",
                "error": "Service not available",
                "fallback": "Phase 1 email system"
            }
        
        # Test email service health
        is_healthy = email_service.is_healthy()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "Utils_services",
            "email_service": is_healthy,
            "fallback": "Phase 1 email system"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "Utils_services",
            "error": str(e),
            "fallback": "Phase 1 email system"
        }

# Convenience functions for easy integration
def send_winner_notification(result: Dict[str, Any]) -> bool:
    """Convenience function for sending winner notifications"""
    return send_email(result)

def send_winner_notification_async(result: Dict[str, Any]) -> str:
    """Convenience function for sending winner notifications asynchronously"""
    return send_email_async(result)

def send_new_draw_notification(user_email: str, game: str, draw_date: str, 
                              winning_numbers: str, jackpot_amount: str) -> bool:
    """
    Send new draw results notification
    
    Args:
        user_email: Recipient email
        game: Game name
        draw_date: Draw date
        winning_numbers: Winning numbers
        jackpot_amount: Jackpot amount
        
    Returns:
        bool: True if sent successfully
    """
    try:
        email_service = get_email_service()
        
        if email_service is None:
            logger.warning("Utils_services not available for new draw notification")
            return False
        
        # Generate HTML content
        html_content = get_new_draw_results_template(
            user_name="Player",
            game=game,
            draw_date=draw_date,
            winning_numbers=winning_numbers,
            jackpot_amount=jackpot_amount
        )
        
        # Create email task
        email_task = EmailTask(
            recipient_email=user_email,
            subject=f'New {game} Draw Results - {draw_date}',
            body_html=html_content,
            template_name="new_draw_results",
            priority="normal"
        )
        
        # Send email
        delivery_result = email_service.send_notification(email_task)
        
        if delivery_result.status == DeliveryStatus.DELIVERED:
            logger.info(f"✅ New draw notification sent to {user_email}")
            return True
        else:
            logger.error(f"❌ Failed to send new draw notification to {user_email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending new draw notification: {e}")
        return False




