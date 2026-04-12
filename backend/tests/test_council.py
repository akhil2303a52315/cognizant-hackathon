import pytest
from backend.graph import build_council_graph


class TestGraph:
    def test_compiles(self):
        graph = build_council_graph()
        assert graph is not None

    def test_has_all_nodes(self):
        graph = build_council_graph()
        compiled = graph.compile()
        for node in ["moderator", "risk", "supply", "logistics", "market", "finance", "brand", "synthesize"]:
            assert node in compiled.nodes
