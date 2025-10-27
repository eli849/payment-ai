# Payments Assistant on Azure

A secure, enterprise-ready scaffold for a payments assistant using Azure AI services:

- Azure AI Agents Service (via Azure AI Foundry) – pluggable client abstraction
- Azure AI Search for knowledge grounding
- Python FastAPI service with clean separation of concerns
- Jupyter notebooks for exploration
- Terraform IaC with secure defaults (Key Vault, Managed Identity, App Insights, Search)
- GitHub Actions CI/CD with OIDC (no secrets)

This repo is structured similarly to Azure Samples enterprise repos, tailored for financial transaction and payments scenarios.

## Repo structure

- `src/` – Application code (API, agents, domain, search, security, config)
- `infra/terraform/` – Terraform root and modules
- `notebooks/` – Jupyter notebooks for exploration
- `data/` – Sample datasets
- `.github/workflows/` – CI and infra automation
- `tests/` – Unit tests

## Security-first defaults

- Managed Identity-first auth for Azure SDKs
- No secrets in code or workflows; use OIDC and Key Vault
- App Insights hooked for observability (configure connection string)
- Terraform with Key Vault purge protection on and Search with identity

## Prerequisites

- Python 3.11+
- Terraform (Windows) – install with:

```powershell
winget install Hashicorp.Terraform
```

- Azure subscription and permissions to create resources
- GitHub repository to host OIDC workflows

## Quickstart – run the API locally

1. Create and fill `.env` from `.env.example` (Search is optional for local demo):
2. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
. .\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

3. Start the API:

```powershell
uvicorn src.api.main:app --reload --port 8000
```

4. Test:

```powershell
Invoke-RestMethod -Method Get http://localhost:8000/healthz
```

## Provision infra with Terraform

Edit variables in `infra/terraform/variables.tf` or provide a tfvars file. Then:

```powershell
cd infra/terraform
terraform init
terraform validate
terraform plan -out tfplan
terraform apply tfplan
```

Notes:
- Default region is West US (`westus`). Change it via `var.location` in `infra/terraform/variables.tf` or by passing `-var location=<region>`.
- Use remote state for team environments (Azure Storage backend)
- Ensure the Search service, Key Vault, and Managed Identity are in the same region/resource group for simplicity

## Bootstrap Azure AI Search (create index + upload sample docs)

For local experimentation, you can create an index and upload the sample CSV using AAD (no Admin keys):

1. Ensure your identity (or the UAI when running in Azure) has Search Index Data Contributor. This scaffold sets it by default via Terraform (see `grant_search_index_data_contributor`).
2. Set in `.env`:
	- `AZURE_SEARCH_SERVICE` – your service name (no https)
	- `AZURE_SEARCH_INDEX` – e.g., `transactions`
3. Run the ingestion script:

```powershell
. .\.venv\Scripts\Activate.ps1
$env:AZURE_SEARCH_SERVICE='<your-search-name>'
$env:AZURE_SEARCH_INDEX='transactions'
python scripts/ingest_search.py
```

This creates the index (if missing) and uploads `data/payments/sample_transactions.csv`.

## GitHub Actions OIDC

This repo includes `.github/workflows/terraform.yml` with OIDC using `azure/login@v2`.

Setup steps:
- Create a Federated Credential on an Azure AD App (or User Assigned Managed Identity) for your GitHub repo
- Store `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID` as `Actions variables` or `secrets`
- Push to `main` to trigger validate/plan; manual approval for apply

References:
- https://github.com/azure/login
- https://learn.microsoft.com/azure/developer/github/connect-from-azure?tabs=azure-portal%2Cwindows#use-openid-connect

## Wiring Azure AI Agents and Azure OpenAI

The `src/agents/agent_client.py` supports two modes:

1) Local placeholder (default):
	- No external calls; helpful canned responses for payments questions.

2) Azure OpenAI (secure via Key Vault):
	- Store the Azure OpenAI API key in Key Vault as a secret (e.g., `aoai-key-fiserv`).
	- Ensure the User Assigned Managed Identity has the Key Vault role "Key Vault Secrets User" (Terraform sets this).
	- Configure `.env`:
	  - `KEY_VAULT_URI` – your vault URI
	  - `AZURE_OPENAI_ENDPOINT` – e.g., `https://<account>.openai.azure.com`
	  - `AZURE_OPENAI_DEPLOYMENT` – your chat/completions deployment name
	- `AZURE_OPENAI_API_VERSION` – recommended stable: `2024-06-01`
	  - `AZURE_OPENAI_API_KEY_SECRET_NAME` – the secret name holding the API key
	- The agent fetches the key from Key Vault using Managed Identity and calls Azure OpenAI via the OpenAI SDK with Azure base_url.

Planned: When Azure AI Agents Service is ready in your region, replace the client internals to call the Agents endpoint (the public interface stays the same).

## Notebooks

- `01_search_quickstart.ipynb` – connect to Azure AI Search with AAD and run simple queries
- `02_agent_payments_demo.ipynb` – demonstrate a chat flow and tool use (placeholder)

## Testing

```powershell
pytest -q
```

## Next steps

- Add private networking (Private Endpoints) to Key Vault and Search
- Add Azure Container Apps or Functions hosting with MSI
- Add ingestion pipelines for Search (indexer or Data Sources)
- Integrate Azure AI Agents SDK once GA for your region

## How it works (architecture & flows)

- Identity and Security
	- Local dev uses your developer sign-in (DefaultAzureCredential), while Azure uses Managed Identity.
	- GitHub Actions authenticates to Azure using OIDC; no secrets in repo.
	- Key Vault stores sensitive values (like Azure OpenAI API key); code retrieves via MSI/RBAC at runtime.

- Data and Retrieval
	- Azure AI Search provides enterprise search; the app’s `AzureSearch` wrapper uses AAD, not admin keys.
	- You can index the sample CSV or your own datasets and query via the notebook or service integration.

- App and Agent
	- FastAPI exposes `/chat` and `/healthz`.
	- The agent client picks Azure OpenAI if configured (securely via KV), else returns safe placeholders.

- Infra as Code
	- Terraform provisions RG, UAI, Key Vault (purge protection), App Insights, Storage, and AI Search.
	- RBAC grants the UAI least-privilege roles: Key Vault Secrets User and Search Index Data Reader.

## Usage examples

Call the API:

```powershell
# Health
Invoke-RestMethod -Method Get http://localhost:8000/healthz

# Chat
$body = @{ messages = @(@{ role = 'user'; content = 'How do I process a refund?' }) } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/chat -ContentType 'application/json' -Body $body
```

Query Azure AI Search (in notebook `01_search_quickstart.ipynb`):
- Set `AZURE_SEARCH_SERVICE` and `AZURE_SEARCH_INDEX` in `.env`
- Run the notebook cells to list, query, and visualize results using AAD (no keys)

## License

MIT

