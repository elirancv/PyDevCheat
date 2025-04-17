import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.style import Style
from rich.text import Text
from rich.box import DOUBLE, SQUARE, ROUNDED
from typing import Optional, List, Dict
import json
import os
from pathlib import Path
from pydevcheat.sources import TLDRSource, CheatShSource, DevhintsSource
import pyperclip
from .gui import run_gui
import logging
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
import requests
import signal
from functools import wraps
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pydevcheat.exceptions import SourceError, NetworkError

# Configure logging to suppress all debug messages
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("pydevcheat").setLevel(logging.WARNING)


class PyDevCheat:
    """Main class for the PyDevCheat application."""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the PyDevCheat application.

        Args:
            cache_dir: Optional custom cache directory path
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".pydevcheat" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize sources with custom cache directory
        self.sources = {
            "tldr": TLDRSource(cache_dir=self.cache_dir),  # Use root cache directory for TLDR
            "cheatsh": CheatShSource(cache_dir=self.cache_dir / "cheatsh"),
            "devhints": DevhintsSource(cache_dir=self.cache_dir / "devhints"),
        }

    def cheat(self, query: str, source: str = "tldr", copy_to_clipboard: bool = False) -> str:
        """
        Search for a command or topic in the specified source.

        Args:
            query: The command or topic to search for
            source: The source to search in (tldr, cheatsh, devhints)
            copy_to_clipboard: Whether to copy the result to clipboard

        Returns:
            The search result as a string

        Raises:
            SourceError: If no results are found
            NetworkError: If a network error occurs
        """
        if not query:
            raise ValueError("Query cannot be empty")

        if len(query) > 100:
            raise ValueError("Query is too long (max 100 characters)")

        if source not in self.sources:
            raise ValueError(f"Unknown source: {source}")

        selected_source = self.sources[source]

        try:
            # Search with timeout
            result = with_timeout(lambda: selected_source.search(query), timeout=SEARCH_TIMEOUT)
            if not result:
                raise SourceError(f"No results found for '{query}' in {source}")

            # Handle successful result
            if copy_to_clipboard:
                pyperclip.copy(result)

            return result

        except TimeoutError:
            raise TimeoutError(f"Search timed out for '{query}' in {source}")
        except Exception as e:
            if isinstance(e, (SourceError, NetworkError)):
                raise
            raise NetworkError(f"Error searching '{query}' in {source}: {str(e)}")


app = typer.Typer(
    name="pydevcheat",
    help="Quick access to programming cheat sheets and command snippets",
    add_completion=False,
)
console = Console()

# Cache directory setup
CACHE_DIR = Path.home() / ".pydevcheat" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "cheats.json"
TLDR_CACHE_FILE = CACHE_DIR / "tldr_cache.json"

# Initialize sources
tldr_source = TLDRSource()
cheatsh_source = CheatShSource()
devhints_source = DevhintsSource()

# Constants
SEARCH_TIMEOUT = 5  # seconds


def load_cache():
    """Load cache from file, return empty dict if file doesn't exist or is corrupted."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_cache(cache_data):
    """Save cache to file, silently handle errors."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_data, f)
    except IOError:
        pass  # Silently handle permission errors


def wrap_text(text: str, width: int) -> str:
    """
    Wrap text to specified width without breaking words.
    Handles empty strings, long words, and special characters.
    Returns a string with lines wrapped at the specified width.
    """
    if not text:
        return ""

    # Split by newlines and tabs first
    paragraphs = text.replace("\t", "    ").split("\n")
    lines = []

    for paragraph in paragraphs:
        if not paragraph.strip():
            lines.append("")
            continue

        words = paragraph.split()
        current_line = []
        current_length = 0

        for word in words:
            # If a single word is longer than width, we need to break it
            if len(word) > width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = []
                    current_length = 0
                # Break the long word into chunks
                for i in range(0, len(word), width):
                    lines.append(word[i : i + width])
            else:
                if current_length + len(word) + (1 if current_line else 0) <= width:
                    if current_line:
                        current_length += 1  # space
                    current_line.append(word)
                    current_length += len(word)
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = len(word)

        if current_line:
            lines.append(" ".join(current_line))

    return "\n".join(lines)


def format_error(message: str) -> str:
    """Format error message with rich styling."""
    return f"[red]Error: {message}[/red]"


