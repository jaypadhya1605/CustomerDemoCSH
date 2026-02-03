// ============================================================================
// CommonSpirit Health - Conversational Analytics Infrastructure
// Azure Bicep Template - Core Services Only (No App Service)
// ============================================================================

@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment name prefix')
param environmentName string = 'csh-convanalytics'

@description('Azure OpenAI Endpoint URL')
param azureOpenAiEndpoint string

@description('Azure OpenAI API Key')
@secure()
param azureOpenAiApiKey string

// ============================================================================
// Variables
// ============================================================================
var uniqueSuffix = uniqueString(resourceGroup().id)
var storageAccountName = 'st${replace(environmentName, '-', '')}${take(uniqueSuffix, 6)}'
var logAnalyticsName = 'law-${environmentName}-${uniqueSuffix}'
var appInsightsName = 'appi-${environmentName}-${uniqueSuffix}'

// ============================================================================
// Log Analytics Workspace
// ============================================================================
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
  tags: {
    environment: 'demo'
    project: 'CommonSpirit-ConvAnalytics'
    costCenter: 'customer-demo'
  }
}

// ============================================================================
// Application Insights
// ============================================================================
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
  tags: {
    environment: 'demo'
    project: 'CommonSpirit-ConvAnalytics'
  }
}

// ============================================================================
// Storage Account (for VTE data and Functions)
// ============================================================================
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    accessTier: 'Hot'
  }
  tags: {
    environment: 'demo'
    project: 'CommonSpirit-ConvAnalytics'
  }
}

// Blob container for VTE data
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource vteDataContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'vte-data'
  properties: {
    publicAccess: 'None'
  }
}

resource costsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'costs'
  properties: {
    publicAccess: 'None'
  }
}

// ============================================================================
// Outputs
// ============================================================================
output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId
output logAnalyticsWorkspaceName string = logAnalytics.name
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output storageAccountName string = storageAccount.name
output storageConnectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
