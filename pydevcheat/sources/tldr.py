import httpx
from pathlib import Path
import re
from typing import Optional, List, Dict
import subprocess
import shutil
from difflib import get_close_matches
from ..utils import create_retry_decorator, handle_source_error, NetworkError, SourceError

class TLDRSource:
    """A source that fetches cheat sheets from TLDR pages."""
    
    # Create retry decorator for network requests
    retry_request = create_retry_decorator(
        max_attempts=3,
        min_wait=1,
        max_wait=10
    )
    
    def __init__(self):
        """Initialize the TLDRSource."""
        self.base_url = "https://raw.githubusercontent.com/tldr-pages/tldr/master/pages"
        self.local_path = Path.home() / ".pydevcheat" / "tldr-pages"
        self.command_cache = {}
        
        # Create directory if it doesn't exist
        self.local_path.mkdir(parents=True, exist_ok=True)
    
    @retry_request
    def _make_request(self, url: str) -> str:
        """Make a retryable HTTP request."""
        response = httpx.get(url)
        response.raise_for_status()
        return response.text
    
    def ensure_repo(self) -> bool:
        """Ensure the TLDR repository exists and is up to date."""
        try:
            if not (self.local_path / ".git").exists():
                # Clone the repository
                subprocess.run(
                    ["git", "clone", "https://github.com/tldr-pages/tldr.git", "."],
                    cwd=self.local_path,
                    check=True
                )
                return True
            else:
                # Update existing repository
                subprocess.run(["git", "pull"], cwd=self.local_path, check=True)
                return True
        except Exception as e:
            handle_source_error("tldr", e)
            return False
    
    def search(self, query: str) -> str:
        """Search for a command in TLDR pages."""
        try:
            # First try to find an exact match
            result = self._search_exact(query)
            if result:
                return result
                
            # If no exact match, try fuzzy search
            return self._search_fuzzy(query)
        except Exception as e:
            handle_source_error("tldr", e)
            return f"# Error searching TLDR pages: {str(e)}"
    
    def _search_exact(self, query: str) -> Optional[str]:
        """Search for an exact command match."""
        # Try common platforms
        platforms = ["common", "linux", "windows", "osx"]
        
        # Handle multi-word queries
        query_parts = query.split()
        if len(query_parts) > 1:
            # For git commands, try the git-subcommand format
            if query_parts[0] == "git":
                subcommand = query_parts[1]
                git_command = f"git-{subcommand}"
                print(f"Looking for git subcommand: {git_command}")
                for platform in platforms:
                    path = self.local_path / "pages" / platform / f"{git_command}.md"
                    print(f"Checking path: {path}")
                    if path.exists():
                        print(f"Found file at: {path}")
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            print(f"File content:\n{content}")
                            parsed = self._parse_markdown(content)
                            print(f"Parsed content:\n{parsed}")
                            return parsed
                
                # If no specific subcommand found, fall back to general git command
                command = "git"
                for platform in platforms:
                    path = self.local_path / "pages" / platform / f"{command}.md"
                    if path.exists():
                        with open(path, 'r', encoding='utf-8') as f:
                            content = self._parse_markdown(f.read())
                            # Add a note about the specific subcommand
                            return f"# Showing results for '{command}'\n# Use '--source cheatsh' for '{query}'\n\n{content}"
            else:
                # Try the full command first
                for platform in platforms:
                    path = self.local_path / "pages" / platform / f"{query}.md"
                    if path.exists():
                        with open(path, 'r', encoding='utf-8') as f:
                            return self._parse_markdown(f.read())
                
                # Try the first word as a command
                command = query_parts[0]
                for platform in platforms:
                    path = self.local_path / "pages" / platform / f"{command}.md"
                    if path.exists():
                        with open(path, 'r', encoding='utf-8') as f:
                            content = self._parse_markdown(f.read())
                            # Add a note about the specific subcommand
                            return f"# Showing results for '{command}'\n# Use '--source cheatsh' for '{query}'\n\n{content}"
        else:
            # Single word query
            for platform in platforms:
                path = self.local_path / "pages" / platform / f"{query}.md"
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        return self._parse_markdown(f.read())
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
            platform_dir = self.local_path / "pages" / platform
            if platform_dir.exists():
                for file in platform_dir.glob("*.md"):
                    self.command_cache[file.stem] = True
    
    def _parse_markdown(self, content: str) -> str:
        """Parse TLDR markdown into a formatted string."""
        lines = content.split('\n')
        result = []
        current_description = None
        current_example = None
        
        print("Parsing markdown content:")
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            print(f"Processing line: {line}")
            if line.startswith('# '):
                # Add the title
                result.append(line)
                print(f"Added title: {line}")
            elif line.startswith('> '):
                # Description line
                desc = line[2:].strip()
                if desc.startswith('More information:'):
                    continue
                current_description = desc
                print(f"Set description: {desc}")
            elif line.startswith('- '):
                # Example description
                current_example = line[2:].strip()
                # Remove trailing colon if present
                if current_example.endswith(':'):
                    current_example = current_example[:-1].strip()
                print(f"Set example description: {current_example}")
            elif line.startswith('`'):
                # Command line
                cmd = line.strip('`')
                # Clean up command
                cmd = re.sub(r'{{(.*?)}}', r'\1', cmd)
                # Remove any remaining curly braces
                cmd = re.sub(r'[{}]', '', cmd).strip()
                # Remove any remaining spaces
                cmd = ' '.join(cmd.split())
                print(f"Cleaned command: {cmd}")
                
                if current_example:
                    result.append(f"{cmd}  # {current_example}")
                    print(f"Added command with description: {cmd}  # {current_example}")
                    current_example = None
                else:
                    result.append(cmd)
                    print(f"Added command without description: {cmd}")
        
        final_result = '\n'.join(result)
        print(f"Final parsed result:\n{final_result}")
        return final_result
    
    def list_all_commands(self) -> Dict[str, str]:
        """List all available commands from TLDR pages."""
        # Try to ensure we have the repository
        if not (self.local_path / ".git").exists():
            if not self.ensure_repo():
                return {}
            
        # Get all commands from all platforms
        all_commands = {}
        platforms = ["common", "linux", "windows", "osx"]
        
        for platform in platforms:
            platform_dir = self.local_path / "pages" / platform
            if platform_dir.exists():
                for file in platform_dir.glob("*.md"):
                    command = file.stem
                    # Add platform prefix to avoid duplicates
                    if command in all_commands:
                        # If command exists in multiple platforms, add platform info
                        all_commands[command] = f"{all_commands[command]}, {platform}"
                    else:
                        all_commands[command] = platform
                        
        return all_commands
    
    def sync(self) -> bool:
        """Sync TLDR pages locally."""
        return self.ensure_repo()

    def is_synced(self) -> bool:
        """Check if the source is already synced."""
        try:
            # Check if local repository exists
            if not self.local_path.exists():
                return False
                
            # Check if pages directory exists
            pages_dir = self.local_path / "pages"
            if not pages_dir.exists():
                return False
                
            # Check if common platforms are present
            platforms = ["common", "linux", "windows", "osx"]
            for platform in platforms:
                platform_dir = pages_dir / platform
                if not platform_dir.exists():
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error checking sync status: {e}")
            return False

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