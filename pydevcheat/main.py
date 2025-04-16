import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.style import Style
from rich.text import Text
from rich.box import DOUBLE, SQUARE, ROUNDED
from typing import Optional, List
import json
import os
from pathlib import Path
from pydevcheat.sources import TLDRSource, CheatShSource, DevhintsSource
import pyperclip
from .gui import run_gui
import logging
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Configure logging to suppress all debug messages
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("pydevcheat").setLevel(logging.WARNING)

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
devhints_source = DevhintsSource()

def load_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache_data):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache_data, f)

def wrap_text(text: str, width: int) -> List[str]:
    """
    Wrap text to specified width without breaking words.
    """
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + (1 if current_line else 0) <= width:
            if current_line:
                current_length += 1  # space
            current_line.append(word)
            current_length += len(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

@app.command()
def cheat(
    query: List[str] = typer.Argument(..., help="The command or topic to search for"),
    source: str = typer.Option("tldr", help="Source to search from (tldr, cheatsh, devhints)"),
    copy: bool = typer.Option(False, "--copy", "-c", help="Copy result to clipboard"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug output"),
):
    """
    Display cheat sheet for a given command or topic.
    """
    # Join multiple query words
    query_str = " ".join(query)
    
    if debug:
        console.print(f"[yellow]Debug: Searching for '{query_str}' in {source}[/yellow]")
    
    cache = load_cache()
    cache_key = f"{source}:{query_str}"
    
    if cache_key in cache:
        if debug:
            console.print("[yellow]Debug: Found result in cache[/yellow]")
        result = cache[cache_key]
    else:
        if debug:
            console.print("[yellow]Debug: Searching in source...[/yellow]")
        if source == "tldr":
            result = tldr_source.search(query_str)
        elif source == "cheatsh":
            result = cheatsh_source.search(query_str)
        elif source == "devhints":
            result = devhints_source.search(query_str)
        else:
            console.print(f"[red]Unknown source: {source}. Available sources: tldr, cheatsh, devhints[/red]")
            raise typer.Exit(1)
        
        if not result:
            console.print(f"[red]No results found for '{query_str}'[/red]")
            raise typer.Exit(1)
            
        cache[cache_key] = result
        save_cache(cache)

    # Create the title panel
    title = Text()
    title.append("⚡ ", style="bold yellow")
    title.append("[ ", style="bold blue")
    title.append("CHEAT", style="bold yellow")
    title.append("::", style="bold blue")
    title.append("SHEET", style="bold yellow")
    title.append(" ]", style="bold blue")
    title.append(" [ ", style="bold blue")
    title.append(query_str.upper(), style="bold cyan")
    title.append(" ] ⚡", style="bold blue")
    
    console.print()
    console.print(Panel(title, border_style="blue", box=SQUARE))

    # Create and style the table
    table = Table(
        show_header=True,
        box=SQUARE,
        padding=(0, 1),
        show_edge=True,
        border_style="blue",
        header_style="bold yellow",
        title_style="bold yellow",
        width=100
    )
    
    table.add_column("COMMAND", style="cyan bold", justify="left", width=35)
    table.add_column("DESCRIPTION", style="green", justify="left", width=65)

    # Process and add content to table
    current_section = None
    
    for line in result.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('#'):
            if current_section:
                # Add a separator between sections
                table.add_row("═" * 35, "═" * 65, style="blue")
            current_section = line.replace('#', '').strip()
            # Add section header
            table.add_row(
                Text("┌──[ " + current_section.upper() + " ]", style="bold yellow"),
                Text("", style="bold yellow")
            )
            table.add_row("└" + "─" * 34, "─" * 65, style="dim blue")
        elif '#' in line:
            cmd, desc = line.split('#', 1)
            cmd = cmd.strip()
            desc = desc.strip()
            
            # Word wrap the description
            wrapped_desc = wrap_text(desc, 60)
            if wrapped_desc:
                # Add first line with cyberpunk-style arrow
                table.add_row(
                    Text("│ > " + cmd, style="cyan bold"),
                    Text(wrapped_desc[0], style="green")
                )
                # Add continuation lines if any
                for cont_line in wrapped_desc[1:]:
                    table.add_row(
                        Text("│   ", style="cyan bold"),
                        Text(cont_line, style="green")
                    )

    # Display the table in a panel with a cyberpunk border
    console.print(Panel(
        table,
        border_style="blue",
        box=SQUARE,
        padding=(0, 1),
        title="[bold blue]<<[bold yellow] COMMAND REFERENCE [bold blue]>>[/bold blue]",
        subtitle="[blue dim][ Press Ctrl+C to exit ][/blue dim]"
    ))
    
    if copy:
        pyperclip.copy(result)
        console.print("\n[bold blue]>>[/bold blue] [bold green]Command reference copied to clipboard![/bold green] [bold blue]<<[/bold blue]")

@app.command()
def sync():
    """
    Sync all available sources locally for offline use.
    """
    def count_files_recursive(directory: Path, pattern: str) -> int:
        """Count files recursively in a directory matching the given pattern."""
        count = 0
        if directory.exists():
            for path in directory.rglob(pattern):
                if path.is_file():
                    count += 1
        return count

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(complete_style="green"),
            TextColumn("[yellow]{task.fields[items]}"),
            TextColumn("[cyan]{task.fields[status]}"),
            console=console,
            transient=False,
            refresh_per_second=10
        ) as progress:
            # Track progress
            sources_completed = 0
            all_up_to_date = True
            total_items = 0
            
            # Create tasks for each source
            tldr_task = progress.add_task("TLDR", total=100, items="0 items", status="checking...")
            cheatsh_task = progress.add_task("Cheat.sh", total=100, items="0 items", status="checking...")
            devhints_task = progress.add_task("DevHints", total=100, items="0 items", status="checking...")
            
            # TLDR Pages
            tldr_items = 0
            if tldr_source.is_synced():
                # Count items in TLDR cache
                tldr_cache_dir = Path.home() / ".pydevcheat" / "tldr-pages" / "pages"
                if tldr_cache_dir.exists():
                    for platform in ["common", "linux", "windows", "osx"]:
                        platform_dir = tldr_cache_dir / platform
                        if platform_dir.exists():
                            tldr_items += len(list(platform_dir.glob("*.md")))
                
                progress.update(tldr_task, completed=100, items=f"{tldr_items} items", status="already up to date")
                sources_completed += 1
                total_items += tldr_items
            else:
                all_up_to_date = False
                try:
                    progress.update(tldr_task, completed=20, items="syncing...", status="")
                    
                    if tldr_source.sync():
                        # Count items after sync
                        tldr_cache_dir = Path.home() / ".pydevcheat" / "tldr-pages" / "pages"
                        if tldr_cache_dir.exists():
                            for platform in ["common", "linux", "windows", "osx"]:
                                platform_dir = tldr_cache_dir / platform
                                if platform_dir.exists():
                                    tldr_items += len(list(platform_dir.glob("*.md")))
                        
                        progress.update(tldr_task, completed=100, items=f"{tldr_items} items", status="synced")
                        sources_completed += 1
                        total_items += tldr_items
                    else:
                        progress.update(tldr_task, completed=100, items="0 items", status="failed")
                except Exception as e:
                    progress.update(tldr_task, completed=100, items="0 items", status=f"error: {str(e)}")
            
            # Cheat.sh Pages
            cheatsh_items = 0
            if cheatsh_source.is_synced():
                # Count items in Cheat.sh cache recursively
                cheatsh_cache_dir = Path.home() / ".pydevcheat" / "cache" / "cheatsh"
                cheatsh_items = count_files_recursive(cheatsh_cache_dir, "*.txt")
                
                progress.update(cheatsh_task, completed=100, items=f"{cheatsh_items} items", status="already up to date")
                sources_completed += 1
                total_items += cheatsh_items
            else:
                all_up_to_date = False
                try:
                    progress.update(cheatsh_task, completed=20, items="syncing...", status="")
                    
                    if cheatsh_source.sync():
                        # Count items after sync recursively
                        cheatsh_cache_dir = Path.home() / ".pydevcheat" / "cache" / "cheatsh"
                        cheatsh_items = count_files_recursive(cheatsh_cache_dir, "*.txt")
                        
                        progress.update(cheatsh_task, completed=100, items=f"{cheatsh_items} items", status="synced")
                        sources_completed += 1
                        total_items += cheatsh_items
                    else:
                        progress.update(cheatsh_task, completed=100, items="0 items", status="failed")
                except Exception as e:
                    progress.update(cheatsh_task, completed=100, items="0 items", status=f"error: {str(e)}")
            
            # DevHints Pages
            devhints_items = 0
            if devhints_source.is_synced():
                # Count items in DevHints cache recursively
                devhints_cache_dir = Path.home() / ".pydevcheat" / "cache" / "devhints"
                devhints_items = count_files_recursive(devhints_cache_dir, "*.md")
                
                progress.update(devhints_task, completed=100, items=f"{devhints_items} items", status="already up to date")
                sources_completed += 1
                total_items += devhints_items
            else:
                all_up_to_date = False
                try:
                    progress.update(devhints_task, completed=20, items="syncing...", status="")
                    
                    if devhints_source.sync():
                        # Count items after sync recursively
                        devhints_cache_dir = Path.home() / ".pydevcheat" / "cache" / "devhints"
                        devhints_items = count_files_recursive(devhints_cache_dir, "*.md")
                        
                        progress.update(devhints_task, completed=100, items=f"{devhints_items} items", status="synced")
                        sources_completed += 1
                        total_items += devhints_items
                    else:
                        progress.update(devhints_task, completed=100, items="0 items", status="failed")
                except Exception as e:
                    progress.update(devhints_task, completed=100, items="0 items", status=f"error: {str(e)}")
            
            # Show final summary
            progress.refresh()
            console.print()
            
            if sources_completed == 3:
                if all_up_to_date:
                    console.print(f"✨ [bold green]All sources are already up to date! ({total_items} items cached)[/bold green]")
                else:
                    console.print(f"🎉 [bold green]All sources synced successfully! ({total_items} items cached)[/bold green]")
            else:
                console.print(f"⚠️ [yellow]Synced {sources_completed} out of 3 sources ({total_items} items cached)[/yellow]")
                
    except Exception as e:
        console.print(f"[red]Error during sync: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def gui():
    """
    Launch the graphical user interface.
    """
    run_gui()

if __name__ == "__main__":
    app() 