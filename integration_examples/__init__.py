"""
Integration Examples for Utils_services with Phase1
Provides seamless integration without breaking existing functionality
"""

# Main integration functions
from .winner_to_user_adapter import (
    get_winner_details,
    get_adapter_stats,
    patch_phase1_winner_notifications,
    unpatch_phase1_winner_notifications
)

from .startup_integration import (
    initialize_utils_services_integration,
    get_integration_status,
    cleanup_utils_services_integration
)

# Quick integration functions
def quick_enable_utils_services():
    """
    Quick function to enable Utils_services integration
    Call this once during Phase1 startup
    """
    try:
        return initialize_utils_services_integration()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to enable Utils_services: {e}")
        return False

def quick_patch_notifications():
    """
    Quick function to patch all Phase1 notification calls
    Enables Utils_services for all existing notification code
    """
    try:
        return patch_phase1_winner_notifications()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to patch notifications: {e}")
        return False

# Convenience aliases
enable_utils_services = quick_enable_utils_services
patch_notifications = quick_patch_notifications
unpatch_notifications = unpatch_phase1_winner_notifications

__all__ = [
    # Main functions
    'get_winner_details',
    'get_adapter_stats', 
    'patch_phase1_winner_notifications',
    'unpatch_phase1_winner_notifications',
    'initialize_utils_services_integration',
    'get_integration_status',
    'cleanup_utils_services_integration',
    
    # Quick functions
    'quick_enable_utils_services',
    'quick_patch_notifications',
    
    # Aliases
    'enable_utils_services',
    'patch_notifications',
    'unpatch_notifications'
]

