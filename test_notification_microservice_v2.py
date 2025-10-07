#!/usr/bin/env python3
"""
Test script for Notification Microservice v2
Tests all endpoints and WebSocket functionality
"""

import requests
import json
import time
import socketio
import threading
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:7002"
SOCKET_URL = "http://localhost:7002"

class NotificationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.socket_url = SOCKET_URL
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, f"Service is healthy - Port: {data.get('port')}")
                return True
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_status_endpoint(self):
        """Test status endpoint"""
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Status Check", True, f"Active connections: {data.get('active_connections', 0)}")
                return True
            else:
                self.log_test("Status Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Status Check", False, f"Error: {str(e)}")
            return False
    
    def test_connections_endpoint(self):
        """Test connections endpoint"""
        try:
            response = requests.get(f"{self.base_url}/connections", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Connections Check", True, f"Active: {data.get('active_connections', 0)}")
                return True
            else:
                self.log_test("Connections Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Connections Check", False, f"Error: {str(e)}")
            return False
    
    def test_send_notification(self):
        """Test sending notification to user"""
        try:
            notification_data = {
                "user_id": 999,  # Test user ID
                "title": "Test Notification",
                "body": "This is a test notification from the microservice",
                "type": "info",
                "icon": "bell",
                "url": "/test"
            }
            
            response = requests.post(
                f"{self.base_url}/send",
                json=notification_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Send Notification", True, f"Sent to user {data.get('user_id')}")
                return True
            else:
                self.log_test("Send Notification", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Send Notification", False, f"Error: {str(e)}")
            return False
    
    def test_broadcast_notification(self):
        """Test broadcasting notification"""
        try:
            notification_data = {
                "title": "Broadcast Test",
                "body": "This is a broadcast test notification",
                "type": "warning",
                "icon": "megaphone"
            }
            
            response = requests.post(
                f"{self.base_url}/broadcast",
                json=notification_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Broadcast Notification", True, f"Sent to {data.get('sent_count', 0)} users")
                return True
            else:
                self.log_test("Broadcast Notification", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Broadcast Notification", False, f"Error: {str(e)}")
            return False
    
    def test_winner_notification(self):
        """Test winner notification endpoint"""
        try:
            winner_data = {
                "user_id": 8,  # Kenntalk@gmail.com
                "game": "Lotto 6/49",
                "draw_date": "2025-10-06",
                "ticket_number": "TEST-WINNER-001",
                "prize_amount": "$50,000",
                "ticket_id": "77"
            }
            
            response = requests.post(
                f"{self.base_url}/phase1/winner",
                json=winner_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Winner Notification", True, f"Winner notification sent: {data.get('message')}")
                return True
            else:
                self.log_test("Winner Notification", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Winner Notification", False, f"Error: {str(e)}")
            return False
    
    def test_websocket_connection(self):
        """Test WebSocket connection"""
        try:
            # Create SocketIO client
            sio = socketio.Client()
            connected = False
            received_message = False
            
            @sio.on('connect')
            def on_connect():
                nonlocal connected
                connected = True
                print("🔌 WebSocket connected")
            
            @sio.on('connected')
            def on_connected(data):
                nonlocal received_message
                received_message = True
                print(f"📨 Received: {data}")
            
            # Connect to server
            sio.connect(self.socket_url)
            
            # Wait for connection
            time.sleep(2)
            
            if connected:
                self.log_test("WebSocket Connection", True, "Successfully connected")
                
                # Test joining user room
                sio.emit('join_user', {'user_id': 999})
                time.sleep(1)
                
                # Disconnect
                sio.disconnect()
                time.sleep(1)
                
                return True
            else:
                self.log_test("WebSocket Connection", False, "Failed to connect")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"Error: {str(e)}")
            return False
    
    def test_queue_functionality(self):
        """Test notification queue functionality"""
        try:
            # Test getting queue for non-existent user
            response = requests.get(f"{self.base_url}/queue/999", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Queue Check", True, f"Queue for user 999: {data.get('queued_count', 0)} notifications")
                return True
            else:
                self.log_test("Queue Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Queue Check", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Notification Microservice v2 Tests...")
        print("=" * 60)
        
        # Test REST API endpoints
        self.test_health_endpoint()
        self.test_status_endpoint()
        self.test_connections_endpoint()
        self.test_send_notification()
        self.test_broadcast_notification()
        self.test_winner_notification()
        self.test_queue_functionality()
        
        # Test WebSocket functionality
        self.test_websocket_connection()
        
        # Print summary
        print("=" * 60)
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"📊 Test Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Notification Microservice v2 is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the service logs for details.")
        
        return passed == total

def main():
    """Main test function"""
    tester = NotificationTester()
    success = tester.run_all_tests()
    
    # Save test results
    with open('notification_test_results.json', 'w') as f:
        json.dump(tester.test_results, f, indent=2)
    
    print(f"\n📄 Test results saved to: notification_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
