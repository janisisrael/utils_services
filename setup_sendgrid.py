#!/usr/bin/env python3
"""
SendGrid Integration Setup Script
This script helps set up SendGrid integration for Phase 1
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_sendgrid():
    """Install SendGrid Python library"""
    try:
        print("📦 Installing SendGrid Python library...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "sendgrid"])
        print("✅ SendGrid library installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install SendGrid: {e}")
        return False

def create_env_file():
    """Create .env file from template"""
    env_template_path = Path(__file__).parent / "sendgrid_env_template.txt"
    env_path = Path(__file__).parent / ".env"
    
    if env_path.exists():
        print("⚠️ .env file already exists")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing .env file")
            return True
    
    try:
        with open(env_template_path, 'r') as template_file:
            template_content = template_file.read()
        
        with open(env_path, 'w') as env_file:
            env_file.write(template_content)
        
        print("✅ .env file created from template")
        print("📝 Please edit .env file and add your SendGrid API key")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def test_sendgrid_connection():
    """Test SendGrid connection"""
    try:
        print("🔍 Testing SendGrid connection...")
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('SENDGRID_API_KEY')
        if not api_key or api_key == 'your-sendgrid-api-key-here':
            print("⚠️ SendGrid API key not configured in .env file")
            return False
        
        # Test import
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content
        
        # Test client creation
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        print("✅ SendGrid client created successfully")
        
        return True
    except ImportError:
        print("❌ SendGrid library not installed")
        return False
    except Exception as e:
        print(f"❌ SendGrid connection test failed: {e}")
        return False

def create_usage_tracking_file():
    """Create usage tracking file"""
    try:
        usage_file = Path(__file__).parent / "sendgrid_usage.json"
        
        if not usage_file.exists():
            initial_data = {
                "current_date": "2025-01-01",
                "emails_sent_today": 0,
                "last_reset": "2025-01-01T00:00:00",
                "total_emails_sent": 0,
                "warnings_sent_today": []
            }
            
            with open(usage_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
            
            print("✅ SendGrid usage tracking file created")
        else:
            print("✅ SendGrid usage tracking file already exists")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create usage tracking file: {e}")
        return False

def show_next_steps():
    """Show next steps for the user"""
    print("\n" + "="*60)
    print("🎉 SendGrid Integration Setup Complete!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Sign up for SendGrid free account at https://sendgrid.com")
    print("2. Create an API key in SendGrid dashboard")
    print("3. Edit .env file and add your SendGrid API key")
    print("4. Update SENDER_EMAIL to your verified sender email")
    print("5. Update ADMIN_EMAIL to receive limit warnings")
    print("\n🔧 Integration:")
    print("To use SendGrid in Phase 1, replace your email imports:")
    print("  from services.notification.email import send_email")
    print("  # Replace with:")
    print("  from utils_services.phase1_sendgrid_integration import send_email")
    print("\n📊 Monitoring:")
    print("Check SendGrid usage: get_sendgrid_usage()")
    print("Check service health: get_email_service_status()")
    print("\n⚠️ Free Tier Limits:")
    print("- 100 emails per day")
    print("- Warnings at 80%, 90%, 95% usage")
    print("- Automatic fallback to Phase 1 at 100% limit")
    print("\n📞 Support:")
    print("If you need help, check the logs or contact support")

def main():
    """Main setup function"""
    print("🚀 SendGrid Integration Setup")
    print("="*40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install SendGrid
    if not install_sendgrid():
        return False
    
    # Create .env file
    if not create_env_file():
        return False
    
    # Create usage tracking file
    if not create_usage_tracking_file():
        return False
    
    # Test connection (optional)
    print("\n🔍 Testing SendGrid connection...")
    if test_sendgrid_connection():
        print("✅ SendGrid connection test passed")
    else:
        print("⚠️ SendGrid connection test failed - check your .env configuration")
    
    # Show next steps
    show_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Setup completed successfully!")
        else:
            print("\n❌ Setup failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)




