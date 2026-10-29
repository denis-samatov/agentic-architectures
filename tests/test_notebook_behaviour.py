"""Execute original pure notebook definitions without credentials or provider calls."""
import ast
import json
import math
from pathlib import Path
import re
from types import SimpleNamespace
from typing import List, Tuple, TypedDict

from langgraph.graph import StateGraph, END

ROOT = Path(__file__).parents[1]

def definitions(file, cells, ns):
    data = json.loads((ROOT / "notebooks" / file).read_text())
    for index in cells:
        tree = ast.parse("".join(data["cells"][index]["source"]))
        nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        exec(compile(ast.Module(nodes, type_ignores=[]), file, "exec"), ns)
    return ns

def lats():
    class Console:
        def print(self, *args, **kwargs):
            pass
    class LLM:
        def invoke(self, prompt):
            return SimpleNamespace(content='op: 1 + 1 = 2, remaining: 2')
    return definitions("19_lats_mcts.ipynb", [8, 14, 16], dict(List=List, Tuple=Tuple, math=math, re=re, console=Console(), llm=LLM()))

def test_lats_rejects_text_and_judge_false_success():
    ns = lats()
    agent = ns["LATSAgent"]("4 9 10 13", simulations=1)
    agent.root.state = "1 + 1 = 24"
    agent.evaluate_and_reflect = lambda state: (1.0, "incorrect fixture judge")
    assert agent.solve().startswith("FAILURE")

def test_game24_allows_only_basic_arithmetic_and_original_multiset():
    env = lats()["Game24Env"]
    assert env.validate_expression("4 4 6 8", "(4+8)*(6-4)")
    assert not env.validate_expression("2 4 4 4", "2**4+4+4")
    assert not env.validate_expression("4 9 10 13", "1+1")

def test_self_refinement_returns_full_state_and_uses_selected_graph():
    class State(TypedDict):
        user_request: str
        draft_email: str
        critique: str
    graph = StateGraph(State)
    graph.add_node("generate", lambda state: {"draft_email": "offline draft"})
    graph.add_node("critique", lambda state: {"critique": "approved"})
    graph.set_entry_point("generate")
    graph.add_edge("generate", "critique")
    graph.add_edge("critique", END)
    compiled = graph.compile()
    ns = definitions("15_RLHF.ipynb", [10], {"self_refine_agent": compiled, "END": END})
    result = ns["run_agent"]("fixture")
    assert result["draft_email"] == "offline draft"
    assert result["critique"] == "approved"
    class SelectedGraph:
        def invoke(self, state):
            return dict(state, draft_email="memory graph")
    assert ns["run_agent"]("fixture", graph=SelectedGraph())["draft_email"] == "memory graph"


def test_lats_accepts_only_valid_full_expression_and_retains_path():
    ns = lats()
    agent = ns["LATSAgent"]("4 4 6 8", simulations=1)
    agent.expand_node = lambda node: ["solution: (4+8)*(6-4)"]
    agent.evaluate_and_reflect = lambda state: (0.2, "judge is not the oracle")
    answer = agent.solve()
    assert answer.startswith("FOUND: (4+8)*(6-4)")
    assert "Path:" in answer and "Start numbers:" in answer
