#!/bin/bash
# Email Microservice Startup Script
# This script starts the email microservice on port 7001

# Configuration
SERVICE_NAME="email-microservice"
SERVICE_PORT=7001
SERVICE_DIR="/home/ubuntu/LottoCommandCentre/Utils_services"
SERVICE_USER="ubuntu"
PYTHON_PATH="/usr/bin/python3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Email Microservice${NC}"
echo "=================================="

# Check if service is already running
if pgrep -f "email_microservice.py" > /dev/null; then
    echo -e "${YELLOW}⚠️ Email microservice is already running${NC}"
    echo "PID: $(pgrep -f email_microservice.py)"
    echo "Port: $SERVICE_PORT"
    exit 0
fi

# Check if port is available
if netstat -tuln | grep ":$SERVICE_PORT " > /dev/null; then
    echo -e "${RED}❌ Port $SERVICE_PORT is already in use${NC}"
    echo "Please stop the service using that port first"
    exit 1
fi

# Check if service directory exists
if [ ! -d "$SERVICE_DIR" ]; then
    echo -e "${RED}❌ Service directory not found: $SERVICE_DIR${NC}"
    exit 1
fi

# Check if Python script exists
if [ ! -f "$SERVICE_DIR/email_microservice.py" ]; then
    echo -e "${RED}❌ Email microservice script not found${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f "$SERVICE_DIR/.env" ]; then
    echo -e "${YELLOW}⚠️ .env file not found, creating from template${NC}"
    if [ -f "$SERVICE_DIR/sendgrid_env_template.txt" ]; then
        cp "$SERVICE_DIR/sendgrid_env_template.txt" "$SERVICE_DIR/.env"
        echo -e "${YELLOW}📝 Please edit $SERVICE_DIR/.env with your SendGrid API key${NC}"
    else
        echo -e "${RED}❌ No .env template found${NC}"
        exit 1
    fi
fi

# Install required packages
echo -e "${GREEN}📦 Installing required packages...${NC}"
pip3 install sendgrid flask flask-cors requests

# Start the service
echo -e "${GREEN}🚀 Starting email microservice on port $SERVICE_PORT...${NC}"
cd "$SERVICE_DIR"

# Start in background
nohup $PYTHON_PATH email_microservice.py > email_microservice.log 2>&1 &
SERVICE_PID=$!

# Wait a moment for service to start
sleep 3

# Check if service started successfully
if pgrep -f "email_microservice.py" > /dev/null; then
    echo -e "${GREEN}✅ Email microservice started successfully${NC}"
    echo "PID: $SERVICE_PID"
    echo "Port: $SERVICE_PORT"
    echo "Log file: $SERVICE_DIR/email_microservice.log"
    echo "Health check: http://localhost:$SERVICE_PORT/health"
    echo "Usage status: http://localhost:$SERVICE_PORT/usage"
else
    echo -e "${RED}❌ Failed to start email microservice${NC}"
    echo "Check log file: $SERVICE_DIR/email_microservice.log"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Email Microservice is now running!${NC}"
echo "=================================="
echo "Service: $SERVICE_NAME"
echo "Port: $SERVICE_PORT"
echo "PID: $SERVICE_PID"
echo "Log: $SERVICE_DIR/email_microservice.log"
echo ""
echo "API Endpoints:"
echo "  Health: http://localhost:$SERVICE_PORT/health"
echo "  Usage:  http://localhost:$SERVICE_PORT/usage"
echo "  Send:   http://localhost:$SERVICE_PORT/send"
echo "  Winner: http://localhost:$SERVICE_PORT/send-winner"
echo ""
echo "To stop the service:"
echo "  kill $SERVICE_PID"
echo "  or"
echo "  pkill -f email_microservice.py"
