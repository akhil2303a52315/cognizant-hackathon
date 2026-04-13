import os
import logging
import asyncio
from typing import AsyncIterator
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
    "groq": lambda model="llama-3.3-70b-versatile", streaming=False: get_groq_client(model, streaming),
    "openrouter": lambda model="meta-llama/llama-3.3-70b-instruct:free", streaming=False: get_openrouter_client(model, streaming),
    "nvidia": lambda model="meta/llama-3.1-8b-instruct", streaming=False: get_nvidia_client(model, streaming),
    "google": lambda model="gemini-2.0-flash", streaming=False: get_google_client(model, streaming),
    "cohere": lambda model="command-r-plus", streaming=False: get_cohere_client(model, streaming),
    "sambanova": lambda model="Meta-Llama-3.3-70B-Instruct", streaming=False: get_sambanova_client(model, streaming),
}

ROUTING = {
    "risk":      {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:meta-llama/llama-3.3-70b-instruct:free", "nvidia:meta/llama-3.1-70b-instruct", "nvidia:meta/llama-3.1-8b-instruct"]},
    "supply":    {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:meta-llama/llama-3.3-70b-instruct:free", "nvidia:mistralai/mixtral-8x7b-instruct-v0.1", "nvidia:meta/llama-3.1-8b-instruct"]},
    "logistics": {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:meta-llama/llama-3.3-70b-instruct:free", "nvidia:microsoft/phi-3-medium-128k-instruct", "nvidia:meta/llama-3.1-8b-instruct"]},
    "market":    {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:meta-llama/llama-3.3-70b-instruct:free", "nvidia:meta/llama-3.1-8b-instruct", "nvidia:mistralai/mixtral-8x7b-instruct-v0.1"]},
    "finance":   {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:meta-llama/llama-3.3-70b-instruct:free", "nvidia:mistralai/mistral-7b-instruct-v0.3", "nvidia:meta/llama-3.1-70b-instruct"]},
    "brand":     {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:meta-llama/llama-3.3-70b-instruct:free", "nvidia:microsoft/phi-3-mini-128k-instruct", "nvidia:meta/llama-3.1-8b-instruct"]},
    "moderator": {"primary": "groq:llama-3.3-70b-versatile", "fallback": ["openrouter:meta-llama/llama-3.3-70b-instruct:free", "nvidia:meta/llama-3.1-70b-instruct", "nvidia:mistralai/mixtral-8x7b-instruct-v0.1"]},
}


class LLMRouter:
    _clients = {}
    _stream_clients = {}

    def _get_client(self, provider: str, model: str, streaming: bool = False):
        if streaming:
            key = f"stream:{provider}:{model}"
            cache = self._stream_clients
        else:
            key = f"{provider}:{model}"
            cache = self._clients

        if key not in cache:
            factory = PROVIDER_FACTORIES.get(provider)
            if not factory:
                raise ValueError(f"Unknown provider: {provider}")
            cache[key] = factory(model, streaming=streaming)
        return cache[key]

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

    async def stream_with_fallback(self, agent: str, messages: list) -> AsyncIterator[str]:
        """Stream tokens from the LLM with fallback support."""
        config = ROUTING.get(agent, ROUTING["risk"])
        all_models = [config["primary"]] + config["fallback"]

        for model_key in all_models:
            try:
                provider, model = model_key.split(":", 1)
                client = self._get_client(provider, model, streaming=True)
                async for chunk in client.astream(messages):
                    if chunk.content:
                        yield chunk.content
                return
            except asyncio.TimeoutError:
                logger.warning(f"Stream {model_key} timed out for {agent}")
                continue
            except Exception as e:
                logger.warning(f"Stream {model_key} failed for {agent}: {e}")
                continue

        raise RuntimeError(f"All LLM streaming providers failed for agent {agent}")


llm_router = LLMRouter()
