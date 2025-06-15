@description('Environment name (dev, qa, stg, prod)')
param environmentName string = 'dev'

@description('Azure region for deployment')
param location string = resourceGroup().location

@description('Base name for the application')
param appName string = 'agents'

@description('Existing Container Registry name')
param containerRegistryName string

@description('Resource group containing the Container Registry')
param containerRegistryResourceGroup string

@description('Existing Key Vault name for this environment')
param keyVaultName string

@description('Resource group containing the Key Vault')
param keyVaultResourceGroup string

@description('Azure OpenAI endpoint')
param openAiEndpoint string

@description('Azure OpenAI API version')
param openAiVersion string = '2023-05-15'

@description('GPT-4 deployment name')
param gpt4DeploymentName string = 'gpt-4'

@description('Embedding model deployment name')
param embeddingDeploymentName string = 'text-embedding-ada-002'

@description('LanceDB URI')
param lanceDbUri string = 'az://lancedb'

@description('LanceDB storage account name')
param lanceDbAccountName string

@description('API Key for authentication (will be stored in Key Vault)')
@secure()
param apiKey string

@description('Azure OpenAI API key (will be stored in Key Vault)')
@secure()
param openAiKey string

@description('LanceDB storage account key (will be stored in Key Vault)')
@secure()
param lanceDbAccountKey string

// Local variables
var envSuffix = environmentName == 'prod' ? '' : '-${environmentName}'
var isProduction = environmentName == 'prod' || environmentName == 'stg'
var appServicePlanSku = isProduction ? 'P1V2' : 'B1'
var fullAppName = '${appName}${envSuffix}'

// Reference existing Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2021-12-01-preview' existing = {
  name: containerRegistryName
  scope: resourceGroup(containerRegistryResourceGroup)
}

// Reference existing Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' existing = {
  name: keyVaultName
  scope: resourceGroup(keyVaultResourceGroup)
}

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${appName}-plan${envSuffix}'
  location: location
  sku: {
    name: appServicePlanSku
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// Web App for Container
resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: fullAppName
  location: location
  kind: 'app,linux,container'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${containerRegistry.properties.loginServer}/${appName}:latest'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      healthCheckPath: '/health'
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_URL'
          value: 'https://${containerRegistry.properties.loginServer}'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_USERNAME'
          value: containerRegistry.listCredentials().username
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_PASSWORD'
          value: containerRegistry.listCredentials().passwords[0].value
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: openAiEndpoint
        }
        {
          name: 'AZURE_OPENAI_VERSION'
          value: openAiVersion
        }
        {
          name: 'GPT4_DEPLOYMENT_NAME'
          value: gpt4DeploymentName
        }
        {
          name: 'EMBEDDING_DEPLOYMENT_NAME'
          value: embeddingDeploymentName
        }
        {
          name: 'DEBUG_MODE'
          value: isProduction ? 'false' : 'true'
        }
        {
          name: 'LANCEDB_URI'
          value: lanceDbUri
        }
        {
          name: 'LANCEDB_ACCOUNT_NAME'
          value: lanceDbAccountName
        }
      ]
    }
  }
}

// Handle Key Vault operations
module keyVaultOps 'keyVaultModule.bicep' = {
  name: 'keyVaultOperations'
  scope: resourceGroup(keyVaultResourceGroup)
  params: {
    keyVaultName: keyVaultName
    apiKey: apiKey
    openAiKey: openAiKey
    lanceDbAccountKey: lanceDbAccountKey
    appName: appName
    envSuffix: envSuffix
    webAppPrincipalId: webApp.identity.principalId
  }
}

// Outputs
output appUrl string = 'https://${webApp.properties.defaultHostName}'
output containerRegistryUrl string = containerRegistry.properties.loginServer

// Add this after the keyVaultOps module
module updateAppSettings 'updateAppSettings.bicep' = {
  name: 'updateAppSettings'
  params: {
    webAppName: webApp.name
    keyVaultName: keyVaultName
    apiKeySecretName: keyVaultOps.outputs.apiKeySecretName
    openAiKeySecretName: keyVaultOps.outputs.openAiKeySecretName
    lanceDbKeySecretName: keyVaultOps.outputs.lanceDbKeySecretName
  }
  dependsOn: [
    keyVaultOps
  ]
}
