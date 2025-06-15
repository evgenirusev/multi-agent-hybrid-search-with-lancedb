#!/bin/bash
#
# Azure App Service Docker Deployment Script
# ------------------------------------------
# This script builds and deploys your Docker application to Azure App Service
# with proper versioning to maintain a history of deployments.
#
# Usage:
#   ./deploy.sh                    # Deploy with auto-versioning
#   ./deploy.sh -m 2               # Deploy with specific major version
#   ./deploy.sh -m 2 -n 1          # Deploy with specific major.minor version
#   ./deploy.sh --skip-build       # Skip the build step (deploy only)
#   ./deploy.sh --skip-logs        # Don't show logs after deployment
#

set -e  # Exit on any error

# Default configuration
MAJOR=1
MINOR=0
SKIP_BUILD=false
SKIP_LOGS=false
ACR_NAME="your-registry"
APP_NAME="your-app-name"
RESOURCE_GROUP="your-resource-group"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -m|--major)
      MAJOR="$2"
      shift 2
      ;;
    -n|--minor)
      MINOR="$2"
      shift 2
      ;;
    --skip-build)
      SKIP_BUILD=true
      shift
      ;;
    --skip-logs)
      SKIP_LOGS=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Auto-increment patch with each build (using timestamp)
PATCH=$(date +%Y%m%d%H%M)

# Create version tags
VERSION="${MAJOR}.${MINOR}.${PATCH}"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
TAG_LATEST="latest"
TAG_VERSION="v${VERSION}"
TAG_TIMESTAMP="${TIMESTAMP}"

echo "╔═════════════════════════════════════════════════════════════════╗"
echo "║                 AZURE APP SERVICE DEPLOYMENT                     ║"
echo "╚═════════════════════════════════════════════════════════════════╝"
echo "✓ App Service:    $APP_NAME"
echo "✓ Resource Group: $RESOURCE_GROUP"
echo "✓ ACR:            $ACR_NAME"
echo "✓ Image versions: ${TAG_LATEST}, ${TAG_VERSION}, ${TAG_TIMESTAMP}"
echo "─────────────────────────────────────────────────────────────────"

# Build the Docker image if not skipped
if [ "$SKIP_BUILD" = false ]; then
  echo "🔨 Building Docker image for linux/amd64 platform..."
  docker buildx build --platform linux/amd64 --no-cache -t your-app-name .
  
  if [ $? -ne 0 ]; then
    echo "❌ Docker build failed! Exiting."
    exit 1
  fi
else
  echo "⏩ Skipping build step as requested."
fi

# Log in to Azure Container Registry
echo "🔑 Logging in to Azure Container Registry..."
az acr login --name $ACR_NAME

if [ $? -ne 0 ]; then
  echo "❌ ACR login failed! Make sure you're logged in to Azure CLI."
  exit 1
fi

# Tag the image with multiple tags
echo "🏷️  Tagging Docker image with version tags..."
docker tag your-app-name $ACR_NAME.azurecr.io/your-app-name:${TAG_LATEST}
docker tag your-app-name $ACR_NAME.azurecr.io/your-app-name:${TAG_VERSION}
docker tag your-app-name $ACR_NAME.azurecr.io/your-app-name:${TAG_TIMESTAMP}

# Push all tagged versions to ACR
echo "⬆️  Pushing versioned images to ACR..."
docker push $ACR_NAME.azurecr.io/your-app-name:${TAG_LATEST}
docker push $ACR_NAME.azurecr.io/your-app-name:${TAG_VERSION}
docker push $ACR_NAME.azurecr.io/your-app-name:${TAG_TIMESTAMP}

# Deploy the versioned image to App Service
echo "🚀 Deploying version ${TAG_VERSION} to App Service..."
az webapp config container set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --container-image-name $ACR_NAME.azurecr.io/your-app-name:${TAG_VERSION} \
  --container-registry-url https://$ACR_NAME.azurecr.io

# Restart the App Service
echo "🔄 Restarting App Service..."
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP

# Show deployment info
echo "✅ Deployment complete!"
echo "   Image: $ACR_NAME.azurecr.io/your-app-name:${TAG_VERSION}"
echo "   App:   https://$APP_NAME.azurewebsites.net"

# Monitor the deployment logs
if [ "$SKIP_LOGS" = false ]; then
  echo "📋 Monitoring App Service logs (press Ctrl+C to exit)..."
  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP
else
  echo "⏩ Skipping log streaming as requested."
fi 