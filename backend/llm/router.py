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
    "nvidia": lambda model="nvidia/llama-3.1-nemotron-70b-instruct": get_nvidia_client(model),
    "google": lambda model="gemini-2.0-flash": get_google_client(model),
    "cohere": lambda model="command-r-plus": get_cohere_client(model),
    "sambanova": lambda model="Meta-Llama-3.3-70B-Instruct": get_sambanova_client(model),
}

ROUTING = {
    "risk":      {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["nvidia:nvidia/llama-3.1-nemotron-70b-instruct", "openrouter:meta-llama/llama-3.3-70b-instruct:free", "google:gemini-2.0-flash"]},
    "supply":    {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:qwen/qwen-2.5-72b-instruct:free", "nvidia:nvidia/llama-3.1-nemotron-70b-instruct", "sambanova:Meta-Llama-3.3-70B-Instruct"]},
    "logistics": {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:meta-llama/llama-3.3-70b-instruct:free", "google:gemini-2.0-flash", "nvidia:nvidia/llama-3.1-nemotron-70b-instruct"]},
    "market":    {"primary": "openrouter:deepseek/deepseek-r1:free", "fallback": ["nvidia:nvidia/llama-3.1-nemotron-70b-instruct", "groq:llama-3.3-70b-versatile", "google:gemini-2.0-flash"]},
    "finance":   {"primary": "nvidia:nvidia/llama-3.1-nemotron-70b-instruct", "fallback": ["openrouter:deepseek/deepseek-r1:free", "groq:llama-3.3-70b-versatile", "cohere:command-r-plus"]},
    "brand":     {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["google:gemini-2.0-flash", "openrouter:google/gemma-2-9b-it:free", "nvidia:nvidia/llama-3.1-nemotron-70b-instruct"]},
    "moderator": {"primary": "google:gemini-2.0-flash", "fallback": ["openrouter:deepseek/deepseek-r1:free", "nvidia:nvidia/llama-3.1-nemotron-70b-instruct", "groq:llama-3.3-70b-versatile"]},
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
