import os
from typing import TYPE_CHECKING, List, Optional
from dotenv import load_dotenv

if TYPE_CHECKING:
    from rich.console import Console

def setup_environment(project_name: str, required_keys: Optional[List[str]] = None) -> "Console":
    """
    Sets up the environment for the notebooks:
    1. Loads environment variables from .env file.
    2. Sets up LangSmith tracing.
    3. Checks for required API keys.
    4. Returns a Rich Console for printing.
    """
    # Lazy import rich components to reduce module import time
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    # Load .env from parent directory (assuming notebook is in the notebooks/ folder)
    # Adjust path if notebooks are nested deeper or moved
    env_path = "../.env"

    # Optimistic loading: try parent directory first, then current directory
    # This avoids redundant stat calls and correctly handles local .env fallback
    if load_dotenv(dotenv_path=env_path):
        pass
    elif load_dotenv(dotenv_path=".env"):
        pass
    else:
         console.print("[yellow]Warning:[/yellow] .env file not found in parent directory or current directory.")
    
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
    os.environ["LANGCHAIN_PROJECT"] = project_name
    
    if required_keys:
        missing_keys = [key for key in required_keys if not os.environ.get(key, "").strip()]
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")
    else:
        # Default check for Nebius and LangChain as they are used almost everywhere
        if not os.environ.get("NEBIUS_API_KEY"):
             console.print("[yellow]Warning:[/yellow] NEBIUS_API_KEY not found.")
        if not os.environ.get("LANGCHAIN_API_KEY"):
             console.print("[yellow]Warning:[/yellow] LANGCHAIN_API_KEY not found.")

    console.print(Panel(f"[green]Environment setup for '{project_name}' complete.[/green]", title="Setup", border_style="green"))
    return console

def visualize_graph(app, console: "Console", *, allow_remote: bool = False):
    """
    Visualizes the LangGraph application graph.
    Tries local PyGraphviz, then local Mermaid syntax. Remote Mermaid rendering
    is available only with allow_remote=True.
    """
    # Lazy import to reduce startup time for notebooks not using visualization
    from IPython.display import Image, display
    from rich.panel import Panel
    from rich.syntax import Syntax

    graph = app.get_graph()

    # Optimization: Try drawing with PyGraphviz first (local, faster than network call)
    try:
        png_image = graph.draw_png()
        display(Image(png_image))
        return
    except Exception:
        pass # Fallback

    # Remote rendering sends the diagram to a third-party service; explicit opt-in only.
    if allow_remote:
        try:
            png_image = graph.draw_mermaid_png()
            display(Image(png_image))
            return
        except Exception:
            pass

    # Fallback to syntax
    console.print(Panel(
        "[yellow]Could not generate graph image.[/yellow]\n"
        "PyGraphviz or Mermaid API failed. Here is the Mermaid syntax:",
        title="Graph Visualization Fallback",
        border_style="yellow"
    ))
    try:
        mermaid_code = graph.draw_mermaid()
        console.print(Syntax(mermaid_code, "mermaid", theme="monokai", line_numbers=True))
    except Exception as e:
        console.print(f"[bold red]Failed to get mermaid syntax:[/bold red] {e}")
