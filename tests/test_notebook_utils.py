import importlib.util
import os
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location("notebook_utils", Path(__file__).parents[1] / "notebooks/notebook_utils.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def test_required_keys_must_be_nonempty(monkeypatch):
    monkeypatch.setattr(module, "load_dotenv", lambda **kwargs: False)
    monkeypatch.setenv("FIXTURE_REQUIRED_KEY", "")
    with pytest.raises(ValueError, match="FIXTURE_REQUIRED_KEY"):
        module.setup_environment("offline", ["FIXTURE_REQUIRED_KEY"])

def test_setup_does_not_enable_tracing(monkeypatch):
    monkeypatch.setattr(module, "load_dotenv", lambda **kwargs: False)
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    monkeypatch.setenv("FIXTURE_REQUIRED_KEY", "fixture")
    module.setup_environment("offline", ["FIXTURE_REQUIRED_KEY"])
    assert os.environ["LANGCHAIN_TRACING_V2"] == "false"

def test_visualization_does_not_call_remote_fallback():
    class Graph:
        def draw_png(self):
            raise RuntimeError("no local renderer")
        def draw_mermaid_png(self):
            pytest.fail("unexpected outbound rendering")
        def draw_mermaid(self):
            return "graph TD; A-->B"
    class App:
        def get_graph(self):
            return Graph()
    class Console:
        def print(self, *args, **kwargs):
            pass
    module.visualize_graph(App(), Console())


def test_notebooks_do_not_force_opt_in_tracing():
    import ast
    import json
    for path in (Path(__file__).parents[1] / "notebooks").glob("*.ipynb"):
        for cell in json.loads(path.read_text())["cells"]:
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell["source"])
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and node.value.value == "true":
                    assert not any(isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) and t.slice.value == "LANGCHAIN_TRACING_V2" for t in node.targets), path.name
