import os
import logging
from backend.llm.providers import (
    get_groq_client,
    get_openrouter_client,
    get_nvidia_client,
    get_google_client,
    get_cohere_client,
    get_sambanova_client,
)

logger = logging.getLogger(__name__)

PROVIDER_FACTORIES = {
    "groq": lambda model="llama-3.3-70b-versatile": get_groq_client(model),
    "openrouter": lambda model="meta-llama/llama-3.3-70b-instruct:free": get_openrouter_client(model),
    "nvidia": lambda model="meta/llama-3.1-8b-instruct": get_nvidia_client(model),
    "google": lambda model="gemini-2.0-flash": get_google_client(model),
    "cohere": lambda model="command-r-plus": get_cohere_client(model),
    "sambanova": lambda model="Meta-Llama-3.3-70B-Instruct": get_sambanova_client(model),
}

ROUTING = {
    "risk":      {"primary": "nvidia:meta/llama-3.1-70b-instruct", "fallback": ["nvidia:meta/llama-3.1-8b-instruct", "nvidia:mistralai/mixtral-8x7b-instruct-v0.1", "nvidia:microsoft/phi-3-medium-128k-instruct"]},
    "supply":    {"primary": "nvidia:mistralai/mixtral-8x7b-instruct-v0.1", "fallback": ["nvidia:meta/llama-3.1-70b-instruct", "nvidia:mistralai/mistral-7b-instruct-v0.3", "nvidia:meta/llama-3.1-8b-instruct"]},
    "logistics": {"primary": "nvidia:microsoft/phi-3-medium-128k-instruct", "fallback": ["nvidia:meta/llama-3.1-70b-instruct", "nvidia:mistralai/mixtral-8x7b-instruct-v0.1", "nvidia:meta/llama-3.1-8b-instruct"]},
    "market":    {"primary": "nvidia:meta/llama-3.1-8b-instruct", "fallback": ["nvidia:mistralai/mistral-7b-instruct-v0.3", "nvidia:microsoft/phi-3-medium-128k-instruct", "nvidia:mistralai/mixtral-8x7b-instruct-v0.1"]},
    "finance":   {"primary": "nvidia:mistralai/mistral-7b-instruct-v0.3", "fallback": ["nvidia:meta/llama-3.1-70b-instruct", "nvidia:microsoft/phi-3-medium-128k-instruct", "nvidia:mistralai/mixtral-8x7b-instruct-v0.1"]},
    "brand":     {"primary": "nvidia:microsoft/phi-3-mini-128k-instruct", "fallback": ["nvidia:mistralai/mistral-7b-instruct-v0.3", "nvidia:meta/llama-3.1-8b-instruct", "nvidia:mistralai/mixtral-8x7b-instruct-v0.1"]},
    "moderator": {"primary": "nvidia:meta/llama-3.1-70b-instruct", "fallback": ["nvidia:mistralai/mixtral-8x7b-instruct-v0.1", "nvidia:microsoft/phi-3-medium-128k-instruct", "nvidia:meta/llama-3.1-8b-instruct"]},
}


class LLMRouter:
    _clients = {}

    def _get_client(self, provider: str, model: str):
        key = f"{provider}:{model}"
        if key not in self._clients:
            factory = PROVIDER_FACTORIES.get(provider)
            if not factory:
                raise ValueError(f"Unknown provider: {provider}")
            self._clients[key] = factory(model)
        return self._clients[key]

    async def invoke_with_fallback(self, agent: str, messages: list):
        config = ROUTING.get(agent, ROUTING["risk"])

        # Try primary
        try:
            provider, model = config["primary"].split(":", 1)
            client = self._get_client(provider, model)
            response = await client.ainvoke(messages)
            return response, config["primary"]
        except Exception as e:
            logger.warning(f"Primary failed for {agent}: {e}")

        # Try fallbacks
        for fb in config["fallback"]:
            try:
                provider, model = fb.split(":", 1)
                client = self._get_client(provider, model)
                response = await client.ainvoke(messages)
                return response, fb
            except Exception as e:
                logger.warning(f"Fallback {fb} failed for {agent}: {e}")

        raise RuntimeError(f"All LLM providers failed for agent {agent}")


llm_router = LLMRouter()
