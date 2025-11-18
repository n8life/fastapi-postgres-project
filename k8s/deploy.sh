#!/bin/bash

# FastAPI PostgreSQL Kubernetes Deployment Script
set -e

echo "🚀 Starting FastAPI PostgreSQL Kubernetes deployment..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Build the Docker image first
echo "📦 Building Docker image..."
docker build -t fastapi-postgres-app:latest ..

# Apply Kubernetes manifests in order
echo "🔧 Applying Kubernetes manifests..."

# Create namespace first
kubectl apply -f namespace.yaml

# Apply storage
kubectl apply -f postgres-storage.yaml

# Apply deployments
kubectl apply -f postgres-deployment.yaml
kubectl apply -f fastapi-deployment.yaml

# Apply services
kubectl apply -f services.yaml

echo "✅ Deployment started successfully!"
echo "📊 Checking deployment status..."

# Wait for deployments to be ready
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n fastapi-postgres
kubectl wait --for=condition=available --timeout=300s deployment/fastapi-app -n fastapi-postgres

echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
kubectl get pods -n fastapi-postgres
echo ""
kubectl get services -n fastapi-postgres
echo ""

# Get the service URL
echo "🌐 Access Information:"
if kubectl get service fastapi-service -n fastapi-postgres -o jsonpath='{.status.loadBalancer.ingress[0].ip}' &> /dev/null; then
    EXTERNAL_IP=$(kubectl get service fastapi-service -n fastapi-postgres -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    echo "External IP: http://$EXTERNAL_IP"
else
    echo "Using port-forward to access the application:"
    echo "Run: kubectl port-forward svc/fastapi-service 8000:80 -n fastapi-postgres"
    echo "Then access: http://localhost:8000"
fi