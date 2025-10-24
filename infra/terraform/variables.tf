variable "prefix" {
  description = "Resource name prefix"
  type        = string
  default     = "fsrv-ai"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "westus"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default = {
    owner       = "ai-platform"
    costcenter  = "payments"
    application = "fiserv-payments-assistant"
  }
}

variable "grant_search_index_data_contributor" {
  description = "Grant UAI Search Index Data Contributor (needed to create indexes and upload docs). Disable for prod."
  type        = bool
  default     = true
}
