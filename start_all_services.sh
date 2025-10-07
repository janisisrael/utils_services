#!/bin/bash
# Start All Microservices Script
# This script starts all microservices for the Lotto Command Center

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting All Lotto Command Center Microservices${NC}"
echo "=================================================="

# Configuration
PHASE1_DIR="/home/ubuntu/LottoCommandCentre"
UTILS_SERVICES_DIR="/home/ubuntu/LottoCommandCentre/Utils_services"
PYTHON_PATH="/usr/bin/python3"

# Port configuration
PREDICTION_PORT=7000
EMAIL_PORT=7001
NOTIFICATION_PORT=7002
MONITORING_PORT=7003

# Function to check if port is available
check_port() {
    local port=$1
    if netstat -tuln | grep ":$port " > /dev/null; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Port $port is available${NC}"
        return 0
    fi
}

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    local command=$3
    local log_file=$4
    
    echo -e "${BLUE}🚀 Starting $service_name on port $port...${NC}"
    
    if check_port $port; then
        cd "$UTILS_SERVICES_DIR"
        nohup $command > "$log_file" 2>&1 &
        local pid=$!
        
        # Wait a moment for service to start
        sleep 3
        
        # Check if service started successfully
        if pgrep -f "$service_name" > /dev/null; then
            echo -e "${GREEN}✅ $service_name started successfully (PID: $pid)${NC}"
            echo "   Port: $port"
            echo "   Log: $log_file"
            return 0
        else
            echo -e "${RED}❌ Failed to start $service_name${NC}"
            echo "   Check log file: $log_file"
            return 1
        fi
    else
        return 1
    fi
}

# Check if directories exist
if [ ! -d "$PHASE1_DIR" ]; then
    echo -e "${RED}❌ Phase1 directory not found: $PHASE1_DIR${NC}"
    exit 1
fi

if [ ! -d "$UTILS_SERVICES_DIR" ]; then
    echo -e "${RED}❌ Utils_services directory not found: $UTILS_SERVICES_DIR${NC}"
    exit 1
fi

# Install required packages
echo -e "${YELLOW}📦 Installing required packages...${NC}"
pip3 install sendgrid flask flask-cors requests flask-socketio psutil schedule

# Start services
echo -e "${BLUE}🚀 Starting microservices...${NC}"

# 1. Prediction Scheduler (Port 7000)
start_service "prediction_scheduler" $PREDICTION_PORT \
    "$PYTHON_PATH $PHASE1_DIR/src/prediction_scheduler.py" \
    "prediction_scheduler.log"

# 2. Email Microservice (Port 7001)
start_service "email_microservice" $EMAIL_PORT \
    "$PYTHON_PATH email_microservice.py" \
    "email_microservice.log"

# 3. Notification Microservice (Port 7002)
start_service "notification_microservice" $NOTIFICATION_PORT \
    "$PYTHON_PATH notification_microservice.py" \
    "notification_microservice.log"

# 4. Monitoring Microservice (Port 7003)
start_service "monitoring_microservice" $MONITORING_PORT \
    "$PYTHON_PATH monitoring_microservice.py" \
    "monitoring_microservice.log"

echo ""
echo -e "${GREEN}🎉 All microservices started!${NC}"
echo "=================================================="
echo "Service Status:"
echo "  📊 Prediction Scheduler: http://localhost:$PREDICTION_PORT/health"
echo "  📧 Email Microservice:   http://localhost:$EMAIL_PORT/health"
echo "  🔔 Notification Service: http://localhost:$NOTIFICATION_PORT/health"
echo "  📊 Monitoring Service:   http://localhost:$MONITORING_PORT/health"
echo ""
echo "Log Files:"
echo "  📊 Prediction: $UTILS_SERVICES_DIR/prediction_scheduler.log"
echo "  📧 Email:      $UTILS_SERVICES_DIR/email_microservice.log"
echo "  🔔 Notification: $UTILS_SERVICES_DIR/notification_microservice.log"
echo "  📊 Monitoring: $UTILS_SERVICES_DIR/monitoring_microservice.log"
echo ""
echo "To stop all services:"
echo "  pkill -f prediction_scheduler"
echo "  pkill -f email_microservice"
echo "  pkill -f notification_microservice"
echo "  pkill -f monitoring_microservice"
echo ""
echo "To test email service:"
echo "  cd $UTILS_SERVICES_DIR"
echo "  python3 test_email_microservice.py"


