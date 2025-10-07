"""
Direct Adapter for Phase1's winner_to_user.py
Provides seamless integration with existing Phase1 winner notification system
"""

import logging
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WinnerToUserAdapter:
    """
    Adapter that integrates directly with Phase1's winner_to_user.py
    Provides the same interface but uses Utils_services internally
    """
    
    def __init__(self):
        self.utils_services_available = False
        self.dispatcher = None
        self._init_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'total_calls': 0,
            'utils_services_success': 0,
            'fallback_used': 0,
            'errors': 0
        }
    
    def _lazy_init_utils_services(self):
        """Lazy initialization of Utils_services to avoid startup dependencies"""
        if self.utils_services_available or self.dispatcher:
            return True
        
        with self._init_lock:
            # Double-check pattern
            if self.utils_services_available:
                return True
            
            try:
                # Import Utils_services
                import sys
                import os
                utils_path = os.path.dirname(os.path.dirname(__file__))
                if utils_path not in sys.path:
                    sys.path.insert(0, utils_path)
                
                from dispatcher.notification_dispatcher import NotificationDispatcher
                
                # Get Phase1 configurations
                email_config = self._get_phase1_email_config()
                notification_config = self._get_phase1_notification_config()
                
                # Initialize dispatcher
                self.dispatcher = NotificationDispatcher()
                
                if self.dispatcher.initialize(email_config, notification_config):
                    self.utils_services_available = True
                    logger.info("Utils_services notification system initialized")
                    return True
                else:
                    logger.warning("Failed to initialize Utils_services")
                    return False
                    
            except Exception as e:
                logger.debug(f"Utils_services not available: {e}")
                return False
    
    def _get_phase1_email_config(self) -> Dict[str, Any]:
        """Get email configuration from Phase1"""
        try:
            from config import app
            return {
                'smtp_server': app.config.get('MAIL_SERVER', 'smtp.gmail.com'),
                'smtp_port': app.config.get('MAIL_PORT', 587),
                'smtp_username': app.config.get('MAIL_USERNAME'),
                'smtp_password': app.config.get('MAIL_PASSWORD'),
                'use_tls': app.config.get('MAIL_USE_TLS', True),
                'sender_email': app.config.get('MAIL_USERNAME'),
                'sender_name': 'Lotto Command Center',
                'max_emails_per_minute': 60
            }
        except:
            return {'smtp_server': 'smtp.gmail.com', 'smtp_port': 587, 'use_tls': True}
    
    def _get_phase1_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration from Phase1"""
        return {
            'store_in_database': True,
            'send_via_websocket': True,
            'max_notifications_per_user_per_hour': 100
        }
    
    def enhanced_get_winner_details(self, json_data: Dict[str, Any]):
        """
        Enhanced version of get_winner_details that uses Utils_services first,
        then falls back to original Phase1 implementation
        """
        self.stats['total_calls'] += 1
        
        try:
            # Try Utils_services first
            if self._lazy_init_utils_services() and self.dispatcher:
                return self._process_with_utils_services(json_data)
            else:
                # Fall back to original implementation
                return self._fallback_to_original(json_data)
                
        except Exception as e:
            logger.error(f"Error in enhanced_get_winner_details: {e}")
            self.stats['errors'] += 1
            # Always fall back to original on error
            return self._fallback_to_original(json_data)
    
    def _process_with_utils_services(self, json_data: Dict[str, Any]):
        """Process winner notifications using Utils_services"""
        try:
            winners = json_data.get("winners", {})
            dispatch_ids = []
            
            for game, game_winners in winners.items():
                for winner in game_winners:
                    # Prepare winner data for Utils_services
                    winner_data = self._prepare_winner_data(winner, game)
                    
                    # Dispatch notification
                    dispatch_id = self.dispatcher.dispatch_winner_notification(winner_data)
                    
                    if dispatch_id:
                        dispatch_ids.append(dispatch_id)
                        
                        # Also call the original database record insertion
                        self._insert_winning_details(winner)
            
            if dispatch_ids:
                self.stats['utils_services_success'] += 1
                logger.info(f"Successfully dispatched {len(dispatch_ids)} winner notifications via Utils_services")
                
                # Return format similar to original function
                return {
                    "success": True,
                    "dispatched_notifications": dispatch_ids,
                    "system": "utils_services"
                }
            else:
                raise Exception("No dispatch IDs returned")
                
        except Exception as e:
            logger.warning(f"Utils_services processing failed: {e}")
            return self._fallback_to_original(json_data)
    
    def _prepare_winner_data(self, winner: Dict[str, Any], game: str) -> Dict[str, Any]:
        """Prepare winner data for Utils_services format"""
        
        # Get user email
        user_email = self._get_user_email(winner.get('user_id'))
        
        # Get user name
        user_name = self._get_user_name(winner.get('user_id'))
        
        return {
            'user_id': winner.get('user_id'),
            'user_email': user_email,
            'name': user_name,
            'game': game.upper(),
            'ticket_number': winner.get('ticket_number'),
            'ticket_numbers': winner.get('ticket_numbers'),
            'draw_date': winner.get('draw_date'),
            'ticket_id': winner.get('id'),
            'classic_draw': winner.get('matches', [{}])[0] if winner.get('matches') else {},
            'gold_ball_draw': winner.get('gold_ball_draw'),
            'extra_match': winner.get('extra_match'),
            'max_million': winner.get('max_million_match'),
            'frontend_url': 'https://www.thesantris.com'  # From Phase1 config
        }
    
    def _get_user_email(self, user_id: int) -> str:
        """Get user email from Phase1 database"""
        try:
            from config import get_connection
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
                result = cursor.fetchone()
                return result[0] if result else f"user_{user_id}@unknown.com"
                
        except Exception as e:
            logger.warning(f"Could not get user email for {user_id}: {e}")
            return f"user_{user_id}@unknown.com"
    
    def _get_user_name(self, user_id: int) -> str:
        """Get user name from Phase1 database"""
        try:
            from config import get_connection
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT first_name, last_name FROM users WHERE id = %s", (user_id,))
                result = cursor.fetchone()
                if result:
                    first_name = result[0] or ""
                    last_name = result[1] or ""
                    return f"{first_name} {last_name}".strip()
                return f"User {user_id}"
                
        except Exception as e:
            logger.warning(f"Could not get user name for {user_id}: {e}")
            return f"User {user_id}"
    
    def _insert_winning_details(self, winner: Dict[str, Any]):
        """Insert winning details using original Phase1 function"""
        try:
            from models.ticket.winner_record import insert_winning_details
            insert_winning_details(winner)
        except Exception as e:
            logger.warning(f"Could not insert winning details: {e}")
    
    def _fallback_to_original(self, json_data: Dict[str, Any]):
        """Fallback to original Phase1 implementation"""
        try:
            self.stats['fallback_used'] += 1
            logger.info("Using original Phase1 winner notification system")
            
            # Import and call original function
            from services.process_winner.winner_to_user import get_winner_details as original_get_winner_details
            
            # Call original implementation
            result = original_get_winner_details(json_data)
            
            return {
                "success": True,
                "result": result,
                "system": "phase1_original"
            }
            
        except Exception as e:
            logger.error(f"Original Phase1 system also failed: {e}")
            self.stats['errors'] += 1
            return {
                "success": False,
                "error": str(e),
                "system": "none"
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics"""
        total = self.stats['total_calls']
        return {
            'utils_services_available': self.utils_services_available,
            **self.stats,
            'utils_services_success_rate': (self.stats['utils_services_success'] / total * 100) if total > 0 else 0,
            'fallback_rate': (self.stats['fallback_used'] / total * 100) if total > 0 else 0,
            'error_rate': (self.stats['errors'] / total * 100) if total > 0 else 0
        }

