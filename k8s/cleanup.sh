#!/bin/bash

# FastAPI PostgreSQL Kubernetes Cleanup Script
set -e

echo "🧹 Starting cleanup of FastAPI PostgreSQL Kubernetes deployment..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Delete all resources in the namespace
echo "🗑️  Deleting Kubernetes resources..."
kubectl delete -f services.yaml || true
kubectl delete -f fastapi-deployment.yaml || true
kubectl delete -f postgres-deployment.yaml || true
kubectl delete -f postgres-storage.yaml || true

# Delete namespace (this will also delete any remaining resources)
kubectl delete -f namespace.yaml || true

# Optional: Remove Docker image
read -p "Do you want to remove the Docker image 'fastapi-postgres-app:latest'? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker rmi fastapi-postgres-app:latest || true
    echo "🗑️  Docker image removed"
fi

echo "✅ Cleanup completed successfully!"