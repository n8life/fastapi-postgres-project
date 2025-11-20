# Kubernetes Deployment with File-Based Secrets

This directory contains Kubernetes manifests for deploying the FastAPI PostgreSQL application with secure file-based secret management.

## Security Features

### File-Based Secrets
- PostgreSQL passwords are stored as Kubernetes Secrets and mounted as read-only files
- No secrets in environment variables or container images
- Secrets have restricted file permissions (0400 - read-only for owner)
- Clear separation between secrets and configuration

### Secret Management
- Secrets are mounted at `/var/secrets/postgres/password`
- Application reads password from file using `POSTGRES_PASSWORD_FILE` environment variable
- Maintains backward compatibility with environment variable fallbacks for development

## Quick Start

### 1. Create Namespace
```bash
kubectl create namespace fastapi-postgres
```

### 2. Set up PostgreSQL Secret
Use the provided script for easy secret management:

```bash
# Create secret with interactive password input
./setup-secrets.sh create

# Or create secret with auto-generated password
./setup-secrets.sh create-random

# View secret information (password hidden)
./setup-secrets.sh show
```

### 3. Deploy the Application
```bash
# Apply all Kubernetes manifests
kubectl apply -f .

# Check deployment status
kubectl get pods -n fastapi-postgres
kubectl get services -n fastapi-postgres
```

## Files Overview

### Core Deployments
- `postgres-deployment.yaml` - PostgreSQL database with file-based secrets
- `fastapi-deployment.yaml` - FastAPI application with file-based secrets
- `services.yaml` - Kubernetes services for internal communication

### Secret Management
- `postgres-secret.yaml` - Secret template (update with actual values)
- `setup-secrets.sh` - Script for managing secrets

### Security & Storage
- `service-accounts.yaml` - Service accounts with minimal permissions
- `network-policies.yaml` - Network isolation policies
- `postgres-storage.yaml` - Persistent storage for PostgreSQL

### Infrastructure
- `namespace.yaml` - Dedicated namespace for the application

## Secret Management Commands

The `setup-secrets.sh` script provides these commands:

```bash
# Create/update secret interactively
./setup-secrets.sh create

# Generate and create random password
./setup-secrets.sh create-random

# Show secret information (password masked)
./setup-secrets.sh show

# Delete secret
./setup-secrets.sh delete

# Show help
./setup-secrets.sh help
```

## Environment Variables

The application supports these environment variables for database configuration:

### File-Based Configuration (Recommended for Production)
- `POSTGRES_PASSWORD_FILE` - Path to file containing PostgreSQL password
- `DB_HOST` - PostgreSQL host (default: localhost)
- `DB_PORT` - PostgreSQL port (default: 5432)
- `DB_NAME` - Database name (default: testdb)
- `DB_USER` - Database username (default: postgres)

### Fallback Configuration (Development)
- `DATABASE_URL` - Complete database connection URL
- `POSTGRES_PASSWORD` - PostgreSQL password as environment variable

## Security Best Practices

### Secret Rotation
1. Generate new password: `./setup-secrets.sh create-random`
2. Update PostgreSQL: Connect and change password
3. Restart deployments: `kubectl rollout restart deployment -n fastapi-postgres`

### Access Control
- Secrets mounted with 0400 permissions (read-only for owner)
- Service accounts with minimal required permissions
- Network policies restrict inter-pod communication
- Read-only root filesystem for application containers

### Monitoring
Monitor secret access and rotation:
```bash
# Check secret age
kubectl get secret postgres-secret -n fastapi-postgres -o jsonpath='{.metadata.creationTimestamp}'

# View secret events
kubectl get events -n fastapi-postgres --field-selector involvedObject.name=postgres-secret
```

## Troubleshooting

### Common Issues

1. **Secret Not Found**
   ```bash
   # Check if secret exists
   kubectl get secret postgres-secret -n fastapi-postgres
   
   # Create if missing
   ./setup-secrets.sh create
   ```

2. **Permission Denied Reading Secret File**
   ```bash
   # Check pod logs
   kubectl logs deployment/fastapi-app -n fastapi-postgres
   
   # Verify mount and permissions
   kubectl exec -it deployment/fastapi-app -n fastapi-postgres -- ls -la /var/secrets/postgres/
   ```

3. **Database Connection Issues**
   ```bash
   # Check database connectivity from app pod
   kubectl exec -it deployment/fastapi-app -n fastapi-postgres -- nc -zv postgres-service 5432
   
   # Check PostgreSQL logs
   kubectl logs deployment/postgres -n fastapi-postgres
   ```

### Debug Commands
```bash
# View all resources
kubectl get all -n fastapi-postgres

# Check pod events
kubectl describe pod -l app=fastapi-app -n fastapi-postgres

# Follow application logs
kubectl logs -f deployment/fastapi-app -n fastapi-postgres
```

## Production Considerations

1. **Secret Management**: Consider using external secret management systems like HashiCorp Vault or AWS Secrets Manager
2. **Backup**: Ensure PostgreSQL data is properly backed up
3. **Monitoring**: Set up monitoring and alerting for the application
4. **Resource Limits**: Adjust CPU and memory limits based on your workload
5. **High Availability**: Consider running multiple PostgreSQL replicas for production