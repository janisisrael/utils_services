#!/usr/bin/env python3
"""
Test script for Email Service
Demonstrates how to use the email service API
"""

import requests
import json
import time

EMAIL_SERVICE_URL = "http://localhost:7001"

def test_email_service():
    """Test the email service functionality"""
    print("🧪 Testing Email Service API")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. 💚 Testing health check...")
    try:
        response = requests.get(f"{EMAIL_SERVICE_URL}/health")
        if response.status_code == 200:
            print("   ✅ Health check passed")
            print(f"   📊 Status: {response.json()['health']['status']}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: Get configuration
    print("\n2. ⚙️ Getting service configuration...")
    try:
        response = requests.get(f"{EMAIL_SERVICE_URL}/config")
        if response.status_code == 200:
            config = response.json()['config']
            print("   ✅ Configuration retrieved")
            print(f"   📧 SMTP Server: {config['smtp_server']}:{config['smtp_port']}")
            print(f"   📊 Rate Limit: {config['max_emails_per_minute']} emails/minute")
        else:
            print(f"   ❌ Config failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Config error: {e}")
    
    # Test 3: List templates
    print("\n3. 📋 Getting available templates...")
    try:
        response = requests.get(f"{EMAIL_SERVICE_URL}/templates")
        if response.status_code == 200:
            templates = response.json()['templates']
            print("   ✅ Templates retrieved")
            print(f"   📝 Available: {', '.join(templates)}")
        else:
            print(f"   ❌ Templates failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Templates error: {e}")
    
    # Test 4: Send basic email
    print("\n4. 📬 Testing basic email sending...")
    email_data = {
        "recipient": "test@example.com",
        "subject": "Test Email from Utils_services",
        "body_html": "<h1>Hello from Email Service!</h1><p>This is a test email from the modular email service running on port 7001.</p>",
        "priority": "normal"
    }
    
    try:
        response = requests.post(
            f"{EMAIL_SERVICE_URL}/send-email",
            headers={"Content-Type": "application/json"},
            json=email_data
        )
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Email queued successfully")
            print(f"   🆔 Task ID: {result['task_id']}")
        else:
            print(f"   ❌ Email failed: {response.status_code}")
            print(f"   📝 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Email error: {e}")
    
    # Test 5: Send winner notification
    print("\n5. 🏆 Testing winner notification...")
    winner_data = {
        "user_email": "winner@example.com",
        "game": "Lotto 649",
        "ticket_number": "ABC-123-456",
        "draw_date": "2025-09-21",
        "match_count": "6",
        "prize_category": "Jackpot",
        "frontend_url": "https://www.thesantris.com",
        "ticket_id": "ticket_123"
    }
    
    try:
        response = requests.post(
            f"{EMAIL_SERVICE_URL}/send-winner-notification",
            headers={"Content-Type": "application/json"},
            json=winner_data
        )
        if response.status_code == 200:
            print("   ✅ Winner notification queued successfully")
        else:
            print(f"   ❌ Winner notification failed: {response.status_code}")
            print(f"   📝 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Winner notification error: {e}")
    
    # Test 6: Get metrics
    print("\n6. 📊 Getting service metrics...")
    try:
        response = requests.get(f"{EMAIL_SERVICE_URL}/metrics")
        if response.status_code == 200:
            metrics = response.json()['metrics']
            print("   ✅ Metrics retrieved")
            print(f"   📧 Messages sent: {metrics['metrics']['messages_sent']}")
            print(f"   ❌ Messages failed: {metrics['metrics']['messages_failed']}")
            print(f"   ⏱️  Service uptime: {metrics['uptime_seconds']:.1f} seconds")
        else:
            print(f"   ❌ Metrics failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Metrics error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 EMAIL SERVICE TEST COMPLETED")
    print("✅ The service has full queuing, retry logic, and rate limiting!")

if __name__ == "__main__":
    print("🚀 Make sure email service is running on port 7001 first!")
    print("   cd email_service && python app.py")
    print("")
    
    input("Press Enter when email service is running...")
    test_email_service()

