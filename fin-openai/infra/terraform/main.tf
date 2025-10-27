locals {
  name = "${var.prefix}-${var.environment}"
}

resource "azurerm_resource_group" "rg" {
  name     = "${local.name}-rg"
  location = var.location
  tags     = var.tags
}

resource "azurerm_user_assigned_identity" "uai" {
  name                = "${local.name}-uai"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  tags                = var.tags
}

resource "azurerm_key_vault" "kv" {
  name                        = replace("${local.name}-kv", "-", "")
  location                    = var.location
  resource_group_name         = azurerm_resource_group.rg.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  rbac_authorization_enabled  = true
  purge_protection_enabled    = true
  soft_delete_retention_days  = 90
  public_network_access_enabled = true # consider private endpoints for prod
  tags                        = var.tags
}

data "azurerm_client_config" "current" {}

resource "azurerm_application_insights" "appi" {
  name                = "${local.name}-appi"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
  tags                = var.tags
}

resource "azurerm_storage_account" "sa" {
  name                            = substr(replace("${local.name}sa", "-", ""), 0, 24)
  resource_group_name             = azurerm_resource_group.rg.name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  allow_nested_items_to_be_public = false
  min_tls_version                 = "TLS1_2"
  public_network_access_enabled   = true
  tags                            = var.tags
}

resource "azurerm_search_service" "search" {
  name                = "${local.name}-search"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  sku                 = "basic" # upgrade to standard for prod
  replica_count       = 1
  partition_count     = 1
  public_network_access_enabled = true # consider private endpoints for prod

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# RBAC: allow User Assigned Identity to read Key Vault secrets
resource "azurerm_role_assignment" "kv_secrets_user" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.uai.principal_id
}

# RBAC: allow User Assigned Identity to read Search index data
resource "azurerm_role_assignment" "search_data_reader" {
  scope                = azurerm_search_service.search.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = azurerm_user_assigned_identity.uai.principal_id
}

resource "azurerm_role_assignment" "search_data_contributor" {
  count               = var.grant_search_index_data_contributor ? 1 : 0
  scope                = azurerm_search_service.search.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = azurerm_user_assigned_identity.uai.principal_id
}

# NOTE: Azure AI Foundry/Agents Service provisioning varies by API version and region.
# You can add a module here using azapi_resource to deploy preview resources when ready.
