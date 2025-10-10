#!/bin/bash
# Notification Microservice v2 Startup Script
# This script starts the notification microservice on port 7002

# Configuration
SERVICE_NAME="notification-microservice-v2"
SERVICE_PORT=7002
SERVICE_DIR="/home/ubuntu/LottoCommandCentre/Utils_services"
LOG_FILE="notification_microservice_v2.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Notification Microservice v2...${NC}"

# Check if service is already running
if pgrep -f "notification_microservice_v2.py" > /dev/null; then
    echo -e "${YELLOW}⚠️  Notification microservice v2 is already running${NC}"
    echo -e "${YELLOW}   Stopping existing service...${NC}"
    pkill -f "notification_microservice_v2.py"
    sleep 2
fi

# Check if port is in use
if lsof -i :$SERVICE_PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port $SERVICE_PORT is already in use${NC}"
    echo -e "${YELLOW}   Attempting to free port...${NC}"
    fuser -k $SERVICE_PORT/tcp
    sleep 2
fi

# Change to service directory
cd "$SERVICE_DIR" || {
    echo -e "${RED}❌ Error: Cannot change to directory $SERVICE_DIR${NC}"
    exit 1
}

# Check if virtual environment exists
if [ ! -d "notification_env" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv notification_env
fi

# Activate virtual environment
source notification_env/bin/activate

# Install/upgrade dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install --upgrade flask flask-socketio flask-cors requests

# Start the service
echo -e "${GREEN}🚀 Starting $SERVICE_NAME on port $SERVICE_PORT...${NC}"
nohup python3 notification_microservice_v2.py > "$LOG_FILE" 2>&1 &

# Get the process ID
SERVICE_PID=$!

# Wait a moment for the service to start
sleep 3

# Check if the service started successfully
if pgrep -f "notification_microservice_v2.py" > /dev/null; then
    echo -e "${GREEN}✅ $SERVICE_NAME started successfully!${NC}"
    echo -e "${GREEN}   Process ID: $SERVICE_PID${NC}"
    echo -e "${GREEN}   Port: $SERVICE_PORT${NC}"
    echo -e "${GREEN}   Log file: $SERVICE_DIR/$LOG_FILE${NC}"
    echo -e "${GREEN}   Health check: http://localhost:$SERVICE_PORT/health${NC}"
else
    echo -e "${RED}❌ Failed to start $SERVICE_NAME${NC}"
    echo -e "${RED}   Check the log file: $SERVICE_DIR/$LOG_FILE${NC}"
    exit 1
fi

# Test the service
echo -e "${BLUE}🔍 Testing service health...${NC}"
sleep 2

if curl -s http://localhost:$SERVICE_PORT/health > /dev/null; then
    echo -e "${GREEN}✅ Service is responding to health checks${NC}"
else
    echo -e "${YELLOW}⚠️  Service may still be starting up${NC}"
fi

echo -e "${BLUE}📋 Service Information:${NC}"
echo -e "   ${BLUE}Service Name:${NC} $SERVICE_NAME"
echo -e "   ${BLUE}Port:${NC} $SERVICE_PORT"
echo -e "   ${BLUE}Process ID:${NC} $SERVICE_PID"
echo -e "   ${BLUE}Log File:${NC} $SERVICE_DIR/$LOG_FILE"
echo -e "   ${BLUE}Health Check:${NC} http://localhost:$SERVICE_PORT/health"
echo -e "   ${BLUE}Status:${NC} http://localhost:$SERVICE_PORT/status"
echo -e "   ${BLUE}Connections:${NC} http://localhost:$SERVICE_PORT/connections"

echo -e "${GREEN}🎉 Notification Microservice v2 is ready!${NC}"




