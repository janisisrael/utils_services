#!/usr/bin/env python3
"""
Email Microservice Test Script
This script tests the email microservice functionality
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

# Configuration
EMAIL_SERVICE_URL = "http://localhost:7001"
TEST_EMAIL = "test@example.com"  # Change this to your test email

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{EMAIL_SERVICE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   Service: {data['service']}")
            print(f"   SendGrid available: {data.get('sendgrid_available', False)}")
            print(f"   Port: {data.get('port', 'unknown')}")
            return True
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to email service at {EMAIL_SERVICE_URL}")
        print("   Make sure the email microservice is running on port 7001")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_usage_status():
    """Test usage status endpoint"""
    print("\n📊 Testing usage status...")
    try:
        response = requests.get(f"{EMAIL_SERVICE_URL}/usage", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Usage status retrieved:")
            print(f"   Emails sent today: {data.get('emails_sent_today', 0)}")
            print(f"   Daily limit: {data.get('daily_limit', 100)}")
            print(f"   Remaining: {data.get('remaining', 0)}")
            print(f"   Percentage used: {data.get('percentage_used', 0)}%")
            return True
        else:
            print(f"❌ Usage status failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Usage status error: {e}")
        return False

def test_send_email():
    """Test sending a simple email"""
    print(f"\n📧 Testing email send to {TEST_EMAIL}...")
    
    email_data = {
        "recipient": TEST_EMAIL,
        "subject": "🧪 Test Email from Lotto Command Center",
        "html_content": """
        <h1>Test Email</h1>
        <p>This is a test email from the Lotto Command Center email microservice.</p>
        <p><strong>Timestamp:</strong> {}</p>
        <p>If you receive this email, the microservice is working correctly!</p>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        "plain_text": f"Test Email\n\nThis is a test email from the Lotto Command Center email microservice.\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nIf you receive this email, the microservice is working correctly!"
    }
    
    try:
        response = requests.post(f"{EMAIL_SERVICE_URL}/send", json=email_data, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Email sent successfully!")
            print(f"   Service: {data.get('service', 'unknown')}")
            print(f"   Status code: {data.get('status_code', 'unknown')}")
            print(f"   Message: {data.get('message', 'No message')}")
            
            # Check for warnings
            usage_status = data.get('usage_status', {})
            for warning in usage_status.get('warnings', []):
                print(f"   ⚠️ Warning: {warning}")
            
            return True
        else:
            print(f"❌ Email send failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Email send error: {e}")
        return False

def test_send_winner_notification():
    """Test sending a winner notification (Phase 1 format)"""
    print(f"\n🎉 Testing winner notification to {TEST_EMAIL}...")
    
    winner_data = {
        "user_email": TEST_EMAIL,
        "user_name": "Test Winner",
        "game": "Lotto 6/49",
        "draw_date": "2025-01-06",
        "ticket_number": "TEST-123456",
        "ticket_id": "TEST-001",
        "winners": {
            "Lotto 6/49": [{
                "matched_numbers": [1, 2, 3, 4, 5, 6],
                "prize_amount": "$5,000",
                "prize_category": "3 of 6"
            }]
        }
    }
    
    try:
        response = requests.post(f"{EMAIL_SERVICE_URL}/send-winner", json=winner_data, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Winner notification sent successfully!")
            print(f"   Service: {data.get('service', 'unknown')}")
            print(f"   Status code: {data.get('status_code', 'unknown')}")
            print(f"   Message: {data.get('message', 'No message')}")
            
            # Check for warnings
            usage_status = data.get('usage_status', {})
            for warning in usage_status.get('warnings', []):
                print(f"   ⚠️ Warning: {warning}")
            
            return True
        else:
            print(f"❌ Winner notification failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Winner notification error: {e}")
        return False

def test_usage_after_sending():
    """Test usage status after sending emails"""
    print("\n📊 Testing usage status after sending emails...")
    try:
        response = requests.get(f"{EMAIL_SERVICE_URL}/usage", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Updated usage status:")
            print(f"   Emails sent today: {data.get('emails_sent_today', 0)}")
            print(f"   Daily limit: {data.get('daily_limit', 100)}")
            print(f"   Remaining: {data.get('remaining', 0)}")
            print(f"   Percentage used: {data.get('percentage_used', 0)}%")
            
            # Check if we're approaching limits
            percentage = data.get('percentage_used', 0)
            if percentage > 80:
                print(f"   ⚠️ Approaching daily limit: {percentage}%")
            elif percentage > 90:
                print(f"   🚨 Near daily limit: {percentage}%")
            
            return True
        else:
            print(f"❌ Usage status failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Usage status error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Email Microservice Test Suite")
    print("=" * 50)
    
    # Check if test email is configured
    if TEST_EMAIL == "test@example.com":
        print("⚠️ Using default test email: test@example.com")
        print("   To test with a real email, edit TEST_EMAIL in this script")
        response = input("   Continue with default email? (y/N): ")
        if response.lower() != 'y':
            print("❌ Test cancelled")
            return
    
    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("Usage Status", test_usage_status),
        ("Send Email", test_send_email),
        ("Send Winner Notification", test_send_winner_notification),
        ("Usage After Sending", test_usage_after_sending)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
        
        # Wait between tests
        time.sleep(2)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Email microservice is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    print(f"\n📧 Test emails sent to: {TEST_EMAIL}")
    print("   Check your email inbox (and spam folder) for test messages.")

if __name__ == "__main__":
    main()




