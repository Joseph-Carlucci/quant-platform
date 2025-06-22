#!/bin/bash

# Quantitative Research Platform - Kubernetes Deployment Script
# This script deploys your platform to EKS or any Kubernetes cluster

set -e

echo "🚀 Deploying Quantitative Research Platform to Kubernetes..."
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first:"
    echo "   https://kubernetes.io/docs/tasks/tools/install-kubectl/"
    exit 1
fi

# Check if eksctl is available
if ! command -v eksctl &> /dev/null; then
    echo "⚠️  eksctl not found. Installing eksctl..."
    curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
    sudo mv /tmp/eksctl /usr/local/bin
fi

echo "📋 Deployment Steps:"
echo "1. Create EKS cluster (15-20 minutes)"
echo "2. Deploy all services (5-10 minutes)"  
echo "3. Get access URLs"
echo ""

# Step 1: Create EKS cluster
echo "📦 Creating EKS cluster..."
echo "⏳ This will take 15-20 minutes. Perfect time for coffee! ☕"
eksctl create cluster \
  --name quant-platform \
  --region us-east-1 \
  --nodes 2 \
  --node-type t3.medium \
  --managed

echo "✅ EKS cluster created successfully!"
echo ""

# Step 2: Create namespace
echo "🏗️  Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Step 3: Apply secrets and config
echo "🔐 Setting up secrets and configuration..."
kubectl apply -f k8s/secrets.yaml

# Step 4: Create configmaps from local files
echo "📋 Creating database init scripts..."
kubectl create configmap db-init-scripts --from-file=db-init/ -n quant-platform

echo "📊 Creating Airflow DAGs..."
kubectl create configmap airflow-dags --from-file=dags/ -n quant-platform

# Step 5: Deploy services in order
echo "🗄️  Deploying PostgreSQL..."
kubectl apply -f k8s/postgres.yaml

echo "🔴 Deploying Redis..."
kubectl apply -f k8s/redis.yaml

echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n quant-platform

echo "🌊 Deploying Airflow..."
kubectl apply -f k8s/airflow.yaml

echo "🐘 Deploying pgAdmin..."
kubectl apply -f k8s/pgadmin.yaml

echo "⏳ Waiting for all services to be ready..."
kubectl wait --for=condition=available --timeout=600s deployment/airflow -n quant-platform
kubectl wait --for=condition=available --timeout=300s deployment/pgadmin -n quant-platform

echo ""
echo "✅ Deployment complete!"
echo ""

# Get external access information
echo "🌐 Getting access URLs..."
echo "⏳ Waiting for LoadBalancers to get external IPs..."
sleep 30

AIRFLOW_URL=$(kubectl get service airflow -n quant-platform -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
PGADMIN_URL=$(kubectl get service pgadmin -n quant-platform -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo ""
echo "🎉 Your Quantitative Research Platform is LIVE!"
echo ""
echo "📊 Airflow UI: http://${AIRFLOW_URL}:8080"
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo "🐘 pgAdmin: http://${PGADMIN_URL}:5050"  
echo "   Email: admin@admin.com"
echo "   Password: admin"
echo ""

echo "🔧 Useful commands:"
echo "   View all pods: kubectl get pods -n quant-platform"
echo "   View logs: kubectl logs -f deployment/airflow -n quant-platform"
echo "   Scale Airflow: kubectl scale deployment airflow --replicas=2 -n quant-platform"
echo "   Update DAGs: kubectl create configmap airflow-dags --from-file=dags/ -n quant-platform --dry-run=client -o yaml | kubectl apply -f -"
echo ""
echo "🧹 To cleanup everything: eksctl delete cluster --name quant-platform --region us-east-1"
echo ""
echo "🚀 Ready to start your quantitative research journey!" 