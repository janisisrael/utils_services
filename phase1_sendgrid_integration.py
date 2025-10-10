"""
SendGrid Integration for Phase 1
Drop-in replacement for Phase 1 email system with SendGrid and free tier monitoring
"""

import os
import sys
import logging
from typing import Dict, Any, Optional

# Add Utils_services to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from sendgrid_integration import (
        send_email_with_sendgrid,
        get_sendgrid_usage_status,
        get_sendgrid_health
    )
    SENDGRID_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SendGrid integration not available: {e}")
    SENDGRID_INTEGRATION_AVAILABLE = False

logger = logging.getLogger(__name__)

def send_email(result: Dict[str, Any], tracking_id: Optional[str] = None) -> bool:
    """
    Send email using SendGrid (drop-in replacement for Phase 1 send_email)
    
    Args:
        result: Winner result data (same format as Phase 1)
        tracking_id: Optional tracking ID
        
    Returns:
        bool: True if email was sent successfully
    """
    try:
        if not SENDGRID_INTEGRATION_AVAILABLE:
            logger.warning("SendGrid integration not available, falling back to Phase 1")
            return _fallback_to_phase1_email(result)
        
        # Send email via SendGrid
        sendgrid_result = send_email_with_sendgrid(result, tracking_id)
        
        if sendgrid_result.get('success'):
            logger.info(f"✅ Email sent via SendGrid: {sendgrid_result.get('message')}")
            
            # Log any warnings
            usage_status = sendgrid_result.get('usage_status', {})
            for warning in usage_status.get('warnings', []):
                logger.warning(warning)
            
            return True
        else:
            logger.error(f"❌ SendGrid email failed: {sendgrid_result.get('error')}")
            
            # Check if it fell back to Phase 1
            if sendgrid_result.get('service') == 'phase1_fallback':
                return sendgrid_result.get('success', False)
            
            # Try Phase 1 fallback
            return _fallback_to_phase1_email(result)
            
    except Exception as e:
        logger.error(f"Error in SendGrid send_email: {e}")
        return _fallback_to_phase1_email(result)

def send_email_async(result: Dict[str, Any]) -> str:
    """
    Send email asynchronously using SendGrid
    
    Args:
        result: Winner result data
        
    Returns:
        str: Tracking ID
    """
    try:
        if not SENDGRID_INTEGRATION_AVAILABLE:
            logger.warning("SendGrid integration not available, falling back to Phase 1")
            return _fallback_to_phase1_email_async(result)
        
        # Generate tracking ID
        email = result.get("user_email", "unknown")
        tracking_id = f"sendgrid_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(email)}"
        
        # Send email
        success = send_email(result, tracking_id)
        
        if success:
            logger.info(f"📧 SendGrid async email sent (ID: {tracking_id})")
        else:
            logger.error(f"❌ SendGrid async email failed (ID: {tracking_id})")
        
        return tracking_id
        
    except Exception as e:
        logger.error(f"Error in SendGrid send_email_async: {e}")
        return _fallback_to_phase1_email_async(result)

def get_email_service_status() -> Dict[str, Any]:
    """
    Get email service status including SendGrid usage
    
    Returns:
        dict: Status information
    """
    try:
        if not SENDGRID_INTEGRATION_AVAILABLE:
            return {
                "status": "unavailable",
                "service": "sendgrid",
                "error": "SendGrid integration not available",
                "fallback": "Phase 1 email system"
            }
        
        # Get SendGrid health and usage
        health = get_sendgrid_health()
        usage = get_sendgrid_usage_status()
        
        return {
            "status": health.get("status", "unknown"),
            "service": "sendgrid",
            "sendgrid_available": health.get("sendgrid_available", False),
            "fallback_enabled": health.get("fallback_enabled", True),
            "usage_status": usage,
            "api_key_configured": health.get("api_key_configured", False)
        }
        
    except Exception as e:
        logger.error(f"Error getting email service status: {e}")
        return {
            "status": "error",
            "service": "sendgrid",
            "error": str(e)
        }

def get_sendgrid_usage() -> Dict[str, Any]:
    """
    Get SendGrid usage information
    
    Returns:
        dict: Usage information
    """
    try:
        if not SENDGRID_INTEGRATION_AVAILABLE:
            return {"error": "SendGrid integration not available"}
        
        return get_sendgrid_usage_status()
        
    except Exception as e:
        logger.error(f"Error getting SendGrid usage: {e}")
        return {"error": str(e)}

def _fallback_to_phase1_email(result: Dict[str, Any]) -> bool:
    """Fallback to Phase 1 email system"""
    try:
        # Import Phase 1 email function
        sys.path.append(os.path.join(current_dir, '..', 'Phase1', 'src'))
        from services.notification.email import send_email as phase1_send_email
        return phase1_send_email(result)
    except Exception as e:
        logger.error(f"Phase 1 email fallback failed: {e}")
        return False

def _fallback_to_phase1_email_async(result: Dict[str, Any]) -> str:
    """Fallback to Phase 1 async email system"""
    try:
        # Import Phase 1 async email function
        sys.path.append(os.path.join(current_dir, '..', 'Phase1', 'src'))
        from services.notification.email_enhanced import send_email_async as phase1_send_email_async
        return phase1_send_email_async(result)
    except Exception as e:
        logger.error(f"Phase 1 async email fallback failed: {e}")
        return f"fallback_error_{datetime.now().strftime('%Y%m%d%H%M%S')}"

# Convenience functions for easy integration
def send_winner_notification(result: Dict[str, Any]) -> bool:
    """Send winner notification using SendGrid"""
    return send_email(result)

def send_winner_notification_async(result: Dict[str, Any]) -> str:
    """Send winner notification asynchronously using SendGrid"""
    return send_email_async(result)

# Export main functions
__all__ = [
    'send_email',
    'send_email_async',
    'send_winner_notification',
    'send_winner_notification_async',
    'get_email_service_status',
    'get_sendgrid_usage'
]




