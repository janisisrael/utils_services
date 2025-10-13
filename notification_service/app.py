"""
Notification Microservice
Port: 7002
Purpose: Broadcast notifications, templates, auto-triggers
Database: notifications_db (separate) + writes to lotto_cc.notifications
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import pooling
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

app = Flask(__name__)

# CORS configuration
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 
    'http://localhost:8080,https://www.thesantris.com'
).split(',')

CORS(app, 
     origins=ALLOWED_ORIGINS,
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"])

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'admin123'),
    'database': os.getenv('DB_NAME', 'notifications_db'),
    'pool_name': 'notification_pool',
    'pool_size': 5
}

# Phase1 database (for writing user notifications)
PHASE1_DB_CONFIG = {
    'host': os.getenv('PHASE1_DB_HOST', 'localhost'),
    'user': os.getenv('PHASE1_DB_USER', 'root'),
    'password': os.getenv('PHASE1_DB_PASSWORD', 'admin123'),
    'database': os.getenv('PHASE1_DB_NAME', 'lotto_cc')
}

# Connection pools
try:
    notification_pool = pooling.MySQLConnectionPool(**DB_CONFIG)
    logger.info("[storage] Notification DB pool created")
except Exception as e:
    logger.error(f"[error] Failed to create notification pool: {e}")
    notification_pool = None


def get_notification_db():
    """Get connection from notification database pool"""
    try:
        return notification_pool.get_connection()
    except Exception as e:
        logger.error(f"[error] Failed to get notification DB connection: {e}")
        return None


def get_phase1_db():
    """Get connection to Phase1 database (lotto_cc)"""
    try:
        return mysql.connector.connect(**PHASE1_DB_CONFIG)
    except Exception as e:
        logger.error(f"[error] Failed to connect to Phase1 DB: {e}")
        return None


# ========================================
# USER CACHE FUNCTIONS
# ========================================
def get_users_by_scope(scope='all'):
    """Get users from cache based on scope"""
    conn = get_notification_db()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if scope == 'all':
            query = "SELECT user_id, email FROM user_cache WHERE is_active = 1"
        elif scope in ['premium', 'viewer', 'admin', 'superuser']:
            query = f"SELECT user_id, email FROM user_cache WHERE role = %s AND is_active = 1"
            cursor.execute(query, (scope,))
        else:
            logger.warning(f"[warning] Unknown scope: {scope}")
            return []
        
        if scope == 'all':
            cursor.execute(query)
        
        users = cursor.fetchall()
        logger.info(f"[info] Found {len(users)} users for scope: {scope}")
        return users
        
    except Exception as e:
        logger.error(f"[error] Error fetching users: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def sync_user_to_cache(user_data):
    """Sync user to local cache"""
    conn = get_notification_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO user_cache (user_id, email, user_name, role, is_active)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                email = VALUES(email),
                user_name = VALUES(user_name),
                role = VALUES(role),
                is_active = VALUES(is_active),
                last_synced = NOW()
        """
        cursor.execute(query, (
            user_data['user_id'],
            user_data['email'],
            user_data.get('user_name'),
            user_data.get('role', 'viewer'),
            user_data.get('is_active', True)
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"[error] Error syncing user to cache: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# ========================================
# NOTIFICATION CREATION
# ========================================
def create_user_notification(user_id, title, body, notif_type='info', 
                            priority='normal', module=None, category=None,
                            action_url=None, action_text=None):
    """Create notification in Phase1 database (lotto_cc.notifications)"""
    conn = get_phase1_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO notifications 
            (user_id, title, body, type, priority, platform, module, category,
             action_url, action_text, is_read, is_delivered, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 1, NOW())
        """
        cursor.execute(query, (
            user_id, title, body, notif_type, priority, 
            'phase1', module, category, action_url, action_text
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"[error] Error creating notification for user {user_id}: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# ========================================
# BROADCAST ENDPOINTS
# ========================================
@app.route('/notify/broadcast', methods=['POST'])
def broadcast_notification():
    """
    Broadcast notification to multiple users
    
    Body:
    {
        "title": "Notification title",
        "body": "Notification body",
        "scope": "all|premium|viewer|admin",
        "type": "info|alert|warning|success",
        "priority": "low|normal|high|urgent",
        "module": "optional",
        "category": "optional",
        "action_url": "optional",
        "action_text": "optional"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'title' not in data or 'body' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: title, body"
            }), 400
        
        title = data['title']
        body = data['body']
        scope = data.get('scope', 'all')
        notif_type = data.get('type', 'info')
        priority = data.get('priority', 'normal')
        module = data.get('module')
        category = data.get('category')
        action_url = data.get('action_url')
        action_text = data.get('action_text')
        
        # Get target users from cache
        users = get_users_by_scope(scope)
        
        if not users:
            return jsonify({
                "status": "warning",
                "message": "No users found for scope",
                "scope": scope,
                "sent_count": 0
            })
        
        # Send notification to each user
        sent_count = 0
        failed_count = 0
        
        for user in users:
            success = create_user_notification(
                user['user_id'], title, body, notif_type,
                priority, module, category, action_url, action_text
            )
            if success:
                sent_count += 1
            else:
                failed_count += 1
        
        # Log broadcast
        log_broadcast(title, body, scope, notif_type, sent_count, failed_count)
        
        logger.info(f"[storage] Broadcast sent: {sent_count} users, {failed_count} failed")
        
        return jsonify({
            "status": "success",
            "message": "Broadcast sent",
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total_users": len(users)
        })
        
    except Exception as e:
        logger.error(f"[error] Broadcast error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


def log_broadcast(title, body, scope, notif_type, sent_count, failed_count):
    """Log broadcast to history"""
    conn = get_notification_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO notification_broadcasts 
            (title, body, scope, type, sent_count, failed_count, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        cursor.execute(query, (title, body, scope, notif_type, sent_count, failed_count))
        conn.commit()
    except Exception as e:
        logger.error(f"[error] Error logging broadcast: {e}")
    finally:
        cursor.close()
        conn.close()


# ========================================
# INDIVIDUAL NOTIFICATION
# ========================================
@app.route('/notify', methods=['POST'])
def send_notification():
    """
    Send notification to specific user
    
    Body:
    {
        "user_id": 123,
        "title": "Notification title",
        "body": "Notification body",
        "type": "info",
        "priority": "normal"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data or 'title' not in data or 'body' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: user_id, title, body"
            }), 400
        
        success = create_user_notification(
            data['user_id'],
            data['title'],
            data['body'],
            data.get('type', 'info'),
            data.get('priority', 'normal'),
            data.get('module'),
            data.get('category'),
            data.get('action_url'),
            data.get('action_text')
        )
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Notification sent"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to send notification"
            }), 500
            
    except Exception as e:
        logger.error(f"[error] Send notification error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ========================================
# USER SYNC ENDPOINTS
# ========================================
@app.route('/internal/sync/user', methods=['POST'])
def sync_user():
    """Sync user from Phase1 to local cache"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data or 'email' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: user_id, email"
            }), 400
        
        success = sync_user_to_cache(data)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "User synced to cache"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to sync user"
            }), 500
            
    except Exception as e:
        logger.error(f"[error] User sync error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ========================================
# HEALTH CHECK
# ========================================
@app.route('/health', methods=['GET'])
def health_check():
    """Service health check"""
    try:
        # Check notification DB
        notif_db_ok = False
        conn = get_notification_db()
        if conn:
            conn.close()
            notif_db_ok = True
        
        # Check Phase1 DB
        phase1_db_ok = False
        conn = get_phase1_db()
        if conn:
            conn.close()
            phase1_db_ok = True
        
        status = "healthy" if (notif_db_ok and phase1_db_ok) else "degraded"
        
        return jsonify({
            "status": status,
            "service": "Notification Microservice",
            "port": 7002,
            "databases": {
                "notifications_db": "connected" if notif_db_ok else "disconnected",
                "lotto_cc": "connected" if phase1_db_ok else "disconnected"
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/', methods=['GET'])
def root():
    """Service info"""
    return jsonify({
        "service": "Notification Microservice",
        "version": "1.0.0",
        "port": 7002,
        "endpoints": {
            "/health": "Health check",
            "/notify": "Send notification to user",
            "/notify/broadcast": "Broadcast to multiple users",
            "/internal/sync/user": "Sync user to cache"
        }
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 7002))
    logger.info(f"[storage] Starting Notification Service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
