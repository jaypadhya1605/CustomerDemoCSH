# ============================================================================
# CommonSpirit Health - Conversational Analytics
# Deployment Script for Azure Resources
# ============================================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId = "2852c4f9-8fcc-47c1-8e96-c4142a9ae463",
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroupName = "rg-customerDemo-conversationAnalytics-clinical-jp-001",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus2",
    
    [Parameter(Mandatory=$false)]
    [string]$EnvironmentName = "csh-convanalytics",
    
    [Parameter(Mandatory=$false)]
    [string]$OpenAiEndpoint = "https://mf-custdemo-convanalytics-clinical-jp-001.cognitiveservices.azure.com/",
    
    [Parameter(Mandatory=$true)]
    [securestring]$OpenAiApiKey,
    
    [Parameter(Mandatory=$false)]
    [string]$OpenAiDeployment = "gpt-5-mini"
)

# Colors for output
function Write-Step { param($Message) Write-Host "➡️  $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

Write-Host ""
Write-Host "💜 CommonSpirit Health - Conversational Analytics Deployment" -ForegroundColor Magenta
Write-Host "=============================================================" -ForegroundColor Magenta
Write-Host ""

# Check Azure CLI is installed
Write-Step "Checking Azure CLI installation..."
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Success "Azure CLI version: $($azVersion.'azure-cli')"
} catch {
    Write-Error "Azure CLI not found. Please install: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
}

# Login to Azure (if not already logged in)
Write-Step "Checking Azure login status..."
$account = az account show --output json 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Warning "Not logged in. Opening browser for login..."
    az login
    $account = az account show --output json | ConvertFrom-Json
}
Write-Success "Logged in as: $($account.user.name)"

# Set subscription
Write-Step "Setting subscription to: $SubscriptionId"
az account set --subscription $SubscriptionId
Write-Success "Subscription set"

# Check if resource group exists
Write-Step "Checking resource group: $ResourceGroupName"
$rgExists = az group exists --name $ResourceGroupName
if ($rgExists -eq "true") {
    Write-Success "Resource group exists"
} else {
    Write-Warning "Resource group does not exist. Creating..."
    az group create --name $ResourceGroupName --location $Location
    Write-Success "Resource group created"
}

# Deploy Bicep template
Write-Step "Deploying Azure infrastructure..."
Write-Host "   This may take 5-10 minutes..." -ForegroundColor Gray

$deploymentName = "csh-deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$apiKeyPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($OpenAiApiKey))

$deployment = az deployment group create `
    --name $deploymentName `
    --resource-group $ResourceGroupName `
    --template-file "infra/main.bicep" `
    --parameters location=$Location `
    --parameters environmentName=$EnvironmentName `
    --parameters appServicePlanSku="B1" `
    --parameters azureOpenAiEndpoint=$OpenAiEndpoint `
    --parameters azureOpenAiApiKey=$apiKeyPlain `
    --parameters azureOpenAiDeployment=$OpenAiDeployment `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Error "Deployment failed!"
    exit 1
}

Write-Success "Infrastructure deployment completed"

# Get deployment outputs
Write-Step "Retrieving deployment outputs..."
$outputs = $deployment.properties.outputs

$appServiceUrl = $outputs.appServiceUrl.value
$functionAppUrl = $outputs.functionAppUrl.value
$logAnalyticsId = $outputs.logAnalyticsWorkspaceId.value
$appInsightsKey = $outputs.appInsightsInstrumentationKey.value

Write-Host ""
Write-Host "=============================================================" -ForegroundColor Magenta
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "=============================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "📊 Deployment Outputs:" -ForegroundColor Cyan
Write-Host "   App Service URL:        $appServiceUrl" -ForegroundColor White
Write-Host "   Function App URL:       $functionAppUrl" -ForegroundColor White
Write-Host "   Log Analytics ID:       $logAnalyticsId" -ForegroundColor White
Write-Host "   App Insights Key:       $($appInsightsKey.Substring(0,8))..." -ForegroundColor White
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Deploy application code using GitHub Actions or:" -ForegroundColor White
Write-Host "      az webapp deploy --resource-group $ResourceGroupName --name <app-name> --src-path ." -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Configure GitHub Secrets for CI/CD:" -ForegroundColor White
Write-Host "      - AZURE_CREDENTIALS" -ForegroundColor Gray
Write-Host "      - AZURE_SUBSCRIPTION_ID" -ForegroundColor Gray
Write-Host "      - AZURE_RESOURCE_GROUP" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Test the application:" -ForegroundColor White
Write-Host "      Open: $appServiceUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "💰 Estimated Monthly Cost: ~\$30-40 (demo workload)" -ForegroundColor Cyan
Write-Host ""