# Global adapter instance
_winner_adapter = WinnerToUserAdapter()

def get_winner_details(json_data: Dict[str, Any]):
    """
    Drop-in replacement for Phase1's get_winner_details function
    This function can be imported and used exactly like the original
    """
    return _winner_adapter.enhanced_get_winner_details(json_data)

def get_adapter_stats() -> Dict[str, Any]:
    """Get statistics about the adapter usage"""
    return _winner_adapter.get_stats()

# Patch function for easy integration
def patch_phase1_winner_notifications():
    """
    Patches Phase1's winner_to_user module to use Utils_services
    Call this once at application startup to enable the new system
    """
    try:
        # Import Phase1 module
        from services.process_winner import winner_to_user
        
        # Store original function reference
        if not hasattr(winner_to_user, '_original_get_winner_details'):
            winner_to_user._original_get_winner_details = winner_to_user.get_winner_details
        
        # Replace with our enhanced version
        winner_to_user.get_winner_details = get_winner_details
        
        logger.info("✅ Successfully patched Phase1 winner notifications to use Utils_services")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to patch Phase1 winner notifications: {e}")
        return False

def unpatch_phase1_winner_notifications():
    """
    Removes the patch and restores original Phase1 functionality
    """
    try:
        from services.process_winner import winner_to_user
        
        if hasattr(winner_to_user, '_original_get_winner_details'):
            winner_to_user.get_winner_details = winner_to_user._original_get_winner_details
            delattr(winner_to_user, '_original_get_winner_details')
            logger.info("✅ Successfully restored original Phase1 winner notifications")
            return True
        else:
            logger.warning("No patch to remove")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to unpatch Phase1 winner notifications: {e}")
        return False

# Example usage
if __name__ == "__main__":
    print("🔗 Winner-to-User Adapter Example")
    print("=" * 40)
    
    # Example 1: Direct usage
    print("\n1. Direct Usage:")
    sample_data = {
        "winners": {
            "6-49": [{
                'id': 1,
                'user_id': 1,
                'ticket_number': 'ADAPTER-TEST-001',
                'ticket_numbers': '03-17-22-30-41-48',
                'draw_date': '2025-09-17',
                'matches': [{
                    'draw_id': 106,
                    'winning_number': '3,17,22,30,41,48',
                    'matched_count': 6,
                    'prize_category': 'Jackpot'
                }]
            }]
        },
        "number_of_winners": 1
    }
    
    result = get_winner_details(sample_data)
    print(f"Result: {result}")
    
    # Example 2: Show statistics
    print("\n2. Adapter Statistics:")
    stats = get_adapter_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Example 3: Patching demonstration
    print("\n3. Patching Example:")
    if patch_phase1_winner_notifications():
        print("✅ Patching successful - Phase1 now uses Utils_services")
        
        # Test that the patch works
        try:
            from services.process_winner.winner_to_user import get_winner_details as patched_function
            test_result = patched_function(sample_data)
            print(f"Patched function result: {test_result}")
        except ImportError:
            print("⚠️ Phase1 modules not available (expected in this context)")
        
        # Unpatch
        if unpatch_phase1_winner_notifications():
            print("✅ Unpatching successful - Phase1 restored to original")
    else:
        print("❌ Patching failed")
    
    print("\n✅ Adapter example completed!")

