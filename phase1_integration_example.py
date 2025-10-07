"""
Phase 1 Integration Example for Utils_services Email Service
This file demonstrates how to integrate the Utils_services email service with Phase 1
without modifying any existing Phase 1 code.
"""

import sys
import os
import logging
from typing import Dict, Any

# Add Utils_services to Python path
utils_services_path = os.path.join(os.path.dirname(__file__), '..', 'Utils_services')
sys.path.insert(0, utils_services_path)

# Import the integration layer
from phase1_integration import (
    send_email,
    send_email_async,
    send_winner_notification,
    send_winner_notification_async,
    send_new_draw_notification,
    get_email_status,
    health_check
)

logger = logging.getLogger(__name__)

def example_winner_notification():
    """Example of sending a winner notification"""
    
    # Sample winner data (same format as Phase 1)
    winner_data = {
        "user_email": "winner@example.com",
        "user_name": "John Doe",
        "game": "Lotto 6/49",
        "draw_date": "2025-10-06",
        "ticket_number": "123456789",
        "ticket_id": "12345",
        "winners": {
            "Lotto 6/49": [
                {
                    "matched_numbers": [1, 2, 3, 4, 5, 6],
                    "prize_amount": "$5,000",
                    "prize_category": "3 of 6"
                }
            ]
        }
    }
    
    print("=== Winner Notification Example ===")
    
    # Method 1: Synchronous email sending
    print("1. Sending synchronous winner notification...")
    success = send_email(winner_data)
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Method 2: Asynchronous email sending with tracking
    print("2. Sending asynchronous winner notification...")
    tracking_id = send_email_async(winner_data)
    print(f"   Tracking ID: {tracking_id}")
    
    # Method 3: Using convenience functions
    print("3. Using convenience functions...")
    success = send_winner_notification(winner_data)
    print(f"   Winner notification: {'✅ Success' if success else '❌ Failed'}")
    
    tracking_id = send_winner_notification_async(winner_data)
    print(f"   Async winner notification tracking ID: {tracking_id}")

def example_new_draw_notification():
    """Example of sending new draw results notification"""
    
    print("\n=== New Draw Results Notification Example ===")
    
    success = send_new_draw_notification(
        user_email="player@example.com",
        game="Lotto Max",
        draw_date="2025-10-06",
        winning_numbers="01, 15, 23, 31, 42, 47, 49",
        jackpot_amount="$50,000,000"
    )
    
    print(f"New draw notification: {'✅ Success' if success else '❌ Failed'}")

def example_email_status_check():
    """Example of checking email status"""
    
    print("\n=== Email Status Check Example ===")
    
    # Check health of the email service
    health = health_check()
    print(f"Email service health: {health}")
    
    # Check status of a specific email (if you have a tracking ID)
    # tracking_id = "utils_email_20251006123456_123456789"
    # status = get_email_status(tracking_id)
    # print(f"Email status: {status}")

def example_phase1_integration():
    """
    Example of how to integrate this with Phase 1 without changing Phase 1 code
    """
    
    print("\n=== Phase 1 Integration Example ===")
    print("To integrate with Phase 1, you can:")
    print("1. Replace Phase 1's send_email calls with Utils_services calls")
    print("2. Use the same data format - no changes needed to Phase 1 data structures")
    print("3. Automatic fallback to Phase 1 email system if Utils_services fails")
    print("4. Enhanced features: tracking, retry logic, rate limiting, better templates")
    
    # Example of replacing Phase 1's send_email function
    print("\nExample replacement in Phase 1:")
    print("""
    # In Phase 1's services/notification/email.py
    # Replace the existing send_email function with:
    
    def send_email(result):
        try:
            # Try Utils_services first
            from utils_services.phase1_integration import send_email as utils_send_email
            return utils_send_email(result)
        except ImportError:
            # Fallback to original Phase 1 implementation
            from services.notification.email_original import send_email as original_send_email
            return original_send_email(result)
    """)

def example_environment_setup():
    """Example of environment setup"""
    
    print("\n=== Environment Setup Example ===")
    print("Required environment variables:")
    print("""
    # SMTP Configuration
    export SMTP_SERVER=smtp.gmail.com
    export SMTP_PORT=587
    export SMTP_USERNAME=your-email@gmail.com
    export SMTP_PASSWORD=your-app-password
    export SENDER_EMAIL=noreply@thesantris.com
    export SENDER_NAME=Lotto Command Center
    
    # Optional Configuration
    export MAX_EMAILS_PER_MINUTE=100
    export EMAIL_ENABLE_TRACKING=true
    export EMAIL_FALLBACK_TO_PHASE1=true
    """)

def main():
    """Run all examples"""
    
    print("🚀 Utils_services Email Integration Examples")
    print("=" * 50)
    
    try:
        # Run examples
        example_winner_notification()
        example_new_draw_notification()
        example_email_status_check()
        example_phase1_integration()
        example_environment_setup()
        
        print("\n✅ All examples completed successfully!")
        print("\n📧 The Utils_services email integration is ready to use!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        logger.error(f"Example execution failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()


