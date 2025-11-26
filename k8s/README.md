# Kubernetes Deployment Guide

This guide provides instructions for deploying the FastAPI PostgreSQL application to Kubernetes.

## Prerequisites

- kubectl configured and connected to your cluster
- Docker installed (for building images)
- Access to push images to your cluster (or use local images)

## Deployment Steps

### 1. Set Environment Variables

Set the required environment variables before deployment. **Do not commit these values to git.**

```bash
# PostgreSQL credentials
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="your-secure-password"
export POSTGRES_DB="testdb"

# API credentials
export API_KEY="your-secure-api-key"
```

### 2. Build and Push the Docker Image

Build and push the FastAPI application image to a registry accessible by your cluster:

```bash
# Build the image
docker build -t fastapi-postgres:latest .

# For minikube: load image into minikube
minikube image load fastapi-postgres:latest

# For kind: load image into kind
kind load docker-image fastapi-postgres:latest

# For remote clusters: push to a container registry
# Option 1: GitHub Container Registry
docker tag fastapi-postgres:latest ghcr.io/YOUR_ORG/fastapi-postgres:latest
docker push ghcr.io/YOUR_ORG/fastapi-postgres:latest

# Option 2: Docker Hub
docker tag fastapi-postgres:latest YOUR_USER/fastapi-postgres:latest
docker push YOUR_USER/fastapi-postgres:latest

# Then update k8s/api-deployment.yaml to use your registry image
```

### 3. Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 4. Create Secrets

Create secrets from environment variables (do not use the secrets.yaml file directly):

```bash
# Create PostgreSQL secret
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=$POSTGRES_USER \
  --from-literal=POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
  --from-literal=POSTGRES_DB=$POSTGRES_DB \
  -n fastapi-postgres

# Create API secret
kubectl create secret generic api-secret \
  --from-literal=API_KEY=$API_KEY \
  -n fastapi-postgres
```

### 5. Apply ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

### 6. Create Storage

```bash
kubectl apply -f k8s/storage.yaml
```

### 7. Deploy PostgreSQL

```bash
kubectl apply -f k8s/postgres-deployment.yaml
```

Wait for PostgreSQL to be ready:

```bash
kubectl wait --for=condition=ready pod -l app=postgres -n fastapi-postgres --timeout=120s
```

### 8. Deploy FastAPI Application

```bash
kubectl apply -f k8s/api-deployment.yaml
```

Wait for the API to be ready:

```bash
kubectl wait --for=condition=ready pod -l app=fastapi -n fastapi-postgres --timeout=120s
```

### 9. Apply Network Policies

```bash
kubectl apply -f k8s/network-policies.yaml
```

## Verification

### Check Pod Status

```bash
kubectl get pods -n fastapi-postgres
```

### Check Services

```bash
kubectl get services -n fastapi-postgres
```

### Test the API

The FastAPI service is exposed via NodePort on port 30080.

```bash
# Get node IP (for minikube)
# NODE_IP=$(minikube ip)

# Get node IP (for other clusters)
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Test health endpoint
curl http://$NODE_IP:30080/health

# Test with API key
curl -H "X-API-Key: $API_KEY" http://$NODE_IP:30080/
```

### View Logs

```bash
# FastAPI logs
kubectl logs -l app=fastapi -n fastapi-postgres

# PostgreSQL logs
kubectl logs -l app=postgres -n fastapi-postgres
```

## Quick Deploy Script

For convenience, you can deploy everything with this script:

```bash
#!/bin/bash
set -e

# Ensure environment variables are set
if [ -z "$POSTGRES_PASSWORD" ] || [ -z "$API_KEY" ]; then
  echo "Error: POSTGRES_PASSWORD and API_KEY must be set"
  exit 1
fi

# Set defaults
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_DB=${POSTGRES_DB:-testdb}

# Build image
docker build -t fastapi-postgres:latest .

# Apply namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=$POSTGRES_USER \
  --from-literal=POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
  --from-literal=POSTGRES_DB=$POSTGRES_DB \
  -n fastapi-postgres --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic api-secret \
  --from-literal=API_KEY=$API_KEY \
  -n fastapi-postgres --dry-run=client -o yaml | kubectl apply -f -

# Apply resources
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/storage.yaml
kubectl apply -f k8s/postgres-deployment.yaml

# Wait for postgres
kubectl wait --for=condition=ready pod -l app=postgres -n fastapi-postgres --timeout=120s

# Deploy API
kubectl apply -f k8s/api-deployment.yaml

# Wait for API
kubectl wait --for=condition=ready pod -l app=fastapi -n fastapi-postgres --timeout=120s

# Apply network policies
kubectl apply -f k8s/network-policies.yaml

echo "Deployment complete!"
kubectl get pods -n fastapi-postgres
```

## Load Testing with Locust

Deploy Locust for distributed load testing of the API.

### Deploy Locust

```bash
# Deploy Locust master and workers
kubectl apply -f k8s/locust-deployment.yaml

# Verify deployment
kubectl get pods -n fastapi-postgres -l app=locust

# Expected output:
# locust-master-xxx   1/1     Running
# locust-worker-xxx   1/1     Running  (x2)
```

### Access Locust Web UI

The Locust web UI is exposed via NodePort on port 30089.

```bash
# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Access web UI
echo "Locust UI: http://$NODE_IP:30089"

# Or use port-forward for local access
kubectl port-forward -n fastapi-postgres svc/locust-master 8089:8089
# Then open http://localhost:8089
```

### Configure and Run Tests

1. Open the Locust web UI
2. Set test parameters:
   - **Number of users**: e.g., 100
   - **Spawn rate**: e.g., 10 users/second
   - **Host**: Pre-configured to `http://fastapi:8000`
3. Click "Start swarming"
4. Monitor results in real-time

### Scale Locust Workers

```bash
# Scale to more workers for higher load
kubectl scale deployment locust-worker -n fastapi-postgres --replicas=5

# Verify workers in Locust UI
```

### Enable API Auto-scaling (Optional)

Test how the API scales under load:

```bash
# Deploy Horizontal Pod Autoscaler
kubectl apply -f k8s/hpa.yaml

# Monitor HPA status
kubectl get hpa -n fastapi-postgres

# Watch pods scale
kubectl get pods -n fastapi-postgres -l app=fastapi -w
```

The HPA will scale the API from 1-5 replicas based on CPU usage (target: 70%).

### Stop Load Test

```bash
# Remove Locust deployment
kubectl delete -f k8s/locust-deployment.yaml

# Remove HPA (if deployed)
kubectl delete -f k8s/hpa.yaml
```

## Cleanup

To remove all resources:

```bash
kubectl delete namespace fastapi-postgres
```

## Troubleshooting

### Pod not starting

Check pod events:

```bash
kubectl describe pod -l app=fastapi -n fastapi-postgres
kubectl describe pod -l app=postgres -n fastapi-postgres
```

### Database connection issues

Verify PostgreSQL is running and accessible:

```bash
kubectl exec -it $(kubectl get pod -l app=postgres -n fastapi-postgres -o jsonpath='{.items[0].metadata.name}') -n fastapi-postgres -- pg_isready
```

### Image pull errors

For local development, ensure `imagePullPolicy: Never` is set and the image is loaded into your cluster.
