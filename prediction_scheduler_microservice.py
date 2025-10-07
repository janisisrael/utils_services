#!/usr/bin/env python3
"""
Prediction Scheduler Microservice - Port 7000
Standalone prediction scheduling service for all phases
"""

import os
import sys
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import threading
import time
import schedule

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

class PredictionScheduler:
    """Prediction scheduling service"""
    
    def __init__(self):
        self.scheduled_jobs = {}
        self.job_history = []
        self.is_running = False
        self.scheduler_thread = None
        
    def add_prediction_job(self, job_id: str, game_type: str, schedule_time: str, 
                          parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new prediction job"""
        try:
            job_data = {
                'job_id': job_id,
                'game_type': game_type,
                'schedule_time': schedule_time,
                'parameters': parameters,
                'created_at': datetime.now().isoformat(),
                'status': 'scheduled'
            }
            
            # Schedule the job
            schedule.every().day.at(schedule_time).do(
                self._execute_prediction_job, job_data
            )
            
            self.scheduled_jobs[job_id] = job_data
            
            logger.info(f"✅ Prediction job scheduled: {job_id} for {game_type} at {schedule_time}")
            
            return {
                'success': True,
                'job_id': job_id,
                'message': f'Prediction job scheduled for {schedule_time}',
                'status': 'scheduled'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to schedule prediction job: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_prediction_job(self, job_data: Dict[str, Any]):
        """Execute a prediction job"""
        job_id = job_data['job_id']
        game_type = job_data['game_type']
        parameters = job_data['parameters']
        
        try:
            logger.info(f"🚀 Executing prediction job: {job_id} for {game_type}")
            
            # Update job status
            self.scheduled_jobs[job_id]['status'] = 'running'
            self.scheduled_jobs[job_id]['started_at'] = datetime.now().isoformat()
            
            # Simulate prediction execution
            # In real implementation, this would call the actual prediction service
            result = self._run_prediction_algorithm(game_type, parameters)
            
            # Update job status
            self.scheduled_jobs[job_id]['status'] = 'completed'
            self.scheduled_jobs[job_id]['completed_at'] = datetime.now().isoformat()
            self.scheduled_jobs[job_id]['result'] = result
            
            # Add to history
            self.job_history.append(self.scheduled_jobs[job_id].copy())
            
            logger.info(f"✅ Prediction job completed: {job_id}")
            
        except Exception as e:
            logger.error(f"❌ Prediction job failed: {job_id} - {e}")
            self.scheduled_jobs[job_id]['status'] = 'failed'
            self.scheduled_jobs[job_id]['error'] = str(e)
            self.scheduled_jobs[job_id]['failed_at'] = datetime.now().isoformat()
    
    def _run_prediction_algorithm(self, game_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run prediction algorithm (placeholder implementation)"""
        # This is a placeholder - in real implementation, this would call actual prediction services
        
        import random
        
        # Simulate prediction processing time
        time.sleep(2)
        
        # Generate mock prediction results
        if game_type.lower() == 'lotto649':
            numbers = sorted(random.sample(range(1, 50), 6))
            bonus = random.randint(1, 49)
        elif game_type.lower() == 'lottomax':
            numbers = sorted(random.sample(range(1, 51), 7))
            bonus = random.randint(1, 50)
        elif game_type.lower() == 'dailygrand':
            numbers = sorted(random.sample(range(1, 50), 5))
            bonus = random.randint(1, 7)
        else:
            numbers = sorted(random.sample(range(1, 50), 6))
            bonus = random.randint(1, 49)
        
        return {
            'predicted_numbers': numbers,
            'bonus_number': bonus,
            'confidence_score': round(random.uniform(0.6, 0.95), 3),
            'algorithm_used': parameters.get('algorithm', 'default'),
            'processing_time': '2.1s'
        }
    
    def get_scheduled_jobs(self) -> Dict[str, Any]:
        """Get all scheduled jobs"""
        return {
            'total_jobs': len(self.scheduled_jobs),
            'jobs': list(self.scheduled_jobs.values())
        }
    
    def get_job_history(self, limit: int = 50) -> Dict[str, Any]:
        """Get job execution history"""
        recent_history = self.job_history[-limit:] if self.job_history else []
        return {
            'total_executions': len(self.job_history),
            'recent_executions': recent_history
        }
    
    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a scheduled job"""
        if job_id in self.scheduled_jobs:
            self.scheduled_jobs[job_id]['status'] = 'cancelled'
            self.scheduled_jobs[job_id]['cancelled_at'] = datetime.now().isoformat()
            
            # Remove from schedule (simplified - in real implementation would need proper job removal)
            logger.info(f"✅ Job cancelled: {job_id}")
            
            return {
                'success': True,
                'message': f'Job {job_id} cancelled successfully'
            }
        else:
            return {
                'success': False,
                'error': f'Job {job_id} not found'
            }
    
    def start_scheduler(self):
        """Start the scheduler thread"""
        if not self.is_running:
            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            logger.info("✅ Prediction scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler thread"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("✅ Prediction scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(5)

# Global scheduler instance
prediction_scheduler = PredictionScheduler()

# Initialize scheduler
prediction_scheduler.start_scheduler()

# API Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'prediction_scheduler',
        'is_running': prediction_scheduler.is_running,
        'scheduled_jobs': len(prediction_scheduler.scheduled_jobs),
        'port': 7000
    }), 200

@app.route('/jobs', methods=['GET'])
def get_jobs():
    """Get all scheduled jobs"""
    return jsonify(prediction_scheduler.get_scheduled_jobs()), 200

@app.route('/history', methods=['GET'])
def get_history():
    """Get job execution history"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify(prediction_scheduler.get_job_history(limit)), 200

@app.route('/schedule', methods=['POST'])
def schedule_job():
    """Schedule a new prediction job"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['job_id', 'game_type', 'schedule_time']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Schedule the job
        result = prediction_scheduler.add_prediction_job(
            job_id=data['job_id'],
            game_type=data['game_type'],
            schedule_time=data['schedule_time'],
            parameters=data.get('parameters', {})
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in schedule_job endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """Cancel a scheduled job"""
    try:
        result = prediction_scheduler.cancel_job(job_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error in cancel_job endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/execute/<job_id>', methods=['POST'])
def execute_job_now(job_id):
    """Execute a job immediately"""
    try:
        if job_id in prediction_scheduler.scheduled_jobs:
            job_data = prediction_scheduler.scheduled_jobs[job_id]
            prediction_scheduler._execute_prediction_job(job_data)
            
            return jsonify({
                'success': True,
                'message': f'Job {job_id} executed successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Job {job_id} not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error in execute_job_now endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get scheduler status"""
    return jsonify({
        'service': 'prediction_scheduler',
        'is_running': prediction_scheduler.is_running,
        'scheduled_jobs_count': len(prediction_scheduler.scheduled_jobs),
        'total_executions': len(prediction_scheduler.job_history),
        'uptime': 'running',
        'port': 7000
    }), 200

if __name__ == '__main__':
    logger.info("🚀 Starting Prediction Scheduler Microservice on port 7000")
    try:
        app.run(host='0.0.0.0', port=7000, debug=False)
    except KeyboardInterrupt:
        logger.info("🛑 Stopping Prediction Scheduler Microservice")
        prediction_scheduler.stop_scheduler()
    except Exception as e:
        logger.error(f"❌ Error starting Prediction Scheduler: {e}")
        prediction_scheduler.stop_scheduler()


