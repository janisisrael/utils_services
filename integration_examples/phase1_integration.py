"""
Phase1 Integration Examples for Utils_services
Shows how to integrate the new notification system with existing Phase1 code
WITHOUT breaking existing functionality
"""

import logging
import sys
import os
from typing import Dict, Any, Optional

# Add Phase1 to path for imports
phase1_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Phase1', 'src')
if phase1_path not in sys.path:
    sys.path.insert(0, phase1_path)

logger = logging.getLogger(__name__)

class Phase1NotificationAdapter:
    """
    Adapter class that provides seamless integration between 
    Phase1 existing notification system and new Utils_services
    """
    
    def __init__(self):
        self.new_system_available = False
        self.dispatcher = None
        self.fallback_count = 0
        self.success_count = 0
        
        # Try to initialize new system
        self._initialize_new_system()
    
    def _initialize_new_system(self):
        """Initialize the new notification system"""
        try:
            # Import new system
            from ..dispatcher.notification_dispatcher import NotificationDispatcher
            
            # Get Phase1 configurations
            email_config = self._get_phase1_email_config()
            notification_config = self._get_phase1_notification_config()
            
            # Initialize dispatcher
            self.dispatcher = NotificationDispatcher()
            
            if self.dispatcher.initialize(email_config, notification_config):
                self.new_system_available = True
                logger.info("✅ New Utils_services notification system initialized successfully")
            else:
                logger.warning("❌ Failed to initialize new notification system")
                
        except Exception as e:
            logger.warning(f"⚠️ New notification system not available: {e}")
            self.new_system_available = False
    
    def _get_phase1_email_config(self) -> Dict[str, Any]:
        """Extract email configuration from Phase1"""
        try:
            # Try to import Phase1 config
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
        except Exception as e:
            logger.warning(f"Could not get Phase1 email config: {e}")
            # Return default config
            return {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True,
                'max_emails_per_minute': 60
            }
    
    def _get_phase1_notification_config(self) -> Dict[str, Any]:
        """Extract notification configuration from Phase1"""
        try:
            # Try to import Phase1 database config
            from config import get_connection
            
            return {
                'database': {
                    'connection_factory': get_connection  # Use Phase1's connection
                },
                'store_in_database': True,
                'send_via_websocket': True,
                'max_notifications_per_user_per_hour': 100
            }
        except Exception as e:
            logger.warning(f"Could not get Phase1 notification config: {e}")
            return {
                'store_in_database': True,
                'send_via_websocket': True,
                'max_notifications_per_user_per_hour': 100
            }
    
    def send_winner_notification(self, winner_data: Dict[str, Any]) -> bool:
        """
        Send winner notification using new system with fallback to old system
        This is a drop-in replacement for existing Phase1 notification functions
        """
        try:
            if self.new_system_available and self.dispatcher:
                # Use new separated notification system
                dispatch_id = self.dispatcher.dispatch_winner_notification(winner_data)
                
                if dispatch_id:
                    self.success_count += 1
                    logger.info(f"✅ Winner notification sent via new system: {dispatch_id}")
                    return True
                else:
                    raise Exception("Dispatcher returned no dispatch_id")
                    
            else:
                raise Exception("New system not available")
                
        except Exception as e:
            logger.warning(f"⚠️ New notification system failed: {e}")
            return self._fallback_to_old_system(winner_data)
    
    def _fallback_to_old_system(self, winner_data: Dict[str, Any]) -> bool:
        """Fallback to existing Phase1 notification system"""
        try:
            self.fallback_count += 1
            logger.info("🔄 Using fallback to existing Phase1 notification system")
            
            # Import existing Phase1 functions
            from services.process_winner.winner_to_user import get_winner_details
            
            # Convert winner_data to Phase1 format
            phase1_data = self._convert_to_phase1_format(winner_data)
            
            # Call existing Phase1 function
            result = get_winner_details(phase1_data)
            
            logger.info("✅ Winner notification sent via Phase1 fallback system")
            return True
            
        except Exception as e:
            logger.error(f"❌ Both new and fallback notification systems failed: {e}")
            return False
    
    def _convert_to_phase1_format(self, winner_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert winner_data to Phase1 expected format"""
        # Ensure the data is in the format that Phase1's get_winner_details expects
        return {
            "winners": {
                winner_data.get('game', 'lottery'): [winner_data]
            },
            "number_of_winners": 1
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics"""
        total = self.success_count + self.fallback_count
        return {
            'new_system_available': self.new_system_available,
            'total_notifications': total,
            'new_system_success': self.success_count,
            'fallback_used': self.fallback_count,
            'new_system_success_rate': (self.success_count / total * 100) if total > 0 else 0
        }

# Global adapter instance (singleton pattern)
_notification_adapter = None

def get_notification_adapter() -> Phase1NotificationAdapter:
    """Get singleton notification adapter"""
    global _notification_adapter
    if _notification_adapter is None:
        _notification_adapter = Phase1NotificationAdapter()
    return _notification_adapter

def enhanced_winner_notification(winner_data: Dict[str, Any]) -> bool:
    """
    Enhanced winner notification function that can be used as drop-in replacement
    for existing Phase1 notification calls
    """
    adapter = get_notification_adapter()
    return adapter.send_winner_notification(winner_data)

def monkey_patch_phase1_notifications():
    """
    Monkey patch existing Phase1 notification functions to use new system
    This allows gradual migration without changing existing code
    """
    try:
        # Import Phase1 modules
        from services.process_winner import winner_to_user
        
        # Store original function
        original_get_winner_details = winner_to_user.get_winner_details
        
        def enhanced_get_winner_details(json_data):
            """Enhanced version that tries new system first"""
            try:
                # Extract winner data for new system
                winners = json_data.get("winners", {})
                
                for game, game_winners in winners.items():
                    for winner in game_winners:
                        # Try new notification system
                        adapter = get_notification_adapter()
                        if adapter.send_winner_notification(winner):
                            continue  # Success with new system
                
                # If we get here, use original function as fallback
                return original_get_winner_details(json_data)
                
            except Exception as e:
                logger.warning(f"Enhanced notification failed, using original: {e}")
                return original_get_winner_details(json_data)
        
        # Replace the function
        winner_to_user.get_winner_details = enhanced_get_winner_details
        
        logger.info("✅ Successfully monkey-patched Phase1 notification functions")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to monkey-patch Phase1 functions: {e}")
        return False

# Integration Examples

def example_1_drop_in_replacement():
    """Example 1: Drop-in replacement for existing notification calls"""
    print("\n📧 Example 1: Drop-in Replacement")
    print("-" * 40)
    
    # Sample winner data (same as Phase1 uses)
    winner_data = {
        'id': 25,
        'user_id': 1,
        'user_email': 'winner@example.com',
        'name': 'John Doe',
        'game': '6-49',
        'ticket_number': 'INTEGRATION-TEST-001',
        'ticket_numbers': '03-17-22-30-41-48',
        'draw_date': '2025-09-17',
        'ticket_status': 'WON',
        'ticket_id': 25,
        'classic_draw': {
            'status': 'WON',
            'match': 6,
            'draw_date': '2025-09-17',
            'winning_number': '3,17,22,30,41,48',
            'your_winning_numbers': '03,17,22,30,41,48',
            'prize_category': 'Jackpot'
        }
    }
    
    # OLD WAY: Phase1 would call this
    # get_winner_details(winner_data)
    
    # NEW WAY: Drop-in replacement
    success = enhanced_winner_notification(winner_data)
    
    print(f"Notification sent: {success}")
    
    # Show stats
    adapter = get_notification_adapter()
    stats = adapter.get_stats()
    print(f"Adapter stats: {stats}")

def example_2_gradual_migration():
    """Example 2: Gradual migration approach"""
    print("\n🔄 Example 2: Gradual Migration")
    print("-" * 40)
    
    # This shows how existing Phase1 functions can be gradually updated
    
    def existing_phase1_function(winner_data):
        """Simulates existing Phase1 function"""
        print("📍 In existing Phase1 function")
        
        # Add new notification system as optional enhancement
        try:
            # Try new system first
            if enhanced_winner_notification(winner_data):
                print("✅ Used new notification system")
                return True
        except Exception as e:
            print(f"⚠️ New system failed: {e}")
        
        # Fallback to old system
        print("🔄 Using old notification system")
        # Here would be existing Phase1 notification code
        return True
    
    # Test it
    sample_data = {
        'user_id': 1,
        'user_email': 'test@example.com',
        'game': '6-49',
        'ticket_number': 'MIGRATION-TEST'
    }
    
    result = existing_phase1_function(sample_data)
    print(f"Function result: {result}")

def example_3_monkey_patching():
    """Example 3: Monkey patching for zero-code-change migration"""
    print("\n🐵 Example 3: Monkey Patching")
    print("-" * 40)
    
    # Apply monkey patch
    if monkey_patch_phase1_notifications():
        print("✅ Monkey patching applied successfully")
        
        # Now existing Phase1 code automatically uses new system
        print("🔄 Existing Phase1 functions now use new notification system")
        
        # Test by calling original function name (but it's now enhanced)
        try:
            from services.process_winner.winner_to_user import get_winner_details
            
            test_data = {
                "winners": {
                    "6-49": [{
                        'user_id': 1,
                        'user_email': 'patch-test@example.com',
                        'game': '6-49',
                        'ticket_number': 'MONKEY-PATCH-TEST'
                    }]
                },
                "number_of_winners": 1
            }
            
            # This looks like old Phase1 call but uses new system
            result = get_winner_details(test_data)
            print(f"Monkey-patched function result: {result}")
            
        except Exception as e:
            print(f"Monkey patch test failed: {e}")
    else:
        print("❌ Monkey patching failed")

def example_4_configuration_bridge():
    """Example 4: Configuration bridge between Phase1 and Utils_services"""
    print("\n⚙️ Example 4: Configuration Bridge")
    print("-" * 40)
    
    adapter = get_notification_adapter()
    
    # Show how configurations are bridged
    try:
        email_config = adapter._get_phase1_email_config()
        notification_config = adapter._get_phase1_notification_config()
        
        print("📧 Email config bridged from Phase1:")
        for key, value in email_config.items():
            if 'password' in key.lower():
                value = "***" if value else None
            print(f"  {key}: {value}")
        
        print("\n🔔 Notification config bridged from Phase1:")
        for key, value in notification_config.items():
            if key != 'database':  # Skip complex objects
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Configuration bridge error: {e}")

def example_5_health_monitoring():
    """Example 5: Health monitoring and service status"""
    print("\n🏥 Example 5: Health Monitoring")
    print("-" * 40)
    
    adapter = get_notification_adapter()
    
    if adapter.new_system_available and adapter.dispatcher:
        # Get service health
        health = adapter.dispatcher.get_service_health()
        print("🔍 Service Health Status:")
        for service_name, health_data in health.items():
            status = health_data.get('status', 'unknown')
            print(f"  {service_name}: {status}")
        
        # Get dispatcher stats
        stats = adapter.dispatcher.get_dispatcher_stats()
        print(f"\n📊 Dispatcher Stats:")
        print(f"  Active Services: {stats.get('active_services', 0)}")
        print(f"  Total Services: {stats.get('total_services', 0)}")
        
        # Get adapter stats
        adapter_stats = adapter.get_stats()
        print(f"\n🔧 Adapter Stats:")
        for key, value in adapter_stats.items():
            print(f"  {key}: {value}")
    else:
        print("❌ New notification system not available")

if __name__ == "__main__":
    print("🔗 Phase1 Integration Examples for Utils_services")
    print("=" * 60)
    
    # Run all examples
    example_1_drop_in_replacement()
    example_2_gradual_migration()
    example_3_monkey_patching()
    example_4_configuration_bridge()
    example_5_health_monitoring()
    
    print("\n✅ All integration examples completed!")
    print("\n💡 Next Steps:")
    print("1. Choose an integration approach that fits your needs")
    print("2. Test with a small subset of notifications first") 
    print("3. Monitor both old and new systems during transition")
    print("4. Gradually increase usage of new system")
    print("5. Eventually deprecate old notification code")
