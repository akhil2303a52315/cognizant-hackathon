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
    "risk":      {"primary": "nvidia:meta/llama-3.1-8b-instruct", "fallback": ["groq:llama-3.3-70b-versatile", "openrouter:meta-llama/llama-3.3-70b-instruct:free", "google:gemini-2.0-flash"]},
    "supply":    {"primary": "nvidia:meta/llama-3.1-8b-instruct", "fallback": ["groq:llama-3.3-70b-versatile", "openrouter:qwen/qwen-2.5-72b-instruct:free", "sambanova:Meta-Llama-3.3-70B-Instruct"]},
    "logistics": {"primary": "nvidia:meta/llama-3.1-8b-instruct", "fallback": ["groq:llama-3.3-70b-versatile", "openrouter:meta-llama/llama-3.3-70b-instruct:free", "google:gemini-2.0-flash"]},
    "market":    {"primary": "nvidia:meta/llama-3.1-8b-instruct", "fallback": ["openrouter:deepseek/deepseek-r1:free", "groq:llama-3.3-70b-versatile", "google:gemini-2.0-flash"]},
    "finance":   {"primary": "nvidia:meta/llama-3.1-8b-instruct", "fallback": ["openrouter:deepseek/deepseek-r1:free", "groq:llama-3.3-70b-versatile", "cohere:command-r-plus"]},
    "brand":     {"primary": "nvidia:meta/llama-3.1-8b-instruct", "fallback": ["groq:llama-3.3-70b-versatile", "google:gemini-2.0-flash", "openrouter:google/gemma-2-9b-it:free"]},
    "moderator": {"primary": "nvidia:meta/llama-3.1-8b-instruct", "fallback": ["google:gemini-2.0-flash", "openrouter:deepseek/deepseek-r1:free", "groq:llama-3.3-70b-versatile"]},
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
