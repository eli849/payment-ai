from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import os
from openai import OpenAI

from ..config import get_settings
from ..security.key_vault import get_secret

logger = logging.getLogger(__name__)


@dataclass
class Message:
    role: str
    content: str


class AgentClient:
    """Abstracts interaction with an agent.

    This default implementation is a placeholder that can be replaced with Azure AI Agents Service
    or Azure OpenAI Assistants when you wire them up. We keep the interface minimal and focused.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: Optional[OpenAI] = None
        self._model: Optional[str] = None

        # Prefer Azure OpenAI if configured
        if (
            self.settings.azure_openai_endpoint
            and self.settings.azure_openai_deployment
            and self.settings.key_vault_uri
            and self.settings.azure_openai_api_key_secret_name
        ):
            api_key = get_secret(
                self.settings.key_vault_uri,
                self.settings.azure_openai_api_key_secret_name,
            )
            if api_key:
                # OpenAI SDK works with Azure by overriding base_url & api_key
                base_url = (
                    f"{self.settings.azure_openai_endpoint}/openai/deployments/"
                    f"{self.settings.azure_openai_deployment}"
                )
                # The Azure OpenAI API version – update to latest supported
                api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
                self._client = OpenAI(
                    base_url=f"{base_url}",
                    api_key=api_key,
                    default_headers={"api-version": api_version},
                )
                self._model = self.settings.azure_openai_deployment

    def chat(self, messages: List[Message], tools: Optional[Dict[str, Any]] = None) -> str:
        """Respond to a chat conversation.

        Parameters
        - messages: List of Message(role, content)
        - tools: optional set of callable tools to augment the agent
        """
        # If Azure OpenAI is configured, route to chat completions
        if self._client and self._model:
            try:
                # Convert to OpenAI messages format
                msgs = [{"role": m.role, "content": m.content} for m in messages]
                resp = self._client.chat.completions.create(
                    model=self._model,
                    messages=msgs,
                    temperature=0.2,
                )
                return resp.choices[0].message.content or ""
            except Exception:
                # Fall back to placeholder if Azure call fails
                pass

        # Simple rule-based placeholder for local dev
        last = messages[-1].content if messages else ""
        if "refund" in last.lower():
            return (
                "To process a refund, ensure the transaction is settled. "
                "I can check transaction status if you provide the transaction_id."
            )
        if "fee" in last.lower():
            return (
                "Standard domestic card present fee is 2.9% + $0.30. "
                "Interchange varies by card network and MCC."
            )
        return (
            "I'm your Payments Assistant. Ask me about transactions, fees, chargebacks, or settlement windows."
        )


def get_agent_client() -> AgentClient:
    # In future, return AzureAgentsClient if azure_ai_agents_endpoint is configured.
    return AgentClient()
