#!/usr/bin/env python3
"""
Email Service API - Port 8001
Independent email microservice with REST API
"""

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Email service configuration
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'smtp_username': os.getenv('SMTP_USERNAME'),
    'smtp_password': os.getenv('SMTP_PASSWORD'),
    'sender_email': os.getenv('SENDER_EMAIL'),
    'sender_name': os.getenv('SENDER_NAME', 'Lotto Command Center'),
    'use_tls': os.getenv('USE_TLS', 'true').lower() == 'true',
    'max_emails_per_minute': int(os.getenv('MAX_EMAILS_PER_MINUTE', 60))
}

# Global email service instance
email_service = None

def init_email_service():
    """Initialize the email service"""
    global email_service
    try:
        from .email_service import EmailService
        email_service = EmailService(EMAIL_CONFIG)
        success = email_service.start()
        if success:
            logger.info("✅ Email service initialized successfully")
        else:
            logger.error("❌ Failed to initialize email service")
        return success
    except Exception as e:
        logger.error(f"❌ Error initializing email service: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if email_service:
            health = email_service.health_check()
            return jsonify({
                'status': 'success',
                'service': 'email_service',
                'port': 8001,
                'health': health,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'service': 'email_service',
                'port': 8001,
                'error': 'Email service not initialized',
                'timestamp': datetime.now().isoformat()
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'service': 'email_service',
            'port': 8001,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/send-email', methods=['POST'])
def send_email():
    """Send email endpoint"""
    try:
        if not email_service:
            return jsonify({
                'status': 'error',
                'message': 'Email service not available'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['recipient', 'subject', 'body_html']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Create email task
        from .email_service import EmailTask
        email_task = EmailTask(
            recipient_email=data['recipient'],
            subject=data['subject'],
            body_html=data['body_html'],
            body_text=data.get('body_text'),
            sender_email=data.get('sender_email'),
            priority=data.get('priority', 'normal'),
            max_retries=data.get('max_retries', 3)
        )
        
        # Send email
        success = email_service.send_notification(email_task)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Email queued for sending',
                'task_id': email_task.id,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to queue email',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Error in send_email endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/send-winner-notification', methods=['POST'])
def send_winner_notification():
    """Send winner notification using template"""
    try:
        if not email_service:
            return jsonify({
                'status': 'error',
                'message': 'Email service not available'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        # Validate winner data
        required_fields = ['user_email', 'game', 'ticket_number']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Render template using Phase1 templates
        from .templates import render_template
        try:
            html_content = render_template('winner_notification', data)
            if not html_content:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to render winner notification template'
                }), 400
            
            # Create email task with rendered template
            from .email_service import EmailTask
            email_task = EmailTask(
                recipient_email=data['user_email'],
                subject=f"🎉 Congratulations! You've Won in {data['game']}!",
                body_html=html_content,
                priority='high'
            )
            
            success = email_service.send_notification(email_task)
        except ValueError as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Winner notification sent',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send winner notification',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Error in send_winner_notification endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get email service metrics"""
    try:
        if email_service:
            metrics = email_service.get_metrics()
            return jsonify({
                'status': 'success',
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Email service not available'
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/templates', methods=['GET'])
def list_templates():
    """List available email templates"""
    try:
        from .templates import get_template_info
        template_info = get_template_info()
        return jsonify({
            'status': 'success',
            'templates': template_info,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/send-subscription-expiry', methods=['POST'])
def send_subscription_expiry():
    """Send subscription expiry notification"""
    try:
        if not email_service:
            return jsonify({
                'status': 'error',
                'message': 'Email service not available'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['user_name', 'user_email', 'expiry_date', 'days_remaining', 'subscription_type']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Render template
        from .templates import render_template
        try:
            html_content = render_template('subscription_expiry', data)
            if not html_content:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to render subscription expiry template'
                }), 400
            
            # Create email task
            from .email_service import EmailTask
            email_task = EmailTask(
                recipient_email=data['user_email'],
                subject=f"📅 Your {data['subscription_type']} Subscription Expires Soon",
                body_html=html_content,
                priority='normal'
            )
            
            success = email_service.send_notification(email_task)
        except ValueError as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Subscription expiry notification sent',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send subscription expiry notification',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Error in send_subscription_expiry endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/send-draw-results', methods=['POST'])
def send_draw_results():
    """Send new draw results notification"""
    try:
        if not email_service:
            return jsonify({
                'status': 'error',
                'message': 'Email service not available'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['user_name', 'user_email', 'game', 'draw_date', 'winning_numbers', 'jackpot_amount']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Render template
        from .templates import render_template
        try:
            html_content = render_template('draw_results', data)
            if not html_content:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to render draw results template'
                }), 400
            
            # Create email task
            from .email_service import EmailTask
            email_task = EmailTask(
                recipient_email=data['user_email'],
                subject=f"🎲 New {data['game']} Results - {data['draw_date']}",
                body_html=html_content,
                priority='normal'
            )
            
            success = email_service.send_notification(email_task)
        except ValueError as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Draw results notification sent',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send draw results notification',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Error in send_draw_results endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/config', methods=['GET'])
def get_config():
    """Get email service configuration (non-sensitive)"""
    try:
        safe_config = {
            'service_name': 'email_service',
            'port': 7001,
            'smtp_server': EMAIL_CONFIG['smtp_server'],
            'smtp_port': EMAIL_CONFIG['smtp_port'],
            'sender_name': EMAIL_CONFIG['sender_name'],
            'max_emails_per_minute': EMAIL_CONFIG['max_emails_per_minute'],
            'use_tls': EMAIL_CONFIG['use_tls']
        }
        return jsonify({
            'status': 'success',
            'config': safe_config,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Email Service on port 7001...")
    print("=" * 50)
    
    # Initialize email service
    if init_email_service():
        print("✅ Email service ready")
        print("📡 API Endpoints:")
        print("   POST /send-email")
        print("   POST /send-winner-notification")
        print("   GET  /health")
        print("   GET  /metrics")
        print("   GET  /templates")
        print("   GET  /config")
        print("")
        print("🌐 Access: http://localhost:7001")
        print("=" * 50)
        
        # Run Flask app
        app.run(
            host='0.0.0.0',
            port=7001,
            debug=False,
            threaded=True
        )
    else:
        print("❌ Failed to start email service")
        exit(1)