def with_timeout(func, timeout):
    """Run a function with a timeout using ThreadPoolExecutor."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeoutError:
            raise TimeoutError("Search operation timed out")


@app.command()
def cheat(
    query: str = typer.Argument(..., help="The command or topic to search for"),
    source: str = typer.Option("tldr", help="The source to search (tldr, cheatsh, devhints)"),
    copy: bool = typer.Option(False, help="Copy the result to clipboard"),
) -> None:
    """
    Search for command cheatsheets from various sources.
    """
    try:
        # Input validation
        if not query:
            typer.echo(format_error("Query cannot be empty"))
            raise typer.Exit(code=1)
        if len(query) > 100:  # Reasonable limit for query length
            typer.echo(format_error("Query too long (max 100 characters)"))
            raise typer.Exit(code=1)

        # Source selection
        source_map = {"tldr": tldr_source, "cheatsh": cheatsh_source, "devhints": devhints_source}

        if source not in source_map:
            typer.echo(format_error(f"Unknown source: {source}"))
            raise typer.Exit(code=1)

        selected_source = source_map[source]

        try:
            # Search with timeout
            result = with_timeout(lambda: selected_source.search(query), timeout=SEARCH_TIMEOUT)
            if not result:
                typer.echo(format_error(f"No results found for '{query}' in {source}"))
                raise typer.Exit(code=1)

            # Handle successful result
            if copy:
                pyperclip.copy(result)
                typer.echo(f"Result copied to clipboard from {source}!")
            typer.echo(result)

        except TimeoutError:
            typer.echo(format_error(f"Search timed out for '{query}' in {source}"))
            raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(format_error(f"Error searching '{query}' in {source}: {str(e)}"))
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(format_error(f"Unexpected error: {str(e)}"))
        raise typer.Exit(code=1)


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
            refresh_per_second=10,
        ) as progress:
            # Track progress
            sources_completed = 0
            all_up_to_date = True
            total_items = 0

            # Create tasks for each source
            tldr_task = progress.add_task("TLDR", total=100, items="0 items", status="checking...")
            cheatsh_task = progress.add_task(
                "Cheat.sh", total=100, items="0 items", status="checking..."
            )
            devhints_task = progress.add_task(
                "DevHints", total=100, items="0 items", status="checking..."
            )

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

                progress.update(
                    tldr_task,
                    completed=100,
                    items=f"{tldr_items} items",
                    status="already up to date",
                )
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

                        progress.update(
                            tldr_task, completed=100, items=f"{tldr_items} items", status="synced"
                        )
                        sources_completed += 1
                        total_items += tldr_items
                    else:
                        progress.update(tldr_task, completed=100, items="0 items", status="failed")
                except Exception as e:
                    progress.update(
                        tldr_task, completed=100, items="0 items", status=f"error: {str(e)}"
                    )

            # Cheat.sh Pages
            cheatsh_items = 0
            if cheatsh_source.is_synced():
                # Count items in Cheat.sh cache recursively
                cheatsh_cache_dir = Path.home() / ".pydevcheat" / "cache" / "cheatsh"
                cheatsh_items = count_files_recursive(cheatsh_cache_dir, "*.txt")

                progress.update(
                    cheatsh_task,
                    completed=100,
                    items=f"{cheatsh_items} items",
                    status="already up to date",
                )
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

                        progress.update(
                            cheatsh_task,
                            completed=100,
                            items=f"{cheatsh_items} items",
                            status="synced",
                        )
                        sources_completed += 1
                        total_items += cheatsh_items
                    else:
                        progress.update(
                            cheatsh_task, completed=100, items="0 items", status="failed"
                        )
                except Exception as e:
                    progress.update(
                        cheatsh_task, completed=100, items="0 items", status=f"error: {str(e)}"
                    )

            # DevHints Pages
            devhints_items = 0
            if devhints_source.is_synced():
                # Count items in DevHints cache recursively
                devhints_cache_dir = Path.home() / ".pydevcheat" / "cache" / "devhints"
                devhints_items = count_files_recursive(devhints_cache_dir, "*.md")

                progress.update(
                    devhints_task,
                    completed=100,
                    items=f"{devhints_items} items",
                    status="already up to date",
                )
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

                        progress.update(
                            devhints_task,
                            completed=100,
                            items=f"{devhints_items} items",
                            status="synced",
                        )
                        sources_completed += 1
                        total_items += devhints_items
                    else:
                        progress.update(
                            devhints_task, completed=100, items="0 items", status="failed"
                        )
                except Exception as e:
                    progress.update(
                        devhints_task, completed=100, items="0 items", status=f"error: {str(e)}"
                    )

            # Show final summary
            progress.refresh()
            console.print()

            if sources_completed == 3:
                if all_up_to_date:
                    console.print(
                        f"✨ [bold green]All sources are already up to date! ({total_items} items cached)[/bold green]"
                    )
                else:
                    console.print(
                        f"🎉 [bold green]All sources synced successfully! ({total_items} items cached)[/bold green]"
                    )
            else:
                console.print(
                    f"⚠️ [yellow]Synced {sources_completed} out of 3 sources ({total_items} items cached)[/yellow]"
                )

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
