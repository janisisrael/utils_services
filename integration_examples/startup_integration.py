"""
Startup Integration Script for Phase1
Shows how to initialize Utils_services notification system during Phase1 startup
"""

import logging
import os
import sys
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Phase1StartupIntegration:
    """
    Handles initialization of Utils_services during Phase1 startup
    """
    
    def __init__(self):
        self.integration_enabled = False
        self.initialization_error = None
        
    def initialize_utils_services(self) -> bool:
        """
        Initialize Utils_services during Phase1 startup
        This should be called early in Phase1's initialization process
        """
        try:
            logger.info("🚀 Initializing Utils_services integration...")
            
            # Check if integration should be enabled
            if not self._should_enable_integration():
                logger.info("📝 Utils_services integration disabled by configuration")
                return False
            
            # Verify Utils_services availability
            if not self._verify_utils_services_available():
                logger.warning("⚠️ Utils_services not available, continuing with Phase1 original system")
                return False
            
            # Apply integration based on configuration
            integration_method = self._get_integration_method()
            
            if integration_method == "patch":
                return self._apply_monkey_patch()
            elif integration_method == "adapter":
                return self._initialize_adapter()
            elif integration_method == "hybrid":
                return self._initialize_hybrid_mode()
            else:
                logger.warning(f"Unknown integration method: {integration_method}")
                return False
                
        except Exception as e:
            self.initialization_error = str(e)
            logger.error(f"❌ Failed to initialize Utils_services integration: {e}")
            return False
    
    def _should_enable_integration(self) -> bool:
        """Check if Utils_services integration should be enabled"""
        try:
            # Check environment variable
            env_enabled = os.getenv('ENABLE_UTILS_SERVICES', 'false').lower()
            if env_enabled in ['true', '1', 'yes', 'on']:
                return True
            
            # Check Phase1 configuration
            try:
                from config import app
                return app.config.get('ENABLE_UTILS_SERVICES', False)
            except:
                pass
            
            # Default: disabled for safety
            return False
            
        except Exception as e:
            logger.warning(f"Could not determine integration setting: {e}")
            return False
    
    def _verify_utils_services_available(self) -> bool:
        """Verify that Utils_services is available and functional"""
        try:
            # Add Utils_services to path
            utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
            if utils_path not in sys.path:
                sys.path.insert(0, utils_path)
            
            # Try to import core components
            from dispatcher.notification_dispatcher import NotificationDispatcher
            from email_service.email_service import EmailService
            from notification_service.notification_service import NotificationService
            
            logger.info("✅ Utils_services components successfully imported")
            return True
            
        except ImportError as e:
            logger.warning(f"Utils_services import failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Utils_services verification failed: {e}")
            return False
    
    def _get_integration_method(self) -> str:
        """Get the integration method from configuration"""
        try:
            # Check environment variable
            method = os.getenv('UTILS_SERVICES_INTEGRATION_METHOD', 'adapter').lower()
            
            # Check Phase1 configuration
            try:
                from config import app
                method = app.config.get('UTILS_SERVICES_INTEGRATION_METHOD', method)
            except:
                pass
            
            # Validate method
            valid_methods = ['patch', 'adapter', 'hybrid']
            if method not in valid_methods:
                logger.warning(f"Invalid integration method '{method}', using 'adapter'")
                return 'adapter'
            
            return method
            
        except Exception as e:
            logger.warning(f"Could not determine integration method: {e}")
            return 'adapter'
    
    def _apply_monkey_patch(self) -> bool:
        """Apply monkey patch integration"""
        try:
            from .winner_to_user_adapter import patch_phase1_winner_notifications
            
            if patch_phase1_winner_notifications():
                self.integration_enabled = True
                logger.info("✅ Monkey patch integration applied successfully")
                return True
            else:
                logger.error("❌ Monkey patch integration failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Monkey patch integration error: {e}")
            return False
    
    def _initialize_adapter(self) -> bool:
        """Initialize adapter-based integration"""
        try:
            from .winner_to_user_adapter import _winner_adapter
            
            # Pre-initialize the adapter
            if _winner_adapter._lazy_init_utils_services():
                self.integration_enabled = True
                logger.info("✅ Adapter integration initialized successfully")
                return True
            else:
                logger.warning("⚠️ Adapter initialization failed, will use fallback")
                return False
                
        except Exception as e:
            logger.error(f"❌ Adapter integration error: {e}")
            return False
    
    def _initialize_hybrid_mode(self) -> bool:
        """Initialize hybrid mode (both patch and adapter)"""
        try:
            # Initialize adapter first
            adapter_success = self._initialize_adapter()
            
            # Apply patch if adapter successful
            patch_success = False
            if adapter_success:
                patch_success = self._apply_monkey_patch()
            
            if adapter_success or patch_success:
                self.integration_enabled = True
                logger.info(f"✅ Hybrid integration - Adapter: {adapter_success}, Patch: {patch_success}")
                return True
            else:
                logger.error("❌ Both adapter and patch initialization failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Hybrid integration error: {e}")
            return False
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get the current integration status"""
        status = {
            'enabled': self.integration_enabled,
            'initialization_error': self.initialization_error,
            'utils_services_available': self._verify_utils_services_available(),
            'integration_method': self._get_integration_method(),
            'should_enable': self._should_enable_integration()
        }
        
        # Get adapter stats if available
        try:
            from .winner_to_user_adapter import get_adapter_stats
            status['adapter_stats'] = get_adapter_stats()
        except:
            status['adapter_stats'] = None
        
        return status
    
    def cleanup_integration(self):
        """Clean up integration during shutdown"""
        try:
            if self.integration_enabled:
                logger.info("🧹 Cleaning up Utils_services integration...")
                
                # Unpatch if patch was applied
                try:
                    from .winner_to_user_adapter import unpatch_phase1_winner_notifications
                    unpatch_phase1_winner_notifications()
                except:
                    pass
                
                self.integration_enabled = False
                logger.info("✅ Utils_services integration cleanup completed")
                
        except Exception as e:
            logger.error(f"❌ Error during integration cleanup: {e}")

# Global integration manager
_startup_integration = Phase1StartupIntegration()

def initialize_utils_services_integration() -> bool:
    """
    Initialize Utils_services integration
    Call this function during Phase1 startup
    """
    return _startup_integration.initialize_utils_services()

def get_integration_status() -> Dict[str, Any]:
    """Get current integration status"""
    return _startup_integration.get_integration_status()

def cleanup_utils_services_integration():
    """
    Clean up Utils_services integration
    Call this function during Phase1 shutdown
    """
    _startup_integration.cleanup_integration()

def phase1_main_integration_example():
    """
    Example of how to integrate Utils_services into Phase1's main.py
    """
    print("\n📋 Phase1 main.py Integration Example")
    print("-" * 50)
    
    # This is how you would modify Phase1's main.py
    example_main_code = '''
# Add this to Phase1/src/main.py

# At the top of the file, add:
import sys
import os

# Add Utils_services to path
utils_services_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Utils_services')
if utils_services_path not in sys.path:
    sys.path.insert(0, utils_services_path)

# Import integration functions
try:
    from integration_examples.startup_integration import (
        initialize_utils_services_integration,
        cleanup_utils_services_integration,
        get_integration_status
    )
    UTILS_SERVICES_AVAILABLE = True
except ImportError:
    UTILS_SERVICES_AVAILABLE = False
    logger.warning("Utils_services integration not available")

# In your main application initialization (after Flask app is created):
def initialize_application():
    # ... existing Phase1 initialization code ...
    
    # Initialize Utils_services integration
    if UTILS_SERVICES_AVAILABLE:
        try:
            if initialize_utils_services_integration():
                logger.info("✅ Utils_services integration enabled")
                
                # Log integration status
                status = get_integration_status()
                logger.info(f"Integration status: {status}")
            else:
                logger.warning("⚠️ Utils_services integration failed, using Phase1 original system")
        except Exception as e:
            logger.error(f"❌ Utils_services integration error: {e}")
    
    # ... rest of initialization ...

# In your shutdown/cleanup code:
def cleanup_application():
    # ... existing Phase1 cleanup code ...
    
    # Cleanup Utils_services integration
    if UTILS_SERVICES_AVAILABLE:
        try:
            cleanup_utils_services_integration()
        except Exception as e:
            logger.error(f"Error during Utils_services cleanup: {e}")
    
    # ... rest of cleanup ...

# Optional: Add a health check endpoint
@app.route('/health/utils-services')
def utils_services_health():
    if UTILS_SERVICES_AVAILABLE:
        status = get_integration_status()
        return jsonify(status)
    else:
        return jsonify({'available': False})
'''
    
    print("Code to add to Phase1/src/main.py:")
    print(example_main_code)

def configuration_examples():
    """Show configuration examples"""
    print("\n⚙️ Configuration Examples")
    print("-" * 30)
    
    print("Environment Variables:")
    print("export ENABLE_UTILS_SERVICES=true")
    print("export UTILS_SERVICES_INTEGRATION_METHOD=adapter  # or 'patch' or 'hybrid'")
    
    print("\nPhase1 Config (config.py):")
    config_example = '''
# Add to Phase1 configuration
ENABLE_UTILS_SERVICES = True
UTILS_SERVICES_INTEGRATION_METHOD = 'adapter'  # 'patch', 'adapter', or 'hybrid'

# Optional: Utils_services specific settings
UTILS_SERVICES_EMAIL_MAX_PER_MINUTE = 60
UTILS_SERVICES_NOTIFICATION_MAX_PER_HOUR = 100
UTILS_SERVICES_FALLBACK_ENABLED = True
'''
    print(config_example)

if __name__ == "__main__":
    print("🚀 Phase1 Startup Integration Examples")
    print("=" * 50)
    
    # Example 1: Test initialization
    print("\n1. Testing Integration Initialization:")
    success = initialize_utils_services_integration()
    print(f"Integration successful: {success}")
    
    # Example 2: Show status
    print("\n2. Integration Status:")
    status = get_integration_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Example 3: Show main.py integration example
    phase1_main_integration_example()
    
    # Example 4: Show configuration examples
    configuration_examples()
    
    # Example 5: Cleanup
    print("\n5. Cleaning up:")
    cleanup_utils_services_integration()
    
    print("\n✅ Startup integration examples completed!")

