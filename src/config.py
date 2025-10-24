from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # General
    app_name: str = Field("fiserv-payments-assistant", description="Application name")
    environment: str = Field("dev", description="Environment name: dev|test|prod")

    # Azure AI Search
    azure_search_service: str | None = Field(
        default=None, description="Name of the Azure AI Search service (no https)"
    )
    azure_search_index: str | None = Field(
        default=None, description="Default Search index to query"
    )

    # Azure AI Foundry / Agents Service (placeholders)
    azure_ai_agents_endpoint: str | None = Field(
        default=None,
        description="Base URL for Azure AI Agents (e.g., https://<resource>.openai.azure.com)",
    )
    azure_ai_agents_api_version: str = Field(
        default="2024-10-01-preview",
        description="API version for Agents (update when GA)",
    )
    azure_ai_model_deployment: str | None = Field(
        default=None, description="Model deployment name (e.g., gpt-4o-mini)"
    )

    # Azure OpenAI (Chat/Assistants) via Key Vault secret
    azure_openai_endpoint: str | None = Field(
        default=None, description="Azure OpenAI endpoint (https://<account>.openai.azure.com)"
    )
    azure_openai_deployment: str | None = Field(
        default=None, description="Chat/Completions deployment name"
    )
    azure_openai_api_key_secret_name: str | None = Field(
        default=None, description="Key Vault secret name that stores Azure OpenAI API key"
    )

    # Observability
    app_insights_connection_string: str | None = None

    # Security
    key_vault_uri: str | None = Field(default=None, description="Key Vault URI if used")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # reads env / .env
