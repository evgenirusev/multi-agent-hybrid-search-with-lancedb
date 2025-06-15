@description('Name of the Web App')
param webAppName string

@description('Name of the Key Vault')
param keyVaultName string

@description('Name of the API Key secret in Key Vault')
param apiKeySecretName string

@description('Name of the OpenAI Key secret in Key Vault')
param openAiKeySecretName string

@description('Name of the LanceDB Key secret in Key Vault')
param lanceDbKeySecretName string

// Get current web app config
resource webApp 'Microsoft.Web/sites@2022-03-01' existing = {
  name: webAppName
}

// Get current app settings
var currentAppSettings = list('${webApp.id}/config/appsettings', '2022-03-01').properties

// Update app settings with Key Vault references
resource appSettings 'Microsoft.Web/sites/config@2022-03-01' = {
  name: 'appsettings'
  parent: webApp
  properties: union(currentAppSettings, {
    API_KEY: '@Microsoft.KeyVault(SecretUri=https://${keyVaultName}.vault.azure.net/secrets/${apiKeySecretName}/)'
    AZURE_OPENAI_KEY: '@Microsoft.KeyVault(SecretUri=https://${keyVaultName}.vault.azure.net/secrets/${openAiKeySecretName}/)'
    LANCEDB_ACCOUNT_KEY: '@Microsoft.KeyVault(SecretUri=https://${keyVaultName}.vault.azure.net/secrets/${lanceDbKeySecretName}/)'
  })
}
