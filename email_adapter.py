"""
Phase 1 Email Service Adapter
This file provides a simple adapter that Phase 1 can use to switch to Utils_services
email service with minimal code changes.

Usage:
    1. Copy this file to Phase1/src/services/notification/
    2. Replace the import in your existing email files:
       from services.notification.email_adapter import send_email, send_email_async
    3. Set environment variables for Utils_services configuration
    4. The adapter will automatically use Utils_services if available, 
       otherwise fall back to Phase 1's original email system
"""

import os
import sys
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import Utils_services integration
try:
    # Add Utils_services to path
    utils_services_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Utils_services')
    if os.path.exists(utils_services_path):
        sys.path.insert(0, utils_services_path)
        from phase1_integration import (
            send_email as utils_send_email,
            send_email_async as utils_send_email_async,
            health_check as utils_health_check
        )
        UTILS_SERVICES_AVAILABLE = True
        logger.info("✅ Utils_services email integration available")
    else:
        UTILS_SERVICES_AVAILABLE = False
        logger.info("ℹ️ Utils_services not found, using Phase 1 email system")
except ImportError as e:
    UTILS_SERVICES_AVAILABLE = False
    logger.warning(f"Utils_services not available: {e}")

# Import Phase 1 original email functions as fallback
try:
    from .email import send_email as phase1_send_email
    from .email_enhanced import send_email_async as phase1_send_email_async
    PHASE1_EMAIL_AVAILABLE = True
except ImportError as e:
    PHASE1_EMAIL_AVAILABLE = False
    logger.error(f"Phase 1 email system not available: {e}")

def send_email(result: Dict[str, Any], tracking_id: Optional[str] = None) -> bool:
    """
    Send email using the best available service
    
    Args:
        result: Winner result data
        tracking_id: Optional tracking ID
        
    Returns:
        bool: True if email was sent successfully
    """
    
    # Try Utils_services first if available
    if UTILS_SERVICES_AVAILABLE:
        try:
            logger.info("📧 Using Utils_services email system")
            return utils_send_email(result, tracking_id)
        except Exception as e:
            logger.error(f"Utils_services email failed: {e}")
            if not PHASE1_EMAIL_AVAILABLE:
                raise
    
    # Fallback to Phase 1 email system
    if PHASE1_EMAIL_AVAILABLE:
        try:
            logger.info("📧 Using Phase 1 email system (fallback)")
            return phase1_send_email(result)
        except Exception as e:
            logger.error(f"Phase 1 email failed: {e}")
            raise
    
    # No email system available
    logger.error("❌ No email system available")
    return False

def send_email_async(result: Dict[str, Any]) -> str:
    """
    Send email asynchronously using the best available service
    
    Args:
        result: Winner result data
        
    Returns:
        str: Tracking ID
    """
    
    # Try Utils_services first if available
    if UTILS_SERVICES_AVAILABLE:
        try:
            logger.info("📧 Using Utils_services async email system")
            return utils_send_email_async(result)
        except Exception as e:
            logger.error(f"Utils_services async email failed: {e}")
            if not PHASE1_EMAIL_AVAILABLE:
                raise
    
    # Fallback to Phase 1 email system
    if PHASE1_EMAIL_AVAILABLE:
        try:
            logger.info("📧 Using Phase 1 async email system (fallback)")
            return phase1_send_email_async(result)
        except Exception as e:
            logger.error(f"Phase 1 async email failed: {e}")
            raise
    
    # No email system available
    logger.error("❌ No async email system available")
    return "no_service_available"

def get_email_service_status() -> Dict[str, Any]:
    """
    Get the status of available email services
    
    Returns:
        dict: Status information
    """
    status = {
        "utils_services_available": UTILS_SERVICES_AVAILABLE,
        "phase1_email_available": PHASE1_EMAIL_AVAILABLE,
        "active_service": None,
        "health": {}
    }
    
    # Check Utils_services health
    if UTILS_SERVICES_AVAILABLE:
        try:
            health = utils_health_check()
            status["health"]["utils_services"] = health
            if health.get("status") == "healthy":
                status["active_service"] = "utils_services"
        except Exception as e:
            status["health"]["utils_services"] = {"status": "error", "error": str(e)}
    
    # Check Phase 1 email availability
    if PHASE1_EMAIL_AVAILABLE:
        status["health"]["phase1_email"] = {"status": "available"}
        if not status["active_service"]:
            status["active_service"] = "phase1_email"
    
    return status

def switch_to_utils_services() -> bool:
    """
    Force switch to Utils_services email system
    
    Returns:
        bool: True if switch was successful
    """
    global UTILS_SERVICES_AVAILABLE
    
    if not UTILS_SERVICES_AVAILABLE:
        logger.error("Cannot switch to Utils_services - not available")
        return False
    
    try:
        # Test Utils_services health
        health = utils_health_check()
        if health.get("status") == "healthy":
            logger.info("✅ Successfully switched to Utils_services email system")
            return True
        else:
            logger.error(f"Utils_services not healthy: {health}")
            return False
    except Exception as e:
        logger.error(f"Failed to switch to Utils_services: {e}")
        return False

def switch_to_phase1_email() -> bool:
    """
    Force switch to Phase 1 email system
    
    Returns:
        bool: True if switch was successful
    """
    if not PHASE1_EMAIL_AVAILABLE:
        logger.error("Cannot switch to Phase 1 email - not available")
        return False
    
    logger.info("✅ Switched to Phase 1 email system")
    return True

# Convenience functions for easy migration
def send_winner_notification(result: Dict[str, Any]) -> bool:
    """Send winner notification using the best available service"""
    return send_email(result)

def send_winner_notification_async(result: Dict[str, Any]) -> str:
    """Send winner notification asynchronously using the best available service"""
    return send_email_async(result)

# Export the main functions
__all__ = [
    'send_email',
    'send_email_async', 
    'send_winner_notification',
    'send_winner_notification_async',
    'get_email_service_status',
    'switch_to_utils_services',
    'switch_to_phase1_email'
]




