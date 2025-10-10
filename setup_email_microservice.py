#!/usr/bin/env python3
"""
Email Microservice Setup Script
This script sets up the email microservice as a standalone service on port 8001
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_required_packages():
    """Install required Python packages"""
    packages = ['sendgrid', 'flask', 'flask-cors', 'requests']
    
    try:
        print("📦 Installing required packages...")
        for package in packages:
            print(f"  Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print("✅ All packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
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

def create_usage_tracking_file():
    """Create usage tracking file"""
    try:
        usage_file = Path(__file__).parent / "email_usage.json"
        
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
            
            print("✅ Email usage tracking file created")
        else:
            print("✅ Email usage tracking file already exists")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create usage tracking file: {e}")
        return False

def setup_systemd_service():
    """Setup systemd service"""
    try:
        service_file = Path(__file__).parent / "email-microservice.service"
        systemd_path = Path("/etc/systemd/system/email-microservice.service")
        
        if systemd_path.exists():
            print("⚠️ Systemd service already exists")
            response = input("Do you want to overwrite it? (y/N): ")
            if response.lower() != 'y':
                print("Keeping existing systemd service")
                return True
        
        # Copy service file to systemd directory
        shutil.copy2(service_file, systemd_path)
        
        # Reload systemd
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        
        print("✅ Systemd service installed successfully")
        print("📝 To enable the service: sudo systemctl enable email-microservice")
        print("📝 To start the service: sudo systemctl start email-microservice")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to setup systemd service: {e}")
        return False
    except PermissionError:
        print("⚠️ Permission denied for systemd setup")
        print("📝 You can manually copy email-microservice.service to /etc/systemd/system/")
        return True

def make_scripts_executable():
    """Make shell scripts executable"""
    try:
        script_path = Path(__file__).parent / "start_email_microservice.sh"
        if script_path.exists():
            os.chmod(script_path, 0o755)
            print("✅ Startup script made executable")
        return True
    except Exception as e:
        print(f"❌ Failed to make scripts executable: {e}")
        return False

def test_microservice():
    """Test the microservice"""
    try:
        print("🔍 Testing email microservice...")
        
        # Import and test the microservice
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Test import
        from email_microservice import EmailService
        print("✅ Email microservice imports successfully")
        
        # Test client
        from email_microservice_client import EmailMicroserviceClient
        print("✅ Email microservice client imports successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Microservice test failed: {e}")
        return False

def show_next_steps():
    """Show next steps for the user"""
    print("\n" + "="*60)
    print("🎉 Email Microservice Setup Complete!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Sign up for SendGrid free account at https://sendgrid.com")
    print("2. Create an API key in SendGrid dashboard")
    print("3. Edit .env file and add your SendGrid API key")
    print("4. Update SENDER_EMAIL to your verified sender email")
    print("5. Update ADMIN_EMAIL to receive limit warnings")
    print("\n🚀 Starting the Service:")
    print("Option 1 - Manual start:")
    print("  ./start_email_microservice.sh")
    print("\nOption 2 - Systemd service:")
    print("  sudo systemctl enable email-microservice")
    print("  sudo systemctl start email-microservice")
    print("\n🔧 Integration with Phase 1:")
    print("Replace your email imports:")
    print("  from services.notification.email import send_email")
    print("  # Replace with:")
    print("  from utils_services.email_microservice_client import send_email")
    print("\n📊 Monitoring:")
    print("Health check: http://localhost:8001/health")
    print("Usage status: http://localhost:8001/usage")
    print("Service logs: journalctl -u email-microservice -f")
    print("\n⚠️ Free Tier Limits:")
    print("- 100 emails per day")
    print("- Warnings at 80%, 90%, 95% usage")
    print("- Automatic fallback to Phase 1 at 100% limit")
    print("\n🌐 Port Configuration:")
    print("Email Microservice: Port 8001")
    print("Phase 1 (Main App): Port 6001")
    print("Frontend: Port 8080")
    print("\n📞 Support:")
    print("If you need help, check the logs or contact support")

def main():
    """Main setup function"""
    print("🚀 Email Microservice Setup")
    print("="*40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install required packages
    if not install_required_packages():
        return False
    
    # Create .env file
    if not create_env_file():
        return False
    
    # Create usage tracking file
    if not create_usage_tracking_file():
        return False
    
    # Setup systemd service
    if not setup_systemd_service():
        return False
    
    # Make scripts executable
    if not make_scripts_executable():
        return False
    
    # Test microservice
    if not test_microservice():
        return False
    
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




