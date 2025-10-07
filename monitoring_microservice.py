#!/usr/bin/env python3
"""
Monitoring Microservice - Port 7003
Standalone monitoring service for all phases
"""

import os
import sys
import logging
import json
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import threading
import requests

from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

class MonitoringService:
    """Monitoring service for system and application metrics"""
    
    def __init__(self):
        self.metrics_history = []
        self.service_endpoints = {
            'phase1': 'http://localhost:6001',
            'email_service': 'http://localhost:7001',
            'notification_service': 'http://localhost:7002',
            'prediction_scheduler': 'http://localhost:7000'
        }
        self.alerts = []
        self.is_monitoring = False
        self.monitoring_thread = None
        
    def start_monitoring(self):
        """Start monitoring thread"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("✅ Monitoring service started")
    
    def stop_monitoring(self):
        """Stop monitoring thread"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("✅ Monitoring service stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                
                # Check service health
                service_health = self._check_service_health()
                
                # Combine metrics
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'system': system_metrics,
                    'services': service_health
                }
                
                # Store metrics
                self.metrics_history.append(metrics)
                
                # Keep only last 1000 entries
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                # Check for alerts
                self._check_alerts(metrics)
                
                # Wait before next check
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            return {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def _check_service_health(self) -> Dict[str, Any]:
        """Check health of all services"""
        service_status = {}
        
        for service_name, endpoint in self.service_endpoints.items():
            try:
                response = requests.get(f"{endpoint}/health", timeout=5)
                if response.status_code == 200:
                    service_status[service_name] = {
                        'status': 'healthy',
                        'response_time': response.elapsed.total_seconds(),
                        'endpoint': endpoint
                    }
                else:
                    service_status[service_name] = {
                        'status': 'unhealthy',
                        'error': f'HTTP {response.status_code}',
                        'endpoint': endpoint
                    }
            except requests.exceptions.ConnectionError:
                service_status[service_name] = {
                    'status': 'down',
                    'error': 'Connection refused',
                    'endpoint': endpoint
                }
            except requests.exceptions.Timeout:
                service_status[service_name] = {
                    'status': 'timeout',
                    'error': 'Request timeout',
                    'endpoint': endpoint
                }
            except Exception as e:
                service_status[service_name] = {
                    'status': 'error',
                    'error': str(e),
                    'endpoint': endpoint
                }
        
        return service_status
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        """Check for alert conditions"""
        try:
            system = metrics.get('system', {})
            services = metrics.get('services', {})
            
            # CPU alert
            cpu_percent = system.get('cpu_percent', 0)
            if cpu_percent > 80:
                self._create_alert('high_cpu', f'High CPU usage: {cpu_percent}%', 'warning')
            
            # Memory alert
            memory_percent = system.get('memory', {}).get('percent', 0)
            if memory_percent > 85:
                self._create_alert('high_memory', f'High memory usage: {memory_percent}%', 'warning')
            
            # Disk alert
            disk_percent = system.get('disk', {}).get('percent', 0)
            if disk_percent > 90:
                self._create_alert('high_disk', f'High disk usage: {disk_percent}%', 'critical')
            
            # Service alerts
            for service_name, status in services.items():
                if status.get('status') not in ['healthy']:
                    self._create_alert(
                        f'service_{service_name}',
                        f'Service {service_name} is {status.get("status")}',
                        'critical'
                    )
        
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _create_alert(self, alert_type: str, message: str, severity: str):
        """Create a new alert"""
        alert = {
            'alert_id': f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(alert_type)}",
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Check if similar alert already exists
        existing_alert = next(
            (a for a in self.alerts if a['type'] == alert_type and a['status'] == 'active'),
            None
        )
        
        if not existing_alert:
            self.alerts.append(alert)
            logger.warning(f"🚨 ALERT: {message}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return {}
    
    def get_metrics_history(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics history for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        return {
            'period_hours': hours,
            'total_metrics': len(filtered_metrics),
            'metrics': filtered_metrics
        }
    
    def get_active_alerts(self) -> Dict[str, Any]:
        """Get active alerts"""
        active_alerts = [a for a in self.alerts if a['status'] == 'active']
        return {
            'total_alerts': len(active_alerts),
            'alerts': active_alerts
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get monitoring service status"""
        return {
            'service': 'monitoring_microservice',
            'is_monitoring': self.is_monitoring,
            'total_metrics_collected': len(self.metrics_history),
            'active_alerts': len([a for a in self.alerts if a['status'] == 'active']),
            'monitored_services': list(self.service_endpoints.keys()),
            'port': 7003
        }

# Global monitoring service instance
monitoring_service = MonitoringService()

# Initialize monitoring
monitoring_service.start_monitoring()

# API Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    status = monitoring_service.get_service_status()
    status['status'] = 'healthy'
    return jsonify(status), 200

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get current metrics"""
    return jsonify(monitoring_service.get_current_metrics()), 200

@app.route('/metrics/history', methods=['GET'])
def get_metrics_history():
    """Get metrics history"""
    hours = request.args.get('hours', 24, type=int)
    return jsonify(monitoring_service.get_metrics_history(hours)), 200

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Get active alerts"""
    return jsonify(monitoring_service.get_active_alerts()), 200

@app.route('/services', methods=['GET'])
def get_services_status():
    """Get status of all monitored services"""
    return jsonify(monitoring_service._check_service_health()), 200

@app.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get dashboard data"""
    try:
        current_metrics = monitoring_service.get_current_metrics()
        active_alerts = monitoring_service.get_active_alerts()
        service_status = monitoring_service.get_service_status()
        
        return jsonify({
            'current_metrics': current_metrics,
            'active_alerts': active_alerts,
            'service_status': service_status,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get monitoring service status"""
    return jsonify(monitoring_service.get_service_status()), 200

if __name__ == '__main__':
    logger.info("🚀 Starting Monitoring Microservice on port 7003")
    try:
        app.run(host='0.0.0.0', port=7003, debug=False)
    except KeyboardInterrupt:
        logger.info("🛑 Stopping Monitoring Microservice")
        monitoring_service.stop_monitoring()
    except Exception as e:
        logger.error(f"❌ Error starting Monitoring Microservice: {e}")
        monitoring_service.stop_monitoring()

