output "resource_group_name" {
  value       = azurerm_resource_group.rg.name
  description = "Resource group name"
}

output "key_vault_uri" {
  value       = azurerm_key_vault.kv.vault_uri
  description = "Key Vault URI"
}

output "search_endpoint" {
  value       = azurerm_search_service.search.search_service_url
  description = "Azure AI Search endpoint"
}

output "uai_id" {
  value       = azurerm_user_assigned_identity.uai.id
  description = "User Assigned Managed Identity resource id"
}

output "app_insights_connection_string" {
  value       = azurerm_application_insights.appi.connection_string
  description = "Application Insights connection string"
}
