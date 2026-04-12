import pytest
from backend.llm.router import LLMRouter, ROUTING


class TestRouter:
    def test_all_agents_routed(self):
        router = LLMRouter()
        assert set(ROUTING.keys()) == {"risk", "supply", "logistics", "market", "finance", "brand", "moderator"}

    def test_fallback_chains(self):
        for agent, cfg in ROUTING.items():
            assert len(cfg["fallback"]) >= 2
