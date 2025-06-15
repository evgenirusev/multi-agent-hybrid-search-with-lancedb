# Deployment to Azure App Service

This guide provides detailed instructions for deploying the Agents API to Azure App Service.

## Prerequisites
- Visual Studio Code
- Azure App Service extension installed
- Azure subscription

## Deployment Steps using VS Code

1. **Open the project in VS Code**

2. **Sign in to Azure**
   - Open the Azure extension in VS Code
   - Click "Sign in to Azure"
   - Follow the authentication prompts

3. **Deploy to Azure App Service**
   - Right-click on the project folder in VS Code Explorer
   - Select "Deploy to Web App..."
   - Select your subscription
   - Create a new Web App or select an existing one
   - If creating new:
     - Enter a globally unique name
     - Select Python 3.10 runtime
     - Choose the appropriate region
   - Confirm deployment

4. **Configure Environment Variables**
   - In Azure Portal, go to your App Service
   - Navigate to Settings > Configuration
   - Add the following Application settings:
     - `API_KEY` - Your chosen API key for securing endpoints
     - `AZURE_OPENAI_KEY` - Your Azure OpenAI key
     - `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint URL
     - `AZURE_OPENAI_VERSION` - Azure OpenAI API version (e.g., "2023-05-15")
     - `GPT4_DEPLOYMENT_NAME` - Your GPT-4 deployment name
     - `EMBEDDING_DEPLOYMENT_NAME` - Your embedding model deployment name
     - `LANCEDB_URI` - Your LanceDB URI if using remote storage
     - `LANCEDB_ACCOUNT_NAME` - Azure storage account name if using Azure Blob Storage
     - `LANCEDB_ACCOUNT_KEY` - Azure storage account key if using Azure Blob Storage
     - `WEBSITES_PORT` - Set to 8000

5. **Configure Startup Command**
   - In Azure Portal, go to Settings > Configuration > General settings
   - Set the Startup Command to: `gunicorn --bind=0.0.0.0 --timeout 600 --workers 4 app:app`

6. **Test the Deployment**
   ```bash
   # Health check
   curl https://your-app-name.azurewebsites.net/health
   
   # Query API
   curl -X POST https://your-app-name.azurewebsites.net/query \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your_api_key_here" \
     -d '{"query": "What are my employment options?"}'
   ```

## Troubleshooting

If deployment issues occur:

1. **Check Logs**
   - In Azure Portal, go to App Service > Monitoring > Log stream
   - Look for error messages that might indicate configuration or startup issues

2. **Access Kudu Console**
   - Visit: `https://your-app-name.scm.azurewebsites.net/DebugConsole`
   - Navigate to site/wwwroot to check file structure
   - Verify all files were properly deployed

3. **Check Python Version**
   - In Kudu Console, run: `python --version`
   - Ensure it matches your required version (3.10)

4. **Check Dependencies**
   - In Kudu Console, run: `pip list`
   - Verify all dependencies were installed correctly

5. **Restart App Service**
   - In Azure Portal, restart the app service after making configuration changes

6. **Review Application Insights**
   - If enabled, check Application Insights for detailed monitoring and error logs

## Scaling Considerations

For production deployments, consider these scaling options:

1. **App Service Plan**
   - Choose a plan with appropriate resources for your workload
   - P2v3 or higher recommended for AI workloads

2. **Autoscaling**
   - Configure autoscaling based on CPU usage or request queue length
   - Set minimum and maximum instance counts based on expected traffic

3. **Azure Front Door**
   - Consider adding Azure Front Door for global distribution and caching

4. **Application Insights**
   - Enable Application Insights for monitoring and performance tracking

## Security Considerations

1. **Network Security**
   - Consider restricting access with VNet integration
   - Use Private Endpoints for connections to Azure OpenAI and other services

2. **Authentication**
   - Consider adding additional authentication methods for production
   - Implement rate limiting for API endpoints

3. **Key Rotation**
   - Implement a process for rotating the API_KEY and other secrets regularly

For more information, see [Azure App Service documentation](https://docs.microsoft.com/en-us/azure/app-service/). 