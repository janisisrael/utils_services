"""
Example Usage of Utils_services Notification System
Demonstrates how to use the separated notification architecture
"""

import logging
from dispatcher.notification_dispatcher import NotificationDispatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_configurations():
    """Create sample configurations for services"""
    
    # Email service configuration
    email_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_username': 'your-email@gmail.com',
        'smtp_password': 'your-app-password',
        'use_tls': True,
        'sender_email': 'your-email@gmail.com',
        'sender_name': 'Lotto Command Center',
        'max_emails_per_minute': 60
    }
    
    # Notification service configuration
    notification_config = {
        'database': {
            'host': 'localhost',
            'port': 3306,
            'username': 'your-db-user',
            'password': 'your-db-password',
            'database': 'lotto_cc'
        },
        'store_in_database': True,
        'send_via_websocket': True,
        'max_notifications_per_user_per_hour': 100
    }
    
    return email_config, notification_config

def example_winner_notification():
    """Example of sending a winner notification"""
    
    # Create configurations
    email_config, notification_config = create_sample_configurations()
    
    # Initialize dispatcher
    dispatcher = NotificationDispatcher()
    
    try:
        # Initialize services
        if not dispatcher.initialize(email_config, notification_config):
            logger.error("Failed to initialize dispatcher")
            return
        
        # Sample winner data (same format as Phase1)
        winner_data = {
            'user_id': 1,
            'user_email': 'winner@example.com',
            'name': 'John Doe',
            'game': '6-49',
            'ticket_number': 'TEST-WINNER-001',
            'ticket_numbers': '03-17-22-30-41-48',
            'draw_date': '2025-09-17',
            'ticket_id': 24,
            'classic_draw': {
                'status': 'WON',
                'match': 6,
                'draw_date': '2025-09-17',
                'winning_number': '3,17,22,30,41,48',
                'your_winning_numbers': '03,17,22,30,41,48',
                'ticket_control_number': 'TEST-WINNER-001',
                'bonus': None,
                'prize_category': 'Jackpot'
            },
            'gold_ball_draw': None,
            'extra_match': None,
            'max_million': None,
            'frontend_url': 'https://www.thesantris.com'
        }
        
        # Dispatch winner notification
        dispatch_id = dispatcher.dispatch_winner_notification(winner_data)
        logger.info(f"Winner notification dispatched with ID: {dispatch_id}")
        
        # Check dispatch status
        import time
        time.sleep(2)  # Wait for processing
        
        status = dispatcher.get_dispatch_status(dispatch_id)
        logger.info(f"Dispatch status: {status}")
        
        # Get service health
        health = dispatcher.get_service_health()
        logger.info(f"Service health: {health}")
        
        # Get dispatcher stats
        stats = dispatcher.get_dispatcher_stats()
        logger.info(f"Dispatcher stats: {stats}")
        
    except Exception as e:
        logger.error(f"Error in example: {e}")
    
    finally:
        # Shutdown
        dispatcher.shutdown()

def example_custom_notification():
    """Example of sending a custom notification"""
    
    # Create configurations
    email_config, notification_config = create_sample_configurations()
    
    # Initialize dispatcher
    dispatcher = NotificationDispatcher()
    
    try:
        # Initialize services
        if not dispatcher.initialize(email_config, notification_config):
            logger.error("Failed to initialize dispatcher")
            return
        
        # Send custom notification
        dispatch_id = dispatcher.dispatch_custom_notification(
            user_id=1,
            title="Welcome to Lotto Command Center!",
            body="Thank you for joining our platform. Good luck with your tickets!",
            channels=['notification'],  # Only push notification, no email
            priority='normal',
            type='info',
            action_url='/dashboard',
            action_text='Go to Dashboard'
        )
        
        logger.info(f"Custom notification dispatched with ID: {dispatch_id}")
        
    except Exception as e:
        logger.error(f"Error in custom notification example: {e}")
    
    finally:
        # Shutdown
        dispatcher.shutdown()

def example_integration_with_phase1():
    """Example of how Phase1 would integrate with Utils_services"""
    
    logger.info("=== Phase1 Integration Example ===")
    
    # This is how Phase1 would use the new notification system
    # WITHOUT modifying existing code
    
    def old_winner_notification_function(winner_data):
        """This simulates the existing Phase1 function"""
        # Old code would call email and notification directly
        # Now it can optionally use the new dispatcher
        
        try:
            # Try to use new notification system
            from Utils_services.dispatcher.notification_dispatcher import NotificationDispatcher
            
            # Create dispatcher (in real implementation, this would be a singleton)
            email_config, notification_config = create_sample_configurations()
            dispatcher = NotificationDispatcher()
            
            if dispatcher.initialize(email_config, notification_config):
                # Use new separated system
                dispatch_id = dispatcher.dispatch_winner_notification(winner_data)
                logger.info(f"Used new notification system: {dispatch_id}")
                
                # Clean shutdown
                dispatcher.shutdown()
                return True
            else:
                raise Exception("Failed to initialize new notification system")
                
        except Exception as e:
            logger.warning(f"New notification system failed, falling back to old system: {e}")
            
            # Fallback to old system (existing Phase1 code)
            # This ensures no breaking changes
            return old_notification_fallback(winner_data)
    
    def old_notification_fallback(winner_data):
        """Fallback to old notification system"""
        logger.info("Using fallback notification system (existing Phase1)")
        # Here would be the existing Phase1 notification code
        return True
    
    # Test the integration
    sample_winner = {
        'user_id': 1,
        'user_email': 'test@example.com',
        'game': '6-49',
        'ticket_number': 'INTEGRATION-TEST',
    }
    
    result = old_winner_notification_function(sample_winner)
    logger.info(f"Integration test result: {result}")

if __name__ == "__main__":
    print("🚀 Utils_services Notification System Examples")
    print("=" * 50)
    
    print("\n1. Winner Notification Example:")
    example_winner_notification()
    
    print("\n2. Custom Notification Example:")
    example_custom_notification()
    
    print("\n3. Phase1 Integration Example:")
    example_integration_with_phase1()
    
    print("\n✅ All examples completed!")

