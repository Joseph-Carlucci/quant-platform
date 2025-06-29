#!/bin/bash

# Quantitative Research Platform - Production Restart Script
# Use this after updating secrets or when you need to restart services

set -e

echo "🔄 Restarting Quantitative Research Platform..."
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace quant-platform &> /dev/null; then
    echo "❌ Namespace 'quant-platform' not found. Please deploy first with ./deploy.sh"
    exit 1
fi

echo "📋 Restart Order:"
echo "1. PostgreSQL (database)"
echo "2. Redis (cache)"  
echo "3. Airflow Scheduler"
echo "4. Airflow Webserver"
echo ""

read -p "🚨 This will cause brief downtime. Continue? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restart cancelled."
    exit 1
fi

echo ""
echo "🔄 Starting restart sequence..."

# 1. Restart PostgreSQL first (other services depend on it)
echo "🗄️  Restarting PostgreSQL..."
kubectl rollout restart deployment/postgres -n quant-platform
kubectl rollout status deployment/postgres -n quant-platform --timeout=300s

# 2. Restart Redis
echo "🔴 Restarting Redis..."
kubectl rollout restart deployment/redis -n quant-platform
kubectl rollout status deployment/redis -n quant-platform --timeout=300s

# 3. Restart Airflow Scheduler (before webserver)
echo "📅 Restarting Airflow Scheduler..."
kubectl rollout restart deployment/airflow-scheduler -n quant-platform
kubectl rollout status deployment/airflow-scheduler -n quant-platform --timeout=600s

# 4. Restart Airflow Webserver
echo "🖥️  Restarting Airflow Webserver..."
kubectl rollout restart deployment/airflow-webserver -n quant-platform
kubectl rollout status deployment/airflow-webserver -n quant-platform --timeout=600s

echo ""
echo "✅ All services restarted successfully!"
echo ""

# Show status
echo "📊 Current Status:"
kubectl get pods -n quant-platform -o wide

echo ""
echo "🌐 Access Information:"
echo "   Airflow UI: kubectl port-forward -n quant-platform service/airflow-webserver 8080:8080"
echo "   Then visit: http://localhost:8080"
echo ""
echo "🔧 Useful Commands:"
echo "   Check logs: kubectl logs -f deployment/airflow-scheduler -n quant-platform"
echo "   View all pods: kubectl get pods -n quant-platform"
echo ""
echo "🎉 Platform restart complete!"