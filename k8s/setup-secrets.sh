#!/bin/bash

# Setup script for managing PostgreSQL secrets in Kubernetes
set -e

NAMESPACE="fastapi-postgres"
SECRET_NAME="postgres-secret"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}PostgreSQL Kubernetes Secret Management${NC}"
echo "========================================"

# Function to create or update secret
create_secret() {
    local password="$1"
    local username="${2:-postgres}"
    
    echo -e "${YELLOW}Creating/updating secret ${SECRET_NAME} in namespace ${NAMESPACE}...${NC}"
    
    # Delete existing secret if it exists
    kubectl delete secret ${SECRET_NAME} -n ${NAMESPACE} --ignore-not-found=true
    
    # Create new secret
    kubectl create secret generic ${SECRET_NAME} \
        --from-literal=username="${username}" \
        --from-literal=password="${password}" \
        -n ${NAMESPACE}
    
    echo -e "${GREEN}Secret created successfully!${NC}"
}

# Function to check if namespace exists
check_namespace() {
    if ! kubectl get namespace ${NAMESPACE} &> /dev/null; then
        echo -e "${RED}Error: Namespace ${NAMESPACE} does not exist!${NC}"
        echo "Please create it first with: kubectl create namespace ${NAMESPACE}"
        exit 1
    fi
}

# Function to display current secret (masked)
show_secret() {
    echo -e "${YELLOW}Current secret information:${NC}"
    if kubectl get secret ${SECRET_NAME} -n ${NAMESPACE} &> /dev/null; then
        echo "Secret exists: ${SECRET_NAME}"
        echo "Keys available:"
        kubectl get secret ${SECRET_NAME} -n ${NAMESPACE} -o jsonpath='{.data}' | jq -r 'keys[]' 2>/dev/null || echo "  - username, password"
        echo "Created: $(kubectl get secret ${SECRET_NAME} -n ${NAMESPACE} -o jsonpath='{.metadata.creationTimestamp}')"
    else
        echo -e "${RED}Secret ${SECRET_NAME} does not exist in namespace ${NAMESPACE}${NC}"
    fi
}

# Function to get password from user input
get_password() {
    echo -e "${YELLOW}Enter the PostgreSQL password (input will be hidden):${NC}"
    read -s password
    echo
    
    if [ -z "$password" ]; then
        echo -e "${RED}Error: Password cannot be empty!${NC}"
        exit 1
    fi
    
    echo "$password"
}

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Main script logic
case "${1:-}" in
    "create")
        check_namespace
        if [ -n "${2:-}" ]; then
            # Password provided as argument (not recommended for production)
            create_secret "$2"
        else
            # Interactive password input
            password=$(get_password)
            create_secret "$password"
        fi
        ;;
    "create-random")
        check_namespace
        password=$(generate_password)
        echo -e "${YELLOW}Generated random password${NC}"
        create_secret "$password"
        echo -e "${GREEN}Random password created. Please save it securely!${NC}"
        ;;
    "show")
        show_secret
        ;;
    "delete")
        echo -e "${YELLOW}Deleting secret ${SECRET_NAME} in namespace ${NAMESPACE}...${NC}"
        kubectl delete secret ${SECRET_NAME} -n ${NAMESPACE}
        echo -e "${GREEN}Secret deleted successfully!${NC}"
        ;;
    "help"|*)
        echo "Usage: $0 {create|create-random|show|delete|help}"
        echo ""
        echo "Commands:"
        echo "  create        - Create/update secret with interactive password input"
        echo "  create-random - Create/update secret with auto-generated password"
        echo "  show          - Display current secret information (password hidden)"
        echo "  delete        - Delete the secret"
        echo "  help          - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 create           # Interactive password input"
        echo "  $0 create-random    # Generate random password"
        echo "  $0 show             # Show secret info"
        echo "  $0 delete           # Delete secret"
        ;;
esac