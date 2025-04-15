import httpx
from pathlib import Path
import re
from typing import Optional, List
import subprocess
import shutil
from difflib import get_close_matches

class TLDRSource:
    def __init__(self):
        self.base_url = "https://raw.githubusercontent.com/tldr-pages/tldr/master/pages"
        self.local_path = Path.home() / ".pydevcheat" / "tldr-pages"
        self.command_cache = {}
    
    def search(self, query: str) -> str:
        """Search for a command in TLDR pages."""
        # First try to find an exact match
        result = self._search_exact(query)
        if result:
            return result
            
        # If no exact match, try fuzzy search
        return self._search_fuzzy(query)
    
    def _search_exact(self, query: str) -> Optional[str]:
        """Search for an exact command match."""
        # Try common platforms
        platforms = ["common", "linux", "windows", "osx"]
        
        # Handle multi-word queries
        query_parts = query.split()
        if len(query_parts) > 1:
            # For git commands, try the first word
            if query_parts[0] == "git":
                command = "git"
                for platform in platforms:
                    try:
                        url = f"{self.base_url}/{platform}/{command}.md"
                        response = httpx.get(url)
                        if response.status_code == 200:
                            content = self._parse_markdown(response.text)
                            # Add a note about the specific subcommand
                            return f"# Showing results for '{command}'\n# Use '--source cheatsh' for '{query}'\n\n{content}"
                    except httpx.RequestError:
                        continue
            else:
                # Try the full command first
                for platform in platforms:
                    try:
                        url = f"{self.base_url}/{platform}/{query}.md"
                        response = httpx.get(url)
                        if response.status_code == 200:
                            return self._parse_markdown(response.text)
                    except httpx.RequestError:
                        continue
                
                # Try the first word as a command
                command = query_parts[0]
                for platform in platforms:
                    try:
                        url = f"{self.base_url}/{platform}/{command}.md"
                        response = httpx.get(url)
                        if response.status_code == 200:
                            content = self._parse_markdown(response.text)
                            # Add a note about the specific subcommand
                            return f"# Showing results for '{command}'\n# Use '--source cheatsh' for '{query}'\n\n{content}"
                    except httpx.RequestError:
                        continue
        else:
            # Single word query
            for platform in platforms:
                try:
                    url = f"{self.base_url}/{platform}/{query}.md"
                    response = httpx.get(url)
                    if response.status_code == 200:
                        return self._parse_markdown(response.text)
                except httpx.RequestError:
                    continue
        return None
    
    def _search_fuzzy(self, query: str) -> str:
        """Perform a fuzzy search for the command."""
        # Get all available commands
        if not self.command_cache:
            self._build_command_cache()
        
        # Try to find close matches
        query_parts = query.split()
        if len(query_parts) > 1:
            command = query_parts[0]
        else:
            command = query
            
        matches = get_close_matches(command, self.command_cache.keys(), n=3, cutoff=0.6)
        
        if matches:
            result = ["# No exact match found. Did you mean:"]
            for match in matches:
                result.append(f"# - {match}")
            result.append("\n# Try one of these commands or use '--source cheatsh' for more results")
            return "\n".join(result)
            
        return f"# No matches found for '{query}'\n# Try searching with a different term or use '--source cheatsh'"
    
    def _build_command_cache(self):
        """Build a cache of available commands."""
        platforms = ["common", "linux", "windows", "osx"]
        for platform in platforms:
            try:
                url = f"{self.base_url}/{platform}"
                response = httpx.get(url)
                if response.status_code == 200:
                    # Extract command names from the directory listing
                    commands = re.findall(r'href="([^"]+).md"', response.text)
                    for cmd in commands:
                        self.command_cache[cmd] = True
            except httpx.RequestError:
                continue
    
    def _parse_markdown(self, content: str) -> str:
        """Parse TLDR markdown into a formatted string."""
        lines = content.split('\n')
        result = []
        description_lines = []
        command_lines = []
        
        for line in lines:
            if line.startswith('# '):
                # Skip the title line
                continue
            elif line.startswith('> '):
                # Description line
                description_lines.append(f"# {line[2:]}")
            elif line.startswith('- '):
                # Command example
                command_lines.append(line[2:])
            elif line.strip():
                # Additional description
                description_lines.append(f"# {line}")
        
        # Combine the results
        if description_lines:
            result.append("Description:")
            result.extend(description_lines)
            result.append("")
        if command_lines:
            result.append("Commands:")
            result.extend(command_lines)
        
        return '\n'.join(result)
    
    def sync(self):
        """Sync TLDR pages locally."""
        try:
            # Create the directory if it doesn't exist
            self.local_path.mkdir(parents=True, exist_ok=True)
            
            # Check if we already have a git repository
            if (self.local_path / ".git").exists():
                # Update existing repository
                subprocess.run(["git", "pull"], cwd=self.local_path, check=True)
            else:
                # Clone the repository
                subprocess.run(
                    ["git", "clone", "https://github.com/tldr-pages/tldr.git", "."],
                    cwd=self.local_path,
                    check=True
                )
            
            return True
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to sync TLDR pages: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error while syncing TLDR pages: {str(e)}") 