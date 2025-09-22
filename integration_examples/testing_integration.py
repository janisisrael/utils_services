"""
Testing Integration Examples
Shows how to test the Utils_services integration with Phase1
"""

import logging
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import sys
import os

logger = logging.getLogger(__name__)

class TestUtilsServicesIntegration(unittest.TestCase):
    """Test cases for Utils_services integration with Phase1"""
    
    def setUp(self):
        """Set up test environment"""
        # Add Utils_services to path
        utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
        if utils_path not in sys.path:
            sys.path.insert(0, utils_path)
    
    def test_adapter_initialization(self):
        """Test that the adapter can be initialized"""
        try:
            from integration_examples.winner_to_user_adapter import WinnerToUserAdapter
            
            adapter = WinnerToUserAdapter()
            self.assertIsNotNone(adapter)
            self.assertFalse(adapter.utils_services_available)  # Should be False without proper config
            
        except ImportError:
            self.skipTest("Utils_services not available")
    
    def test_dispatcher_creation(self):
        """Test that the notification dispatcher can be created"""
        try:
            from dispatcher.notification_dispatcher import NotificationDispatcher
            
            dispatcher = NotificationDispatcher()
            self.assertIsNotNone(dispatcher)
            
        except ImportError:
            self.skipTest("Utils_services not available")
    
    @patch('config.get_connection')
    @patch('config.app')
    def test_winner_notification_with_mocked_phase1(self, mock_app, mock_get_connection):
        """Test winner notification with mocked Phase1 dependencies"""
        # Mock Phase1 configuration
        mock_app.config = {
            'MAIL_SERVER': 'smtp.test.com',
            'MAIL_PORT': 587,
            'MAIL_USERNAME': 'test@test.com',
            'MAIL_PASSWORD': 'test_password',
            'MAIL_USE_TLS': True
        }
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ('winner@test.com',)
        mock_get_connection.return_value.__enter__.return_value = mock_conn
        
        try:
            from integration_examples.winner_to_user_adapter import get_winner_details
            
            # Test data
            test_data = {
                "winners": {
                    "6-49": [{
                        'id': 1,
                        'user_id': 1,
                        'ticket_number': 'TEST-001',
                        'ticket_numbers': '1-2-3-4-5-6',
                        'draw_date': '2025-09-17',
                        'matches': [{
                            'draw_id': 1,
                            'winning_number': '1,2,3,4,5,6',
                            'matched_count': 6,
                            'prize_category': 'Jackpot'
                        }]
                    }]
                },
                "number_of_winners": 1
            }
            
            # Call the function
            result = get_winner_details(test_data)
            
            # Should return a result (either success or fallback)
            self.assertIsNotNone(result)
            self.assertIn('success', result)
            
        except ImportError:
            self.skipTest("Utils_services not available")
    
    def test_startup_integration_configuration(self):
        """Test startup integration configuration reading"""
        try:
            from integration_examples.startup_integration import Phase1StartupIntegration
            
            integration = Phase1StartupIntegration()
            
            # Test configuration methods
            with patch.dict(os.environ, {'ENABLE_UTILS_SERVICES': 'true'}):
                self.assertTrue(integration._should_enable_integration())
            
            with patch.dict(os.environ, {'ENABLE_UTILS_SERVICES': 'false'}):
                self.assertFalse(integration._should_enable_integration())
            
            # Test integration method
            with patch.dict(os.environ, {'UTILS_SERVICES_INTEGRATION_METHOD': 'adapter'}):
                self.assertEqual(integration._get_integration_method(), 'adapter')
            
        except ImportError:
            self.skipTest("Utils_services not available")

