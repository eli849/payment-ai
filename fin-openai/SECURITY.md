# Security Guidelines

- Use Azure AD and Managed Identity for all service-to-service authentication
- Store application secrets in Azure Key Vault; never commit secrets
- Enable Key Vault purge protection and soft-delete (configured in Terraform)
- Restrict public network access with Private Endpoints for production
- Grant least-privilege RBAC to identities; prefer built-in roles
- Use GitHub OIDC for federated identity to Azure (no long-lived credentials)
- Keep dependencies patched; run CI regularly
- Monitor with Application Insights and enable alerts for error rates

For any suspected vulnerability, please open a private issue or contact the maintainers.
