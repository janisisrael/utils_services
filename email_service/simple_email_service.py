#!/usr/bin/env python3
"""
Simple Email Service - Port 7001
Standalone service with .env support
"""

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Email configuration from .env
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_FROM = os.getenv('SMTP_SENDER', os.getenv('SENDER_EMAIL', 'noreply@thesantris.com'))

logger.info(f"📧 SMTP Config: {SMTP_SERVER}:{SMTP_PORT}, User: {SMTP_USERNAME}")

@app.route('/send', methods=['POST'])
def send_email():
    """Send email endpoint"""
    try:
        data = request.json
        recipient = data.get('recipient')
        subject = data.get('subject')
        html_content = data.get('html_content')
        
        if not all([recipient, subject, html_content]):
            return jsonify({"error": "Missing required fields"}), 400
        
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.error("❌ SMTP credentials not configured!")
            return jsonify({"error": "SMTP not configured"}), 500
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_FROM
        msg['To'] = recipient
        msg['Subject'] = subject
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Email sent to {recipient}")
        return jsonify({"message": "Email sent successfully"}), 200
        
    except Exception as e:
        logger.error(f"❌ Error sending email: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "email"}), 200

if __name__ == '__main__':
    print("🚀 Starting Simple Email Service on port 7001...")
    print("=" * 50)
    print(f"📧 SMTP: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"👤 User: {SMTP_USERNAME}")
    print("✅ Email service ready")
    print("📡 Endpoints: POST /send, GET /health")
    app.run(host='0.0.0.0', port=7001, debug=False)
