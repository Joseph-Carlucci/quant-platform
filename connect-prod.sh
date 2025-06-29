#!/bin/bash

# Simple Production Port-Forward Script
# Connects to production Airflow and PostgreSQL

set -e

echo "🔗 Connecting to Production Services..."
echo ""

# Check if kubectl works
if ! kubectl get pods -n quant-platform &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    echo "Make sure you're connected: aws eks update-kubeconfig --region us-east-1 --name quant-platform"
    exit 1
fi

# Kill any existing port-forwards on these ports
echo "🧹 Cleaning up existing port-forwards..."
lsof -ti:8081 | xargs kill -9 2>/dev/null || true
lsof -ti:15432 | xargs kill -9 2>/dev/null || true
sleep 2

# Start port-forwards in background
echo "🚀 Starting port-forwards..."
nohup kubectl port-forward -n quant-platform service/airflow 8081:8080 > /tmp/airflow-port-forward.log 2>&1 &
nohup kubectl port-forward -n quant-platform service/postgres 15432:5432 > /tmp/postgres-port-forward.log 2>&1 &

# Wait a moment for connections to establish
sleep 3

echo ""
echo "✅ Production services connected!"
echo ""
echo "📊 Airflow: http://localhost:8081"
echo "🐘 PostgreSQL: localhost:15432 (use DBeaver, TablePlus, etc.)"
echo ""
echo "💡 Use your GitHub secret credentials to login"
echo "💡 Port-forwards are running in background"  
echo "💡 Run './disconnect-prod.sh' to stop them"
echo ""