// ============================================================================
// CommonSpirit Health - Conversational Analytics Infrastructure
// Azure Bicep Template for Demo Deployment
// ============================================================================

@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment name prefix')
param environmentName string = 'csh-convanalytics'

@description('App Service Plan SKU')
@allowed(['B1', 'B2', 'S1', 'P1v2'])
param appServicePlanSku string = 'B1'

@description('Azure OpenAI Endpoint URL')
param azureOpenAiEndpoint string

@description('Azure OpenAI API Key')
@secure()
param azureOpenAiApiKey string

@description('Azure OpenAI Deployment Name')
param azureOpenAiDeployment string = 'gpt-5-mini'

// ============================================================================
// Variables
// ============================================================================
var uniqueSuffix = uniqueString(resourceGroup().id)
var appServicePlanName = 'asp-${environmentName}-${uniqueSuffix}'
var appServiceName = 'app-${environmentName}-${uniqueSuffix}'
var functionAppName = 'func-${environmentName}-${uniqueSuffix}'
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
// Storage Account (for Azure Functions)
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

// ============================================================================
// App Service Plan (Linux for Python)
// ============================================================================
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  kind: 'linux'
  sku: {
    name: appServicePlanSku
    capacity: 1
  }
  properties: {
    reserved: true  // Required for Linux
  }
  tags: {
    environment: 'demo'
    project: 'CommonSpirit-ConvAnalytics'
  }
}

// ============================================================================
// App Service (Streamlit Web App)
// ============================================================================
resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: appServiceName
  location: location
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: appServicePlanSku != 'B1' // AlwaysOn not available on B1
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appCommandLine: 'python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0'
      appSettings: [
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: azureOpenAiEndpoint
        }
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: azureOpenAiApiKey
        }
        {
          name: 'AZURE_OPENAI_DEPLOYMENT'
          value: azureOpenAiDeployment
        }
        {
          name: 'AZURE_OPENAI_API_VERSION'
          value: '2024-12-01-preview'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
      ]
    }
  }
  tags: {
    environment: 'demo'
    project: 'CommonSpirit-ConvAnalytics'
    customer: 'CommonSpirit Health'
  }
}

// Configure Python dependencies
resource appServiceConfig 'Microsoft.Web/sites/config@2023-01-01' = {
  parent: appService
  name: 'web'
  properties: {
    pythonVersion: '3.11'
    requestTracingEnabled: true
    httpLoggingEnabled: true
    detailedErrorLoggingEnabled: true
  }
}

// ============================================================================
// Azure Functions (Consumption Plan for Workflows)
// ============================================================================
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: appServicePlan.id  // Sharing plan for cost efficiency in demo
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: azureOpenAiEndpoint
        }
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: azureOpenAiApiKey
        }
      ]
    }
  }
  tags: {
    environment: 'demo'
    project: 'CommonSpirit-ConvAnalytics'
  }
}

// ============================================================================
// Diagnostic Settings
// ============================================================================
resource appServiceDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'diag-${appServiceName}'
  scope: appService
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      {
        category: 'AppServiceHTTPLogs'
        enabled: true
      }
      {
        category: 'AppServiceConsoleLogs'
        enabled: true
      }
      {
        category: 'AppServiceAppLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource functionAppDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'diag-${functionAppName}'
  scope: functionApp
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      {
        category: 'FunctionAppLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

// ============================================================================
// Outputs
// ============================================================================
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output storageAccountName string = storageAccount.name
