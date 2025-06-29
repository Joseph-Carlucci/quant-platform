#!/bin/bash

# Quantitative Research Platform - Connection Script
# Convenient access to your deployed services via port-forwarding

set -e

NAMESPACE="quant-platform"
# Use different ports to avoid conflicts with local Docker services
AIRFLOW_LOCAL_PORT=8081  # Local Docker uses 8080
PGADMIN_LOCAL_PORT=5051  # Local Docker uses 5050

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Quant Platform Connection Manager${NC}"
echo "======================================"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl first.${NC}"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl get namespaces &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster.${NC}"
    echo "Make sure you're connected to the right cluster:"
    echo "aws eks update-kubeconfig --region us-east-1 --name quant-platform"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${RED}❌ Namespace '$NAMESPACE' not found.${NC}"
    echo "Deploy the platform first: ./k8s/deploy.sh"
    exit 1
fi

# Function to check if port is already in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start port forwarding
start_port_forward() {
    local service=$1
    local local_port=$2
    local remote_port=$3
    local service_name=$4
    
    echo -e "${YELLOW}🔗 Starting port-forward for $service_name...${NC}"
    
    if check_port $local_port; then
        echo -e "${YELLOW}⚠️  Port $local_port is already in use. Trying to kill existing process...${NC}"
        lsof -ti:$local_port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    kubectl port-forward -n $NAMESPACE service/$service $local_port:$remote_port &
    local pid=$!
    echo $pid > /tmp/quant-$service-port-forward.pid
    
    # Wait a moment for port-forward to establish
    sleep 3
    
    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}✅ $service_name accessible at http://localhost:$local_port${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to start port-forward for $service_name${NC}"
        return 1
    fi
}

# Function to stop port forwarding
stop_port_forward() {
    local service=$1
    local service_name=$2
    
    if [ -f /tmp/quant-$service-port-forward.pid ]; then
        local pid=$(cat /tmp/quant-$service-port-forward.pid)
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid
            echo -e "${GREEN}✅ Stopped port-forward for $service_name${NC}"
        fi
        rm -f /tmp/quant-$service-port-forward.pid
    fi
}

