// llm-locker hosting topology — simple version. Public network access with
// firewall rules / RBAC / auth, not private networking — see BACKLOG.md
// "Hosting / ops" for the fuller topology (VNet + private endpoints) to
// harden into later. Encryption key never reaches Azure at all (E2EE
// happens client-side); this only needs to protect ciphertext and the API
// auth key, which is why there's no customer-managed key here.
//
// Before deploying: the deploying account needs "Key Vault Secrets Officer"
// on this resource group/subscription (or will after the Key Vault is
// created — grant it explicitly if unsure). enableRbacAuthorization below
// means Key Vault access is RBAC-gated, and creating secrets is a
// data-plane operation Contributor/Owner alone does not cover — without
// this, the deployment 403s on the secret resources partway through.
//
// Deploy with:
//   az group create --name rg-llm-locker --location eastus
//   az deployment group create --resource-group rg-llm-locker \
//     --template-file main.bicep --parameters postgresAdminPassword=<secret>

@description('Postgres administrator password — pass via --parameters, never commit it.')
@secure()
param postgresAdminPassword string

// Defaults to centralus, not resourceGroup().location (rg-llm-locker is in
// eastus) — this subscription has Postgres Flexible Server provisioning
// restricted in eastus/eastus2/southcentralus (confirmed via
// `az postgres flexible-server list-skus --location <region>`); centralus
// and westus3 are open. Resource group location and resource location
// differing is normal in Azure, not a mismatch to fix.
param location string = 'centralus'
param namePrefix string = 'locker'
param postgresDatabaseName string = 'lockerdb'

// --- Managed identity -------------------------------------------------------
// User-assigned, not the App Service's system-assigned identity. Reason:
// a system-assigned identity doesn't exist until the App Service resource
// itself is created, so the Key Vault role assignment granting it access
// can only happen *after* — and if the app tries to resolve its Key Vault
// references before that role assignment finishes propagating, it comes up
// with empty secrets on first boot (a well-documented App Service gotcha).
// A UAMI can be created and granted access *before* the App Service exists
// at all, removing that race entirely.
resource appIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namePrefix}-identity'
  location: location
}

// --- Key Vault ------------------------------------------------------------
// Holds LOCKER_API_KEY and the Postgres connection string. Public access
// (no private endpoint) — locked down by RBAC + auth, not network isolation.

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${namePrefix}-kv-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
  }
}

// Granted before the App Service exists — see appIdentity comment above.
resource keyVaultSecretsUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, appIdentity.id, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6' // Key Vault Secrets User
    )
  }
}

// --- Postgres Flexible Server -----------------------------------------------
// Public access + firewall rule, not VNet-integrated. Default (Azure-managed)
// encryption at rest is sufficient — content is already ciphertext by the
// time it reaches here, so no customer-managed key is needed.

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: '${namePrefix}-postgres-${uniqueString(resourceGroup().id)}'
  location: location
  sku: { name: 'Standard_B1ms', tier: 'Burstable' }
  properties: {
    version: '16'
    administratorLogin: 'lockeradmin'
    administratorLoginPassword: postgresAdminPassword
    storage: { storageSizeGB: 32 }
    network: { publicNetworkAccess: 'Enabled' }
    highAvailability: { mode: 'Disabled' }
  }
}

// Special "0.0.0.0–0.0.0.0" rule = allow traffic from other Azure
// resources (including this App Service), per Azure's documented convention.
resource postgresAllowAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-06-01-preview' = {
  parent: postgres
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// A dedicated application database — not the default `postgres` maintenance
// database, which isn't meant to hold app tables even for testing.
resource lockerDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: postgres
  name: postgresDatabaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// --- App Insights -----------------------------------------------------------

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${namePrefix}-insights'
  location: location
  kind: 'web'
  properties: { Application_Type: 'web' }
}

// --- App Service ------------------------------------------------------------

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${namePrefix}-plan'
  location: location
  sku: { name: 'B1', tier: 'Basic' }
  properties: { reserved: true } // required for Linux plans
}

resource appService 'Microsoft.Web/sites@2023-12-01' = {
  name: '${namePrefix}-api-${uniqueString(resourceGroup().id)}'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${appIdentity.id}': {}
    }
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    // Tells App Service which identity to use when resolving the
    // @Microsoft.KeyVault(...) references below — without this it falls
    // back to system-assigned, which doesn't exist on this resource.
    keyVaultReferenceIdentity: appIdentity.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      appSettings: [
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
        { name: 'LOCKER_API_KEY', value: '@Microsoft.KeyVault(SecretUri=${apiKeySecret.properties.secretUri})' }
        { name: 'LOCKER_DB_URL', value: '@Microsoft.KeyVault(SecretUri=${dbUrlSecret.properties.secretUri})' }
      ]
    }
  }
  // Explicit: nothing above textually forces the role assignment to finish
  // before this resource creates (appService no longer references
  // keyVaultSecretsUserRole directly now that it goes through appIdentity),
  // and this ordering is exactly the race #1 is about.
  dependsOn: [
    keyVaultSecretsUserRole
  ]
}

resource apiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'LOCKER-API-KEY'
  properties: { value: 'CHANGE-ME-after-deploy' } // rotate via az keyvault secret set
}

resource dbUrlSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'LOCKER-DB-URL'
  properties: {
    value: 'postgresql://lockeradmin:${postgresAdminPassword}@${postgres.properties.fullyQualifiedDomainName}:5432/${postgresDatabaseName}?sslmode=require'
  }
}

output appServiceUrl string = 'https://${appService.properties.defaultHostName}'
output postgresHost string = postgres.properties.fullyQualifiedDomainName
output keyVaultName string = keyVault.name
output appIdentityPrincipalId string = appIdentity.properties.principalId
