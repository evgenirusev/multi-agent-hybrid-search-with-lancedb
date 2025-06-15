// keyVaultModule.bicep
param keyVaultName string
param apiKey string
param openAiKey string
param lanceDbAccountKey string
param appName string
param envSuffix string
param webAppPrincipalId string

resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' existing = {
  name: keyVaultName
}

// Key Vault Secrets
resource apiKeySecret 'Microsoft.KeyVault/vaults/secrets@2022-07-01' = {
  parent: keyVault
  name: '${appName}-api-key${envSuffix}'
  properties: {
    value: apiKey
  }
}

resource openAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2022-07-01' = {
  parent: keyVault
  name: '${appName}-openai-key${envSuffix}'
  properties: {
    value: openAiKey
  }
}

resource lanceDbKeySecret 'Microsoft.KeyVault/vaults/secrets@2022-07-01' = {
  parent: keyVault
  name: '${appName}-lancedb-key${envSuffix}'
  properties: {
    value: lanceDbAccountKey
  }
}

// Grant the Web App access to Key Vault
resource keyVaultAccessPolicy 'Microsoft.KeyVault/vaults/accessPolicies@2022-07-01' = {
  name: 'add'
  parent: keyVault
  properties: {
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: webAppPrincipalId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
        }
      }
    ]
  }
}

output apiKeySecretName string = apiKeySecret.name
output openAiKeySecretName string = openAiKeySecret.name
output lanceDbKeySecretName string = lanceDbKeySecret.name