# Function to check service status
check_service_status() {
    echo -e "${BLUE}📊 Checking service status...${NC}"
    echo ""
    
    local services=("postgres" "redis" "airflow" "pgadmin")
    
    for service in "${services[@]}"; do
        if kubectl get deployment $service -n $NAMESPACE &> /dev/null; then
            local ready=$(kubectl get deployment $service -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
            local desired=$(kubectl get deployment $service -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "1")
            
            if [ "$ready" = "$desired" ] && [ "$ready" != "0" ]; then
                echo -e "  ${GREEN}✅ $service: Ready ($ready/$desired)${NC}"
            else
                echo -e "  ${RED}❌ $service: Not ready ($ready/$desired)${NC}"
            fi
        else
            echo -e "  ${RED}❌ $service: Not found${NC}"
        fi
    done
    echo ""
}

# Main menu
show_menu() {
    echo "Select an option:"
    echo "1) Connect to Production Airflow (http://localhost:$AIRFLOW_LOCAL_PORT)"
    echo "2) Connect to Production pgAdmin (http://localhost:$PGADMIN_LOCAL_PORT)"
    echo "3) Connect to both production services"
    echo "4) Check service status"
    echo "5) Stop all connections"
    echo "6) Show connection info"
    echo "7) Exit"
    echo ""
}

# Show current connections
show_connections() {
    echo -e "${BLUE}🔗 Current Connections:${NC}"
    echo ""
    
    if [ -f /tmp/quant-airflow-port-forward.pid ]; then
        local pid=$(cat /tmp/quant-airflow-port-forward.pid)
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "  ${GREEN}✅ Airflow: http://localhost:$AIRFLOW_LOCAL_PORT${NC}"
        else
            rm -f /tmp/quant-airflow-port-forward.pid
        fi
    fi
    
    if [ -f /tmp/quant-pgadmin-port-forward.pid ]; then
        local pid=$(cat /tmp/quant-pgadmin-port-forward.pid)
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "  ${GREEN}✅ pgAdmin: http://localhost:$PGADMIN_LOCAL_PORT${NC}"
        else
            rm -f /tmp/quant-pgadmin-port-forward.pid
        fi
    fi
    
    if [ ! -f /tmp/quant-airflow-port-forward.pid ] && [ ! -f /tmp/quant-pgadmin-port-forward.pid ]; then
        echo -e "  ${YELLOW}No active connections${NC}"
    fi
    echo ""
}

# Connection info
show_connection_info() {
    echo -e "${BLUE}📋 Production Connection Information:${NC}"
    echo ""
    echo -e "${GREEN}Production Airflow Web UI:${NC}"
    echo "  URL: http://localhost:$AIRFLOW_LOCAL_PORT"
    echo "  Username: Set via AIRFLOW_ADMIN_USERNAME secret"
    echo "  Password: Set via AIRFLOW_ADMIN_PASSWORD secret"
    echo ""
    echo -e "${GREEN}Production pgAdmin Web UI:${NC}"
    echo "  URL: http://localhost:$PGADMIN_LOCAL_PORT"
    echo "  Email: Set via PGADMIN_EMAIL secret"
    echo "  Password: Set via PGADMIN_PASSWORD secret"
    echo ""
    echo -e "${BLUE}💡 Local Development Services (if running):${NC}"
    echo "  Local Airflow: http://localhost:8080"
    echo "  Local pgAdmin: http://localhost:5050"
    echo ""
    echo -e "${GREEN}PostgreSQL Connection Setup (inside Production pgAdmin):${NC}"
    echo "  1. Right-click 'Servers' → 'Register' → 'Server'"
    echo "  2. General tab:"
    echo "     Name: Production Quant DB"
    echo "  3. Connection tab:"
    echo "     Host: postgres"
    echo "     Port: 5432"
    echo "     Database: postgres"
    echo "     Username: postgres"
    echo "     Password: [Your POSTGRES_PASSWORD secret value]"
    echo "  4. Click 'Save'"
    echo ""
    echo -e "${BLUE}💡 Local PostgreSQL (from local pgAdmin):${NC}"
    echo "  Host: localhost (or host.docker.internal)"
    echo "  Port: 5432"
    echo "  Database: postgres"
    echo "  Username: postgres"
    echo "  Password: [Your local .env POSTGRES_PASSWORD or 'postgres']"
    echo ""
}

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    stop_port_forward "airflow" "Airflow"
    stop_port_forward "pgadmin" "pgAdmin"
    exit 0
}

# Trap cleanup on script exit
trap cleanup EXIT INT TERM

# Check service status first
check_service_status

# Main loop
while true; do
    show_connections
    show_menu
    read -p "Enter your choice [1-7]: " choice
    
    case $choice in
        1)
            start_port_forward "airflow" $AIRFLOW_LOCAL_PORT "8080" "Airflow"
            echo ""
            echo -e "${GREEN}🎉 Airflow is now accessible at http://localhost:$AIRFLOW_LOCAL_PORT${NC}"
            echo -e "${BLUE}💡 Tip: Press Ctrl+C to stop all connections when done${NC}"
            echo ""
            ;;
        2)
            start_port_forward "pgadmin" $PGADMIN_LOCAL_PORT "80" "pgAdmin"
            echo ""
            echo -e "${GREEN}🎉 pgAdmin is now accessible at http://localhost:$PGADMIN_LOCAL_PORT${NC}"
            echo -e "${BLUE}💡 Tip: Press Ctrl+C to stop all connections when done${NC}"
            echo ""
            ;;
        3)
            start_port_forward "airflow" $AIRFLOW_LOCAL_PORT "8080" "Airflow"
            start_port_forward "pgadmin" $PGADMIN_LOCAL_PORT "80" "pgAdmin"
            echo ""
            echo -e "${GREEN}🎉 Both services are now accessible:${NC}"
            echo -e "  📊 Airflow: http://localhost:$AIRFLOW_LOCAL_PORT"
            echo -e "  🐘 pgAdmin: http://localhost:$PGADMIN_LOCAL_PORT"
            echo -e "${BLUE}💡 Tip: Press Ctrl+C to stop all connections when done${NC}"
            echo ""
            ;;
        4)
            check_service_status
            ;;
        5)
            stop_port_forward "airflow" "Airflow"
            stop_port_forward "pgadmin" "pgAdmin"
            echo ""
            ;;
        6)
            show_connection_info
            ;;
        7)
            echo -e "${GREEN}👋 Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid option. Please try again.${NC}"
            echo ""
            ;;
    esac
done