# Agents API

A containerized API service for agent support services using Azure OpenAI and LanceDB for RAG capabilities.

## Table of Contents

- [Overview](#overview)
- [Local Development](#local-development)
- [Docker Setup](#docker-setup)
- [Azure Deployment](#azure-deployment)
- [Environment Configuration](#environment-configuration)
- [Infrastructure as Code](#infrastructure-as-code)
- [Debugging and Development](#debugging-and-development)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Automated Deployment](#automated-deployment)

## Overview

This API provides AI-powered agent support using:
- FastAPI backend
- Azure OpenAI integration
- LanceDB vector database for RAG
- Docker containerization
- Azure App Service hosting

## Local Development

### Prerequisites
- Python 3.10+
- Azure OpenAI access
- LanceDB account

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/agents.git
   cd agents
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   # For production dependencies only
   pip install -r requirements.txt
   
   # For development (includes testing tools)
   pip install -r requirements.txt -r requirements-dev.txt
   ```

4. Create a `.env` file with required variables (see [Environment Configuration](#environment-configuration))

5. Run the application:
   ```bash
   python app.py
   ```

6. Access the API at http://localhost:8000

## Docker Setup

### Build Docker Image

```bash
# Build for local development
docker build -t agents .

# Build specifically for Azure (required for App Service)
docker buildx build --platform linux/amd64 -t agents .
```

### Run Locally

```bash
# Run with environment variables from .env file
docker run -p 8000:8000 --env-file .env agents
```

### Test Local Container

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test API with query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"query": "test query"}'
```

## Azure Deployment

### Prerequisites
- Azure CLI installed and logged in
- Azure subscription
- Azure Container Registry
- Azure App Service

### First-time Setup

1. Create Azure resources using the provided Bicep templates:
   ```bash
   az deployment group create \
     --resource-group WEU-RG-DEV-OPA01 \
     --template-file infra/main.bicep \
     --parameters @infra/parameters.dev.json
   ```

### Deploy Updated Code

1. Build and tag Docker image:
   ```bash
   # Build with platform flag for Azure
   docker buildx build --platform linux/amd64 -t agents .

   # Login to ACR
   az acr login --name agentregistry

   # Tag image
   docker tag agents agentregistry.azurecr.io/agents:latest

   # Push to ACR
   docker push agentregistry.azurecr.io/agents:latest
   ```

2. Restart App Service to pull new image:
   ```bash
   az webapp restart --name agents --resource-group WEU-RG-DEV-OPA01
   ```

3. Monitor deployment:
   ```bash
   az webapp log tail --name agents --resource-group WEU-RG-DEV-OPA01
   ```

### Alternative: Force Update Without Rebuilding

If you just want to trigger a redeploy of the existing image:

```bash
az webapp config set --name agents --resource-group WEU-RG-DEV-OPA01 \
  --generic-configurations '{"linuxFxVersion": "DOCKER|agentregistry.azurecr.io/agents:latest"}'
```

## Environment Configuration

Required environment variables:

```
# API Configuration
API_KEY=your-api-key

# Debug Configuration
DEBUG_MODE=true  # Set to 'true' for local development, 'false' for production

# Azure OpenAI Configuration
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_VERSION=2023-05-15
GPT4_DEPLOYMENT_NAME=gpt-4
EMBEDDING_DEPLOYMENT_NAME=text-embedding-ada-002

# LanceDB Configuration
LANCEDB_URI=az://lancedb
LANCEDB_ACCOUNT_NAME=your-storage-account
LANCEDB_ACCOUNT_KEY=your-storage-account-key
```

## Infrastructure as Code

This project includes Bicep templates for deploying all required Azure infrastructure:

- `infra/main.bicep`: Main template for App Service and container configuration
- `infra/keyVaultModule.bicep`: Module for Key Vault integration
- `infra/updateAppSettings.bicep`: Module for configuring app settings with Key Vault references
- `infra/parameters.{env}.json`: Environment-specific parameters

To deploy a new environment:

1. Create a parameter file for the environment (e.g., `parameters.qa.json`)
2. Run the deployment:
   ```bash
   az deployment group create \
     --resource-group YOUR-RG-NAME \
     --template-file infra/main.bicep \
     --parameters @infra/parameters.qa.json
   ```

## Debugging and Development

### Debug Mode

The application includes a debug mode that displays detailed information about the LLM requests, including:

- The exact prompts being sent to Azure OpenAI
- The complete Pydantic schemas used for structured outputs
- The function-calling API configuration

To enable debug mode:

#### Environment Variable

The simplest way to control debug mode is via the `DEBUG_MODE` environment variable:

```bash
# In .env file or environment configuration
DEBUG_MODE=true   # Enable debug mode
DEBUG_MODE=false  # Disable debug mode
```

This variable is automatically set to `true` for development environments and `false` for production in the Azure App Service configuration.

#### Command Line

When running from the command line:

```bash
# Using the debug flag
python -m agents.main --debug "What are my employment benefits?"

# Or with shorthand flag
python -m agents.main -d "What are my employment benefits?"
```

#### API Requests

When making API requests, include the `debug` parameter:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"query": "What are my employment benefits?", "debug": true}'
```

#### Programmatic Usage

When using the `AgentSupportCrew` class directly:

```python
from agents.crews.agent_support_agents import AgentSupportCrew

# Initialize with debug enabled
crew = AgentSupportCrew(debug_enabled=True)

# Process a query
result = await crew.process_query("What are my employment benefits?")
```

The debug output provides valuable insights for development, troubleshooting, and understanding how the LLM's function-calling capabilities work with Pydantic models.

## Monitoring and Maintenance

### Health Checks

Azure health check is configured to monitor the `/health` endpoint.

### Scaling

For production environments, configure multiple instances:

```bash
# Set to multiple instances
az appservice plan update --resource-group WEU-RG-DEV-OPA01 --name agent-app-plan --number-of-workers 2
```

### Logs

View application logs:

```bash
# Stream logs in real-time
az webapp log tail --name agents --resource-group WEU-RG-DEV-OPA01
```

### Diagnostics

Use the `/debug` endpoint (requires API key) to view system information and test connections to Azure OpenAI and LanceDB.

```bash
curl -X GET "https://agents.azurewebsites.net/debug" \
  -H "X-API-Key: your-api-key"
```

## Automated Deployment

This project includes a comprehensive deployment script (`deploy.sh`) that automates the entire process of building, tagging, pushing, and deploying Docker images to Azure App Service with proper versioning.