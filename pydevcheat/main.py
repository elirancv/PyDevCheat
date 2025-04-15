import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from typing import Optional
import json
import os
from pathlib import Path
from pydevcheat.sources import TLDRSource, CheatShSource
import pyperclip

app = typer.Typer(
    name="pydevcheat",
    help="Quick access to programming cheat sheets and command snippets",
    add_completion=False
)
console = Console()

# Cache directory setup
CACHE_DIR = Path.home() / ".pydevcheat" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "cheats.json"

# Initialize sources
tldr_source = TLDRSource()
cheatsh_source = CheatShSource()

def load_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache_data):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache_data, f)

@app.command()
def cheat(
    query: str = typer.Argument(..., help="The command or topic to search for"),
    source: str = typer.Option("tldr", help="Source to search from (tldr, cheatsh)"),
    copy: bool = typer.Option(False, "--copy", "-c", help="Copy result to clipboard"),
):
    """
    Search for cheat sheets and command snippets.
    """
    cache = load_cache()
    cache_key = f"{source}:{query}"
    
    if cache_key in cache:
        result = cache[cache_key]
    else:
        if source == "tldr":
            result = tldr_source.search(query)
        elif source == "cheatsh":
            result = cheatsh_source.search(query)
        else:
            console.print(f"[red]Unknown source: {source}[/red]")
            raise typer.Exit(1)
        
        cache[cache_key] = result
        save_cache(cache)
    
    # Display the result
    syntax = Syntax(result, "bash", theme="monokai")
    console.print(Panel(syntax, title=f"Cheat Sheet: {query}", border_style="blue"))
    
    if copy:
        pyperclip.copy(result)
        console.print("[green]Copied to clipboard![/green]")

@app.command()
def sync():
    """
    Sync TLDR pages locally for offline use.
    """
    try:
        tldr_source.sync()
        console.print("[green]Successfully synced TLDR pages![/green]")
    except Exception as e:
        console.print(f"[red]Failed to sync TLDR pages: {str(e)}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 