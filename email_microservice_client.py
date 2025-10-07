"""
Email Microservice Client for Phase 1
This module provides a client to communicate with the email microservice running on port 8001
"""

import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailMicroserviceClient:
    """Client for communicating with the email microservice"""
    
    def __init__(self, base_url: str = "http://localhost:7001"):
        self.base_url = base_url.rstrip('/')
        self.timeout = 30  # 30 second timeout
        
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to email microservice"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Cannot connect to email microservice at {self.base_url}")
            return {'success': False, 'error': 'Email microservice unavailable'}
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout connecting to email microservice")
            return {'success': False, 'error': 'Email microservice timeout'}
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP error from email microservice: {e}")
            return {'success': False, 'error': f'HTTP error: {e}'}
        except Exception as e:
            logger.error(f"❌ Error communicating with email microservice: {e}")
            return {'success': False, 'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check email microservice health"""
        return self._make_request('GET', '/health')
    
    def get_usage_status(self) -> Dict[str, Any]:
        """Get email usage status"""
        return self._make_request('GET', '/usage')
    
    def send_email(self, recipient: str, subject: str, html_content: str, 
                   plain_text: str = None, tracking_id: str = None) -> Dict[str, Any]:
        """Send email via microservice"""
        data = {
            'recipient': recipient,
            'subject': subject,
            'html_content': html_content,
            'plain_text': plain_text,
            'tracking_id': tracking_id
        }
        return self._make_request('POST', '/send', data)
    
    def send_winner_notification(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Send winner notification (Phase 1 compatible format)"""
        return self._make_request('POST', '/send-winner', result)

# Global client instance
_email_client = None

def get_email_client() -> EmailMicroserviceClient:
    """Get or create email microservice client"""
    global _email_client
    
    if _email_client is None:
        # Get base URL from environment or use default
        import os
        base_url = os.getenv('EMAIL_MICROSERVICE_URL', 'http://localhost:7001')
        _email_client = EmailMicroserviceClient(base_url)
        logger.info(f"✅ Email microservice client initialized: {base_url}")
    
    return _email_client

def send_email(result: Dict[str, Any], tracking_id: Optional[str] = None) -> bool:
    """
    Send email using email microservice (drop-in replacement for Phase 1)
    
    Args:
        result: Winner result data (same format as Phase 1)
        tracking_id: Optional tracking ID
        
    Returns:
        bool: True if email was sent successfully
    """
    try:
        client = get_email_client()
        
        # Send winner notification via microservice
        response = client.send_winner_notification(result)
        
        if response.get('success'):
            logger.info(f"✅ Email sent via microservice: {response.get('message')}")
            
            # Log any warnings
            usage_status = response.get('usage_status', {})
            for warning in usage_status.get('warnings', []):
                logger.warning(warning)
            
            return True
        else:
            logger.error(f"❌ Email microservice failed: {response.get('error')}")
            
            # Fallback to Phase 1 email system
            logger.info("🔄 Falling back to Phase 1 email system")
            return _fallback_to_phase1_email(result)
            
    except Exception as e:
        logger.error(f"Error in microservice send_email: {e}")
        return _fallback_to_phase1_email(result)

def send_email_async(result: Dict[str, Any]) -> str:
    """
    Send email asynchronously using email microservice
    
    Args:
        result: Winner result data
        
    Returns:
        str: Tracking ID
    """
    try:
        client = get_email_client()
        
        # Generate tracking ID
        email = result.get("user_email", "unknown")
        tracking_id = f"microservice_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(email)}"
        
        # Send email
        success = send_email(result, tracking_id)
        
        if success:
            logger.info(f"📧 Microservice async email sent (ID: {tracking_id})")
        else:
            logger.error(f"❌ Microservice async email failed (ID: {tracking_id})")
        
        return tracking_id
        
    except Exception as e:
        logger.error(f"Error in microservice send_email_async: {e}")
        return _fallback_to_phase1_email_async(result)

def get_email_service_status() -> Dict[str, Any]:
    """
    Get email service status including microservice health
    
    Returns:
        dict: Status information
    """
    try:
        client = get_email_client()
        
        # Get microservice health
        health = client.health_check()
        usage = client.get_usage_status()
        
        return {
            "status": health.get("status", "unknown"),
            "service": "email_microservice",
            "microservice_url": client.base_url,
            "sendgrid_available": health.get("sendgrid_available", False),
            "usage_status": usage,
            "api_key_configured": health.get("api_key_configured", False)
        }
        
    except Exception as e:
        logger.error(f"Error getting email service status: {e}")
        return {
            "status": "error",
            "service": "email_microservice",
            "error": str(e)
        }

def get_email_usage() -> Dict[str, Any]:
    """
    Get email usage information from microservice
    
    Returns:
        dict: Usage information
    """
    try:
        client = get_email_client()
        return client.get_usage_status()
    except Exception as e:
        logger.error(f"Error getting email usage: {e}")
        return {"error": str(e)}

def _fallback_to_phase1_email(result: Dict[str, Any]) -> bool:
    """Fallback to Phase 1 email system"""
    try:
        # Import Phase 1 email function
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Phase1', 'src'))
        from services.notification.email import send_email as phase1_send_email
        return phase1_send_email(result)
    except Exception as e:
        logger.error(f"Phase 1 email fallback failed: {e}")
        return False

def _fallback_to_phase1_email_async(result: Dict[str, Any]) -> str:
    """Fallback to Phase 1 async email system"""
    try:
        # Import Phase 1 async email function
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Phase1', 'src'))
        from services.notification.email_enhanced import send_email_async as phase1_send_email_async
        return phase1_send_email_async(result)
    except Exception as e:
        logger.error(f"Phase 1 async email fallback failed: {e}")
        return f"fallback_error_{datetime.now().strftime('%Y%m%d%H%M%S')}"

# Convenience functions for easy integration
def send_winner_notification(result: Dict[str, Any]) -> bool:
    """Send winner notification using email microservice"""
    return send_email(result)

def send_winner_notification_async(result: Dict[str, Any]) -> str:
    """Send winner notification asynchronously using email microservice"""
    return send_email_async(result)

# Export main functions
__all__ = [
    'send_email',
    'send_email_async',
    'send_winner_notification',
    'send_winner_notification_async',
    'get_email_service_status',
    'get_email_usage',
    'EmailMicroserviceClient'
]