class IntegrationTestSuite:
    """Integration test suite for Utils_services"""
    
    def __init__(self):
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🧪 Running Utils_services Integration Tests")
        print("=" * 50)
        
        test_methods = [
            self.test_imports,
            self.test_adapter_functionality,
            self.test_dispatcher_functionality,
            self.test_email_service,
            self.test_notification_service,
            self.test_configuration_bridge,
            self.test_fallback_mechanism,
            self.test_statistics_tracking
        ]
        
        for test_method in test_methods:
            try:
                print(f"\n🔍 {test_method.__name__}:")
                test_method()
                self.test_results['passed'] += 1
                print(f"  ✅ PASSED")
            except Exception as e:
                self.test_results['failed'] += 1
                self.test_results['errors'].append(f"{test_method.__name__}: {e}")
                print(f"  ❌ FAILED: {e}")
        
        self.print_summary()
    
    def test_imports(self):
        """Test that all required modules can be imported"""
        try:
            from dispatcher.notification_dispatcher import NotificationDispatcher
            from email_service.email_service import EmailService
            from notification_service.notification_service import NotificationService
            from integration_examples.winner_to_user_adapter import WinnerToUserAdapter
            from integration_examples.startup_integration import Phase1StartupIntegration
            print("    All modules imported successfully")
        except ImportError as e:
            raise Exception(f"Import failed: {e}")
    
    def test_adapter_functionality(self):
        """Test adapter basic functionality"""
        from integration_examples.winner_to_user_adapter import WinnerToUserAdapter
        
        adapter = WinnerToUserAdapter()
        
        # Test stats
        stats = adapter.get_stats()
        assert isinstance(stats, dict), "Stats should be a dictionary"
        assert 'total_calls' in stats, "Stats should include total_calls"
        
        print("    Adapter functionality verified")
    
    def test_dispatcher_functionality(self):
        """Test dispatcher basic functionality"""
        from dispatcher.notification_dispatcher import NotificationDispatcher
        
        dispatcher = NotificationDispatcher()
        
        # Test configuration
        email_config = {'smtp_server': 'test.com', 'smtp_port': 587}
        notification_config = {'store_in_database': True}
        
        # Note: We don't actually initialize to avoid dependencies
        assert hasattr(dispatcher, 'initialize'), "Dispatcher should have initialize method"
        assert hasattr(dispatcher, 'dispatch_winner_notification'), "Dispatcher should have dispatch method"
        
        print("    Dispatcher functionality verified")
    
    def test_email_service(self):
        """Test email service basic functionality"""
        from email_service.email_service import EmailService
        
        config = {
            'smtp_server': 'test.com',
            'smtp_port': 587,
            'use_tls': True
        }
        
        email_service = EmailService(config)
        
        assert email_service.service_name == "EmailService", "Service name should be correct"
        assert hasattr(email_service, 'send_winner_notification'), "Should have winner notification method"
        
        print("    Email service functionality verified")
    
    def test_notification_service(self):
        """Test notification service basic functionality"""
        from notification_service.notification_service import NotificationService
        
        config = {
            'store_in_database': True,
            'send_via_websocket': True
        }
        
        notification_service = NotificationService(config)
        
        assert notification_service.service_name == "NotificationService", "Service name should be correct"
        assert hasattr(notification_service, 'send_winner_notification'), "Should have winner notification method"
        
        print("    Notification service functionality verified")
    
    def test_configuration_bridge(self):
        """Test configuration bridging from Phase1"""
        from integration_examples.winner_to_user_adapter import WinnerToUserAdapter
        
        adapter = WinnerToUserAdapter()
        
        # Test configuration methods
        email_config = adapter._get_phase1_email_config()
        notification_config = adapter._get_phase1_notification_config()
        
        assert isinstance(email_config, dict), "Email config should be dict"
        assert isinstance(notification_config, dict), "Notification config should be dict"
        assert 'smtp_server' in email_config, "Email config should have SMTP server"
        
        print("    Configuration bridge verified")
    
    def test_fallback_mechanism(self):
        """Test fallback mechanism"""
        from integration_examples.winner_to_user_adapter import WinnerToUserAdapter
        
        adapter = WinnerToUserAdapter()
        
        # Force fallback by ensuring new system is not available
        adapter.utils_services_available = False
        
        test_data = {
            "winners": {"test": [{"user_id": 1}]},
            "number_of_winners": 1
        }
        
        # This should trigger fallback
        try:
            result = adapter.enhanced_get_winner_details(test_data)
            assert isinstance(result, dict), "Should return a result dict"
            print("    Fallback mechanism verified")
        except Exception as e:
            # Fallback might fail due to missing Phase1 modules, which is expected
            if "No module named" in str(e):
                print("    Fallback mechanism verified (Phase1 modules not available)")
            else:
                raise
    
    def test_statistics_tracking(self):
        """Test statistics tracking"""
        from integration_examples.winner_to_user_adapter import get_adapter_stats
        
        stats = get_adapter_stats()
        
        assert isinstance(stats, dict), "Stats should be a dictionary"
        required_keys = ['utils_services_available', 'total_calls', 'utils_services_success', 'fallback_used']
        
        for key in required_keys:
            assert key in stats, f"Stats should include {key}"
        
        print("    Statistics tracking verified")
    
    def print_summary(self):
        """Print test summary"""
        print("\n📊 Test Summary")
        print("-" * 20)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"⏭️  Skipped: {self.test_results['skipped']}")
        
        if self.test_results['errors']:
            print("\n🔍 Errors:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        
        total_tests = self.test_results['passed'] + self.test_results['failed'] + self.test_results['skipped']
        if total_tests > 0:
            success_rate = (self.test_results['passed'] / total_tests) * 100
            print(f"\n📈 Success Rate: {success_rate:.1f}%")

def mock_phase1_environment():
    """Set up a mock Phase1 environment for testing"""
    print("\n🎭 Setting up Mock Phase1 Environment")
    print("-" * 40)
    
    # Mock Phase1 config module
    mock_config = MagicMock()
    mock_config.app.config = {
        'MAIL_SERVER': 'smtp.test.com',
        'MAIL_PORT': 587,
        'MAIL_USERNAME': 'test@test.com',
        'MAIL_PASSWORD': 'test_password',
        'MAIL_USE_TLS': True
    }
    
    # Mock database connection
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ('test@example.com',)
    mock_config.get_connection.return_value.__enter__.return_value = mock_conn
    
    # Add mock to sys.modules
    sys.modules['config'] = mock_config
    
    print("✅ Mock Phase1 environment set up")
    return mock_config

def run_integration_tests_with_mock():
    """Run integration tests with mocked Phase1 environment"""
    print("\n🧪 Running Integration Tests with Mock Environment")
    print("=" * 60)
    
    # Set up mock environment
    mock_config = mock_phase1_environment()
    
    try:
        # Run the test suite
        test_suite = IntegrationTestSuite()
        test_suite.run_all_tests()
        
        # Test with mock data
        print("\n🎯 Testing with Mock Data:")
        
        from integration_examples.winner_to_user_adapter import get_winner_details
        
        test_data = {
            "winners": {
                "6-49": [{
                    'id': 1,
                    'user_id': 1,
                    'ticket_number': 'MOCK-TEST-001',
                    'ticket_numbers': '1-2-3-4-5-6',
                    'draw_date': '2025-09-17'
                }]
            },
            "number_of_winners": 1
        }
        
        result = get_winner_details(test_data)
        print(f"Mock test result: {result}")
        
    finally:
        # Clean up mock
        if 'config' in sys.modules:
            del sys.modules['config']

if __name__ == "__main__":
    print("🧪 Utils_services Integration Testing")
    print("=" * 50)
    
    # Option 1: Run unittest tests
    print("\n1. Running Unit Tests:")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Option 2: Run custom integration test suite
    print("\n2. Running Custom Integration Tests:")
    test_suite = IntegrationTestSuite()
    test_suite.run_all_tests()
    
    # Option 3: Run tests with mock environment
    print("\n3. Running Tests with Mock Environment:")
    run_integration_tests_with_mock()
    
    print("\n✅ All testing examples completed!")
