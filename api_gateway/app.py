"""
API Gateway Service
Port: 8000
Purpose: Route traffic to microservices to reduce Phase1 load
"""

from flask import Flask, request, Response
from flask_cors import CORS
import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# CORS configuration
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 
    'http://localhost:8080,http://127.0.0.1:8080,https://www.thesantris.com,https://thesantris.com'
).split(',')

CORS(app, 
     origins=ALLOWED_ORIGINS,
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Service Registry - Mapping of services to their ports
SERVICES = {
    'phase1': os.getenv('PHASE1_URL', 'http://localhost:5001'),
    'phase1_alt': os.getenv('PHASE1_ALT_URL', 'http://localhost:6001'),
    'notification': os.getenv('NOTIFICATION_URL', 'http://localhost:7002'),
    'email': os.getenv('EMAIL_URL', 'http://localhost:7001'),
    'prediction': os.getenv('PREDICTION_URL', 'http://localhost:7000'),
    'monitoring': os.getenv('MONITORING_URL', 'http://localhost:7003'),
    'port_watcher': os.getenv('PORT_WATCHER_URL', 'http://localhost:7004')
}

def proxy_request(service_url, path='', strip_prefix=''):
    """
    Proxy request to microservice
    
    Args:
        service_url: Base URL of the target service
        path: Additional path to append
        strip_prefix: Prefix to remove from original path
    """
    try:
        # Build target URL
        if strip_prefix and request.path.startswith(strip_prefix):
            remaining_path = request.path[len(strip_prefix):]
        else:
            remaining_path = path or request.path
        
        target_url = f"{service_url}{remaining_path}"
        
        # Log the routing
        logger.info(f"[GATEWAY] {request.method} {request.path} → {target_url}")
        
        # Prepare headers (exclude Host header)
        headers = {
            key: value for key, value in request.headers 
            if key.lower() not in ['host', 'connection']
        }
        
        # Forward request to target service
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.args,
            json=request.get_json(silent=True),
            data=request.get_data() if not request.is_json else None,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=30
        )
        
        # Create response with same status and headers
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [
            (name, value) for name, value in response.raw.headers.items()
            if name.lower() not in excluded_headers
        ]
        
        return Response(
            response.content,
            status=response.status_code,
            headers=response_headers
        )
        
    except requests.exceptions.Timeout:
        logger.error(f"[GATEWAY] Timeout calling {service_url}")
        return {"error": "Service timeout", "service": service_url}, 504
        
    except requests.exceptions.ConnectionError:
        logger.error(f"[GATEWAY] Connection error to {service_url}")
        return {"error": "Service unavailable", "service": service_url}, 503
        
    except Exception as e:
        logger.error(f"[GATEWAY] Error proxying request: {e}")
        return {"error": "Gateway error", "details": str(e)}, 500


# ========================================
# NOTIFICATION SERVICE ROUTES
# ========================================
@app.route('/notif/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def route_notification(subpath):
    """Route /notif/* to Notification Service (7002)"""
    return proxy_request(SERVICES['notification'], f'/notification/{subpath}')


@app.route('/notif', methods=['GET', 'POST'])
def route_notification_root():
    """Route /notif to Notification Service root"""
    return proxy_request(SERVICES['notification'], '/notification')


# ========================================
# EMAIL SERVICE ROUTES
# ========================================
@app.route('/email/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_email(subpath):
    """Route /email/* to Email Service (7001)"""
    return proxy_request(SERVICES['email'], f'/email/{subpath}')


@app.route('/email', methods=['POST'])
def route_email_root():
    """Route /email to Email Service root"""
    return proxy_request(SERVICES['email'], '/email')


# ========================================
# PREDICTION SERVICE ROUTES
# ========================================
@app.route('/pred/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_prediction(subpath):
    """Route /pred/* to Prediction Service (7000)"""
    return proxy_request(SERVICES['prediction'], f'/prediction/{subpath}')


# ========================================
# MONITORING SERVICE ROUTES
# ========================================
@app.route('/monitor/<path:subpath>', methods=['GET'])
def route_monitoring(subpath):
    """Route /monitor/* to Monitoring Service (7003)"""
    return proxy_request(SERVICES['monitoring'], f'/{subpath}')


@app.route('/monitor', methods=['GET'])
def route_monitoring_root():
    """Route /monitor to Monitoring Service root"""
    return proxy_request(SERVICES['monitoring'], '/')


# ========================================
# PHASE1 ROUTES (Fallback for non-migrated routes)
# ========================================
@app.route('/p1/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def route_phase1(subpath):
    """Route /p1/* to Phase1 Backend (5001/6001)"""
    return proxy_request(SERVICES['phase1'], f'/p1/{subpath}')


# ========================================
# HEALTH CHECK & INFO
# ========================================
@app.route('/health', methods=['GET'])
def health_check():
    """Gateway health check"""
    return {
        "status": "healthy",
        "service": "API Gateway",
        "version": "1.0.0",
        "services": {
            name: url for name, url in SERVICES.items()
        }
    }


@app.route('/routes', methods=['GET'])
def list_routes():
    """List all available routes"""
    return {
        "gateway_routes": {
            "/notif/*": f"Notification Service ({SERVICES['notification']})",
            "/email/*": f"Email Service ({SERVICES['email']})",
            "/pred/*": f"Prediction Service ({SERVICES['prediction']})",
            "/monitor/*": f"Monitoring Service ({SERVICES['monitoring']})",
            "/p1/*": f"Phase1 Backend ({SERVICES['phase1']})"
        },
        "services": SERVICES
    }


@app.route('/', methods=['GET'])
def root():
    """Gateway root - show info"""
    return {
        "service": "The Santris API Gateway",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "/health": "Health check",
            "/routes": "List available routes",
            "/notif/*": "Notification service",
            "/email/*": "Email service",
            "/pred/*": "Prediction service",
            "/monitor/*": "Monitoring service",
            "/p1/*": "Phase1 backend (legacy)"
        }
    }


# ========================================
# ERROR HANDLERS
# ========================================
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return {
        "error": "Route not found",
        "path": request.path,
        "available_prefixes": ["/notif", "/email", "/pred", "/monitor", "/p1"]
    }, 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}")
    return {
        "error": "Internal gateway error",
        "details": str(error)
    }, 500


if __name__ == '__main__':
    port = int(os.getenv('GATEWAY_PORT', 8000))
    logger.info(f"[storage] Starting API Gateway on port {port}")
    logger.info(f"[storage] Service registry: {SERVICES}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('DEBUG', 'False').lower() == 'true'
    )
